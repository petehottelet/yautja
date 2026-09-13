"""Optional local segmentation and bounded-memory tracking. Adapter code: MIT.

Model weights are separately downloaded Apache-2.0 dependencies, pinned below.
No remote Python code is trusted and no source frames are uploaded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import nullcontext
import math
import time as clock

import numpy as np
from PIL import Image

from thermal import SURFACE_RULES, sensor_size
from runtime import MODELS, select_device, validate_execution, execution_error
DEFAULT_WARM = 'person,bird,cat,dog,horse,sheep,cow,elephant,bear,zebra,giraffe'


@dataclass
class SurfacePart:
    mask: np.ndarray
    label: str
    score: float


@dataclass
class Subject:
    mask: np.ndarray
    label: str
    score: float
    hot: bool = False
    track_id: int = 0
    last_seen: float = 0.
    opacity: float = 1.
    # COCO's 17 joint coordinates and confidence, in mask pixel coordinates.
    keypoints: np.ndarray | None = None
    parts: list[SurfacePart] = field(default_factory=list)


def labels(text):
    return list(dict.fromkeys(part.strip().lower() for part in text.split(',') if part.strip()))


class GroundedSegmenter:
    def __init__(self, *, warm=DEFAULT_WARM, hot='', device='auto', download=False, confidence=.30, precision='fp32', surfaces=False):
        started = clock.perf_counter()
        try:
            import torch
            from transformers import (AutoProcessor, AutoModelForZeroShotObjectDetection, Sam2Processor,
                                      Sam2Model, VitPoseForPoseEstimation)
            import scipy.ndimage  # ViTPose's affine crop and heatmap decoding.
        except (ImportError, OSError, RuntimeError) as exc:
            raise ValueError('Semantic dependencies could not load; install requirements-semantic.txt and check '
                             'the PyTorch/torchvision pair with --doctor --thermal semantic. ' + str(exc)) from exc
        self.torch, self.confidence = torch, confidence
        self.surfaces = surfaces
        self.surface_counts = {}
        self.warm, self.hot = labels(warm), labels(hot)
        self.classes = list(dict.fromkeys(self.warm + self.hot))
        if not self.classes:
            raise ValueError('Specify at least one --warm-objects or --hot-objects class.')
        self.prompt = '. '.join(self.classes) + '.'
        self.device, self.device_reason = select_device(torch, device)
        self.requested_device, self.precision = device, precision
        validate_execution(torch, self.device, precision)
        if self.device == 'cuda':
            torch.cuda.reset_peak_memory_stats()
        if self.device == 'cpu':
            torch.set_num_threads(min(8, torch.get_num_threads()))
        self.download = download
        try:
            name, revision = MODELS['detector']
            options = dict(revision=revision, local_files_only=not download, trust_remote_code=False)
            self.detector_processor = AutoProcessor.from_pretrained(name, **options)
            self.detector = AutoModelForZeroShotObjectDetection.from_pretrained(name, use_safetensors=True, **options).to(self.device).eval()
            name, revision = MODELS['segmenter']
            options['revision'] = revision
            self.mask_processor = Sam2Processor.from_pretrained(name, **options)
            self.segmenter = Sam2Model.from_pretrained(name, use_safetensors=True, **options).to(self.device).eval()
            name, revision = MODELS['pose']
            options['revision'] = revision
            self.pose_processor = AutoProcessor.from_pretrained(name, use_fast=False, **options)
            self.pose_model = VitPoseForPoseEstimation.from_pretrained(
                name, use_safetensors=True, **options).to(self.device).eval()
            if self.device == 'cuda':
                torch.cuda.synchronize()
        except OSError as exc:
            raise ValueError('Unable to load pinned semantic models. Run --download-models once with network access; later conversions use only cached files. ' + str(exc)) from exc
        except RuntimeError as exc:
            raise execution_error(exc, self.device, 'model loading') from exc
        self.model_load_seconds = clock.perf_counter() - started
        self.inference_seconds = 0.
        self.inference_calls = 0
        self.pose_people = 0

    def autocast(self):
        return (self.torch.autocast(device_type='cuda', dtype=self.torch.bfloat16)
                if self.precision == 'bf16' else nullcontext())

    def detect(self, frame):
        started = clock.perf_counter()
        try:
            result = self._detect(frame)
            if self.device == 'cuda':
                self.torch.cuda.synchronize()
        except RuntimeError as exc:
            raise execution_error(exc, self.device, 'inference') from exc
        self.inference_seconds += clock.perf_counter() - started
        self.inference_calls += 1
        return result

    def _detect(self, frame):
        inputs = self.detector_processor(images=frame, text=self.prompt, return_tensors='pt').to(self.device)
        with self.torch.inference_mode(), self.autocast():
            outputs = self.detector(**inputs)
        result = self.detector_processor.post_process_grounded_object_detection(
            outputs, inputs.input_ids, threshold=self.confidence, text_threshold=.25,
            target_sizes=[frame.size[::-1]])[0]
        candidates = []
        # Grounding DINO can repeat a box for synonyms; suppress class-independent
        # near-duplicates before asking SAM to segment them.
        for i in result['scores'].argsort(descending=True).tolist():
            text = result['text_labels'][i].strip().lower()
            matches = [name for name in self.classes if name == text or name in text.split(' . ')]
            if not matches:
                matches = [name for name in self.classes if name in text]
            if not matches:
                continue
            label = max(matches, key=len)
            box = result['boxes'][i].detach().float().cpu().numpy()
            box[[0, 2]] = np.clip(box[[0, 2]], 0, frame.width)
            box[[1, 3]] = np.clip(box[[1, 3]], 0, frame.height)
            if box[2] - box[0] < 2 or box[3] - box[1] < 2:
                continue
            if any(box_iou(box, old[0]) > .75 for old in candidates):
                continue
            candidates.append((box, label, float(result['scores'][i])))
            if len(candidates) == 16:
                break
        if not candidates:
            return []
        inputs = self.mask_processor(images=frame, input_boxes=[[c[0].tolist() for c in candidates]], return_tensors='pt').to(self.device)
        with self.torch.inference_mode(), self.autocast():
            output = self.segmenter(**inputs, multimask_output=False)
        masks = self.mask_processor.post_process_masks(output.pred_masks.cpu(), inputs['original_sizes'].cpu())[0]
        subjects = []
        for mask, (_, label, score) in zip(masks, candidates):
            mask = mask[0].numpy().astype(np.float32)
            if mask.sum() >= 8:
                subjects.append(Subject(mask, label, score, label in self.hot))
        people = [subject for subject in subjects if subject.label == 'person']
        if people:
            # Reuse the detected person masks; no second person detector is needed.
            boxes = []
            for subject in people:
                rows, cols = np.nonzero(subject.mask > .5)
                boxes.append([float(cols.min()), float(rows.min()),
                              float(cols.max() - cols.min() + 1), float(rows.max() - rows.min() + 1)])
            inputs = self.pose_processor(frame, boxes=[boxes], return_tensors='pt').to(self.device)
            with self.torch.inference_mode(), self.autocast():
                pose_output = self.pose_model(**inputs)
            # The processor decodes heatmaps with NumPy, which does not accept bf16.
            pose_output.heatmaps = pose_output.heatmaps.float()
            poses = self.pose_processor.post_process_pose_estimation(pose_output, boxes=[boxes])[0]
            for subject, pose in zip(people, poses):
                joints = np.zeros((17, 3), dtype=np.float32)
                indices = pose['labels'].cpu().numpy()
                joints[indices, :2] = pose['keypoints'].cpu().numpy()
                joints[indices, 2] = pose['scores'].cpu().numpy()
                subject.keypoints = joints
            self.pose_people += len(people)
            if self.surfaces:
                for subject in people:
                    subject.parts = self.detect_surfaces(frame, subject)
        return subjects

    def detect_surfaces(self, frame, subject):
        """Ground visible surfaces inside each person crop with the cached models."""
        rows, cols = np.nonzero(subject.mask > .5)
        pad = max(4, round((rows.max() - rows.min() + 1) * .04))
        x0, y0 = max(0, int(cols.min()) - pad), max(0, int(rows.min()) - pad)
        x1, y1 = min(frame.width, int(cols.max()) + pad + 1), min(frame.height, int(rows.max()) + pad + 1)
        crop = frame.crop((x0, y0, x1, y1))
        prompt = '. '.join(SURFACE_RULES) + '.'
        inputs = self.detector_processor(images=crop, text=prompt, return_tensors='pt').to(self.device)
        with self.torch.inference_mode(), self.autocast():
            output = self.detector(**inputs)
        result = self.detector_processor.post_process_grounded_object_detection(
            output, inputs.input_ids, threshold=max(.30, self.confidence), text_threshold=.25,
            target_sizes=[crop.size[::-1]])[0]
        candidates = []
        for i in result['scores'].argsort(descending=True).tolist():
            text = result['text_labels'][i].lower().split()
            # Ordered rules prefer clothing over an ambiguous clothing/bag label.
            label = next((name for name in SURFACE_RULES if name in text), None)
            if label is None or float(result['scores'][i]) < SURFACE_RULES[label][3]:
                continue
            box = result['boxes'][i].detach().float().cpu().numpy()
            box[[0, 2]] = np.clip(box[[0, 2]], 0, crop.width)
            box[[1, 3]] = np.clip(box[[1, 3]], 0, crop.height)
            if min(box[2:] - box[:2]) < 2:
                continue
            if any(label == old[1] and box_iou(box, old[0]) > .6 for old in candidates):
                continue
            candidates.append((box, label, float(result['scores'][i])))
            if len(candidates) == 12:
                break
        if not candidates:
            return []
        inputs = self.mask_processor(images=crop, input_boxes=[[c[0].tolist() for c in candidates]], return_tensors='pt').to(self.device)
        with self.torch.inference_mode(), self.autocast():
            output = self.segmenter(**inputs, multimask_output=False)
        masks = self.mask_processor.post_process_masks(output.pred_masks.cpu(), inputs['original_sizes'].cpu())[0]
        parts = []
        owner = subject.mask[y0:y1, x0:x1] > .5
        for mask, (box, label, score) in zip(masks, candidates):
            local = mask[0].numpy().astype(bool)
            area = int(local.sum())
            bx0, by0 = np.floor(box[:2]).astype(int)
            bx1, by1 = np.ceil(box[2:]).astype(int)
            # Reject masks that jump to another person or grow far beyond the box.
            if not area or local[by0:by1, bx0:bx1].sum() / area < .6:
                continue
            overlap = local & owner
            if overlap.sum() / area < .65 or overlap.sum() > owner.sum() * SURFACE_RULES[label][2]:
                continue
            if overlap.sum() < 4:
                continue
            full = np.zeros_like(subject.mask)
            full[y0:y1, x0:x1] = overlap
            parts.append(SurfacePart(full, label, score))
            self.surface_counts[label] = self.surface_counts.get(label, 0) + 1
        return parts

    def report(self):
        result = {'device': self.device, 'requested_device': self.requested_device,
                  'device_reason': self.device_reason, 'precision': self.precision,
                  'torch_version': self.torch.__version__, 'cuda_build': self.torch.version.cuda,
                  'model_load_seconds': round(self.model_load_seconds, 3),
                  'inference_seconds': round(self.inference_seconds, 3), 'inference_calls': self.inference_calls,
                  'pose_people': self.pose_people, 'surface_regions': self.surface_counts}
        if self.device == 'cuda':
            result.update(gpu_name=self.torch.cuda.get_device_name(),
                          peak_vram_allocated_bytes=self.torch.cuda.max_memory_allocated(),
                          peak_vram_reserved_bytes=self.torch.cuda.max_memory_reserved())
        return result


def box_iou(a, b):
    lo, hi = np.maximum(a[:2], b[:2]), np.minimum(a[2:], b[2:])
    intersection = np.maximum(hi - lo, 0).prod()
    union = np.maximum(a[2:] - a[:2], 0).prod() + np.maximum(b[2:] - b[:2], 0).prod() - intersection
    return float(intersection / max(1., union))


def mask_iou(a, b):
    a, b = a > .5, b > .5
    return float(np.count_nonzero(a & b) / max(1, np.count_nonzero(a | b)))


class SemanticTracker:
    """Detect periodically, advect masks each frame, and reset at cuts.

    This is optical-flow tracking between SAM image masks, not SAM's video-memory
    predictor. IDs are temporary within a shot, not persistent identities.
    """
    def __init__(self, detector, interval=.5):
        try:
            import cv2
        except ImportError as exc:
            raise ValueError('Semantic tracking requires opencv-python-headless; install requirements-semantic.txt.') from exc
        self.cv2, self.detector, self.interval = cv2, detector, interval
        self.previous = None
        self.tracks = []
        self.last_detection = -math.inf
        self.last_time = -math.inf
        self.next_id = 1
        self.detection_frames = 0
        self.scene_cuts = 0
        self.max_subjects = 0

    def update(self, frame, time):
        cv2 = self.cv2
        frame = frame.resize(sensor_size(*frame.size, 640), Image.Resampling.BILINEAR)
        gray = np.asarray(frame.convert('L'))
        reset = self.previous is None or self.previous.shape != gray.shape or time <= self.last_time
        cut = False
        if not reset:
            # Test a coarse image so grain and fine texture do not trigger resets.
            before = cv2.resize(self.previous, (32, 18)).astype(np.float32)
            after = cv2.resize(gray, (32, 18)).astype(np.float32)
            cut = float(np.mean(np.abs(before - after))) > 38
        if reset or cut:
            self.tracks = []
            self.last_detection = -math.inf
            if cut:
                self.scene_cuts += 1
        elif self.tracks:
            # Backward flow samples the previous mask at each CURRENT pixel.
            flow = cv2.calcOpticalFlowFarneback(gray, self.previous, None, .5, 3, 21, 3, 5, 1.2, 0)
            yy, xx = np.mgrid[:gray.shape[0], :gray.shape[1]].astype(np.float32)
            for track in self.tracks:
                if track.keypoints is not None:
                    points = track.keypoints[:, :2].copy()
                    # Invert backward flow at each previous joint by fixed-point
                    # sampling, so landmarks follow the same motion as the mask.
                    moved = points.copy()
                    for _ in range(3):
                        sampled = cv2.remap(flow, moved[:, 0].reshape(1, -1), moved[:, 1].reshape(1, -1),
                                            cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0]
                        moved = points - sampled
                    valid = ((moved[:, 0] >= 0) & (moved[:, 0] < gray.shape[1]) &
                             (moved[:, 1] >= 0) & (moved[:, 1] < gray.shape[0]))
                    track.keypoints[:, :2] = moved
                    track.keypoints[~valid, 2] = 0
                track.mask = cv2.remap(track.mask, xx + flow[..., 0], yy + flow[..., 1], cv2.INTER_LINEAR,
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                for part in track.parts:
                    part.mask = cv2.remap(part.mask, xx + flow[..., 0], yy + flow[..., 1], cv2.INTER_LINEAR,
                                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if time - self.last_detection >= self.interval - 1e-6:
            detected = self.detector.detect(frame)
            # Global greedy matching prevents an early weak candidate stealing a
            # better match. Each old/new mask participates at most once.
            pairs = sorted(((mask_iou(old.mask, new.mask), i, j)
                            for i, old in enumerate(self.tracks) for j, new in enumerate(detected)
                            if old.label == new.label), reverse=True)
            used_old, used_new = set(), set()
            for overlap, i, j in pairs:
                if overlap < .15 or i in used_old or j in used_new:
                    continue
                old, new = self.tracks[i], detected[j]
                new.track_id = old.track_id
                if new.keypoints is not None and old.keypoints is not None:
                    reliable = (new.keypoints[:, 2] >= .3) & (old.keypoints[:, 2] >= .3)
                    new.keypoints[reliable, :2] = (.8 * new.keypoints[reliable, :2] +
                                                  .2 * old.keypoints[reliable, :2])
                # Blend only aligned masks; no screen-space trails behind motion.
                new.mask = new.mask * .85 + old.mask * .15
                used_parts = set()
                for part in new.parts:
                    matches = [(mask_iou(part.mask, previous.mask), k, previous)
                               for k, previous in enumerate(old.parts)
                               if k not in used_parts and part.label == previous.label]
                    if matches:
                        agreement, k, previous = max(matches, key=lambda item: item[0])
                        if agreement > .25:
                            part.mask = part.mask * .8 + previous.mask * .2
                            used_parts.add(k)
                used_old.add(i)
                used_new.add(j)
            for new in detected:
                if not new.track_id:
                    new.track_id = self.next_id
                    self.next_id += 1
                new.last_seen = time
            stale = [old for i, old in enumerate(self.tracks) if i not in used_old]
            self.tracks = detected + stale
            self.last_detection = time
            self.detection_frames += 1
        # Allow one missed detection, then fade over .5s. Expire old masks so
        # undetected subjects cannot leave permanent hot ghosts in a new scene.
        expiry = self.interval + .5
        self.tracks = [t for t in self.tracks if time - t.last_seen < expiry and np.any(t.mask > .5)]
        for track in self.tracks:
            track.opacity = min(1., max(0., (expiry - (time - track.last_seen)) / .5))
        self.previous, self.last_time = gray, time
        self.max_subjects = max(self.max_subjects, len(self.tracks))
        return self.tracks

    def report(self):
        return {'models': {key: {'id': value[0], 'revision': value[1], 'license': 'Apache-2.0'} for key, value in MODELS.items()},
                'device': self.detector.device, 'detection_frames': self.detection_frames,
                'scene_cuts': self.scene_cuts, 'max_subjects': self.max_subjects,
                'backend': 'optical-flow',
                'heat_model': ('segmented skin, clothing, and gear with pose-guided fallback'
                               if getattr(self.detector, 'surfaces', False) else 'pose-guided surface regions with seeded variation'),
                'runtime': self.detector.report() if hasattr(self.detector, 'report') else {},
                'tracking': 'optical-flow with periodic detection and SAM image masks'}
