"""Offline diagnostics, device failures, and protected-output regressions."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from runtime import MODELS, MODEL_FILES, model_cache_status, select_device, validate_execution
from semantic import GroundedSegmenter
from yautja import main, stop_process


def fake_torch(available=False, cuda_build=None, bf16=False):
    return SimpleNamespace(version=SimpleNamespace(cuda=cuda_build),
                           cuda=SimpleNamespace(is_available=Mock(return_value=available),
                                                is_bf16_supported=Mock(return_value=bf16),
                                                synchronize=Mock()))


class DiagnosticsTests(unittest.TestCase):
    def test_missing_ml_packages_are_nonfatal_only_for_classic_doctor(self):
        missing = {key: {'cached': False} for key in MODELS}
        for mode, expected in [('classic', 0), ('semantic', 1)]:
            with self.subTest(mode=mode), patch('runtime.import_module', side_effect=ImportError('not installed')), \
                    patch('runtime.model_cache_status', return_value=missing), patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(main(['--doctor', '--thermal', mode]), expected)
                result = json.loads(output.getvalue())
                self.assertEqual(result['ready'], mode == 'classic')
                self.assertFalse(result['semantic']['ready'])
                self.assertEqual(result['environment']['executable'], sys.executable)
                self.assertIn('requirements-semantic.txt', ' '.join(result['semantic']['errors']))

    def test_partial_cache_and_empty_weights_are_not_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for key, filenames in MODEL_FILES.items():
                (root / key).mkdir()
                for filename in filenames:
                    (root / key / filename).write_bytes(b'present')
            def cached(repo, filename, revision):
                key = next(k for k, (name, rev) in MODELS.items() if (name, rev) == (repo, revision))
                return str(root / key / filename)
            lookup = Mock(side_effect=cached)
            with patch.dict(sys.modules, {'huggingface_hub': SimpleNamespace(try_to_load_from_cache=lookup)}):
                self.assertTrue(all(m['cached'] for m in model_cache_status().values()))
                (root / 'detector' / 'tokenizer.json').unlink()
                (root / 'segmenter' / 'model.safetensors').write_bytes(b'')
                result = model_cache_status()
                self.assertEqual(result['detector']['missing_files'], ['tokenizer.json'])
                self.assertEqual(result['segmenter']['missing_files'], ['model.safetensors'])
                self.assertFalse(result['detector']['cached'])
                self.assertFalse(result['segmenter']['cached'])
                self.assertTrue(result['pose']['cached'])
                (root / 'pose' / 'preprocessor_config.json').unlink()
                self.assertEqual(model_cache_status()['pose']['missing_files'], ['preprocessor_config.json'])

    def test_auto_explains_cpu_and_explicit_cuda_never_falls_back(self):
        torch = fake_torch()
        device, reason = select_device(torch, 'auto')
        self.assertEqual(device, 'cpu')
        self.assertIn('no CUDA support', reason)
        with self.assertRaisesRegex(ValueError, 'CUDA requested but unavailable'):
            select_device(torch, 'cuda')
        torch.version.cuda = '12.4'
        self.assertIn('driver', select_device(torch, 'auto')[1])
        torch.cuda.is_available.return_value = True
        self.assertEqual(select_device(torch, 'auto')[0], 'cuda')
        self.assertEqual(select_device(torch, 'cpu')[0], 'cpu')

    def test_tensor_execution_failure_is_not_reported_as_cuda_success(self):
        torch = fake_torch(True, '12.4')
        torch.ones = Mock(side_effect=RuntimeError('driver cannot execute kernel'))
        with self.assertRaisesRegex(ValueError, 'tensor check failed on cuda'):
            validate_execution(torch, 'cuda')
        torch.ones.assert_called_once_with((4, 4), device='cuda')

    def test_bfloat16_requires_supported_cuda(self):
        for device in ('cpu', 'cuda'):
            with self.subTest(device=device), self.assertRaisesRegex(ValueError, 'bfloat16 support'):
                validate_execution(fake_torch(), device, 'bf16')

    def test_inference_oom_and_other_runtime_errors_do_not_retry(self):
        for message in ('CUDA out of memory', 'unsupported kernel'):
            model = GroundedSegmenter.__new__(GroundedSegmenter)
            model.device = 'cuda'
            model._detect = Mock(side_effect=RuntimeError(message))
            with self.subTest(message=message), self.assertRaises(ValueError) as error:
                model.detect(None)
            self.assertIn('cuda', str(error.exception))
            if 'memory' in message:
                self.assertIn('--device cpu', str(error.exception))
            else:
                self.assertIn('No automatic CPU retry', str(error.exception))
            model._detect.assert_called_once()
            self.assertEqual(model.device, 'cuda')


class FailureCleanupTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows launcher process-tree behavior')
    def test_windows_launcher_children_release_open_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            resource, ready = root / 'open.log', root / 'ready'
            child = ('import sys,time; from pathlib import Path; '
                     'f=open(sys.argv[1],"wb"); Path(sys.argv[2]).write_text("ready"); time.sleep(60)')
            launcher = 'import subprocess,sys; subprocess.run([sys.executable,"-c",sys.argv[1],*sys.argv[2:]])'
            process = subprocess.Popen([sys.executable, '-c', launcher, child, str(resource), str(ready)])
            try:
                deadline = time.monotonic() + 10
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(ready.exists(), 'child process did not start')
                stop_process(process)
                resource.unlink()  # Fails on Windows if the child still holds it.
                self.assertFalse(resource.exists())
            finally:
                stop_process(process)

    def test_inference_failure_and_cancellation_preserve_existing_output_and_remove_scratch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, destination = root / 'source.mp4', root / 'output.mp4'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=s=160x90:r=4:d=1',
                            '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True)
            for failure, expected in [(RuntimeError('CUDA out of memory'), 1), (KeyboardInterrupt(), 130)]:
                destination.write_bytes(b'existing output must survive')
                model = GroundedSegmenter.__new__(GroundedSegmenter)
                model.device, model.device_reason, model.precision = 'cuda', 'test device', 'fp32'
                model._detect = Mock(side_effect=failure)
                tracker = SimpleNamespace(detector=model, update=lambda frame, time: model.detect(frame))
                with self.subTest(failure=type(failure).__name__), \
                        patch('semantic.GroundedSegmenter', return_value=model), \
                        patch('semantic.SemanticTracker', return_value=tracker), \
                        patch('sys.stderr', new_callable=io.StringIO), patch('sys.stdout', new_callable=io.StringIO):
                    result = main([str(source), str(destination), '--thermal', 'semantic', '--device', 'cuda', '--overwrite'])
                self.assertEqual(result, expected)
                self.assertEqual(destination.read_bytes(), b'existing output must survive')
                self.assertEqual(list(root.glob('.yautja-*')), [])


if __name__ == '__main__':
    unittest.main()
