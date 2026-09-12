"""Offline semantic runtime checks. Importing this module needs only the stdlib."""
from __future__ import annotations

from importlib import import_module, metadata
from pathlib import Path
import sys

MODELS = {
    'detector': ('IDEA-Research/grounding-dino-tiny', 'a2bb814dd30d776dcf7e30523b00659f4f141c71'),
    'segmenter': ('facebook/sam2.1-hiera-tiny', 'de431c4043854a71d8101e17995dfe596bf101a5'),
}
# Files used by these exact, unsharded snapshots and their processors. Directory
# presence alone can mean an interrupted download; check every required file.
MODEL_FILES = {
    'detector': ('config.json', 'model.safetensors', 'preprocessor_config.json',
                 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json',
                 'added_tokens.json', 'vocab.txt'),
    'segmenter': ('config.json', 'model.safetensors', 'preprocessor_config.json', 'processor_config.json'),
}
PACKAGES = ('torch', 'torchvision', 'transformers', 'opencv-python-headless',
            'huggingface-hub', 'safetensors', 'numpy', 'Pillow', 'fonttools')


def environment_info():
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    config = Path(sys.prefix) / 'pyvenv.cfg'
    inherited = None
    if config.is_file():
        inherited = any(line.strip().lower() == 'include-system-site-packages = true'
                        for line in config.read_text(encoding='utf-8').splitlines())
    return {'python': sys.version.split()[0], 'executable': sys.executable,
            'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
            'system_site_packages': inherited, 'packages': versions}


def select_device(torch, requested):
    if requested == 'cpu':
        return 'cpu', 'CPU explicitly requested.'
    if torch.cuda.is_available():
        return 'cuda', 'CUDA available in PyTorch.'
    reason = ('This PyTorch build has no CUDA support.' if torch.version.cuda is None
              else 'PyTorch has CUDA support but no CUDA device is available; check the driver and device visibility.')
    if requested == 'cuda':
        raise ValueError('CUDA requested but unavailable. ' + reason +
                         ' Install a compatible CUDA PyTorch/torchvision pair or select --device cpu.')
    return 'cpu', reason


def validate_execution(torch, device, precision='fp32'):
    if precision == 'bf16' and (device != 'cuda' or not torch.cuda.is_bf16_supported()):
        raise ValueError('--precision bf16 requires a CUDA device with bfloat16 support; use --precision fp32.')
    if device == 'cuda':
        try:
            value = torch.ones((4, 4), device=device)
            result = (value @ value).sum().item()
            torch.cuda.synchronize()
            if result != 64:
                raise RuntimeError('CUDA tensor check returned an incorrect result.')
        except RuntimeError as exc:
            raise execution_error(exc, device, 'tensor check') from exc


def execution_error(exc, device, stage):
    if 'out of memory' in str(exc).lower():
        advice = ('Close other GPU applications or rerun with --device cpu.' if device == 'cuda'
                  else 'Close other memory-heavy applications or reduce the requested object categories.')
        return ValueError(f'Semantic {stage} on {device} ran out of memory. {advice} '
                          'Output is committed only after success.')
    return ValueError(f'Semantic {stage} failed on {device}: {exc}. '
                      'Check the PyTorch/torchvision pair and GPU driver with --doctor --thermal semantic. '
                      'No automatic CPU retry was performed.')


def model_cache_status():
    result = {}
    try:
        from huggingface_hub import try_to_load_from_cache
    except (ImportError, OSError) as exc:
        return {key: {'id': name, 'revision': revision, 'cached': False, 'error': str(exc)}
                for key, (name, revision) in MODELS.items()}
    for key, (name, revision) in MODELS.items():
        missing = []
        for filename in MODEL_FILES[key]:
            # This API reads the cache only; no network lookup or download.
            path = try_to_load_from_cache(name, filename, revision=revision)
            if not isinstance(path, str) or not Path(path).is_file() or not Path(path).stat().st_size:
                missing.append(filename)
        result[key] = {'id': name, 'revision': revision, 'cached': not missing, 'missing_files': missing}
    return result


def semantic_diagnostics(requested='auto', precision='fp32'):
    errors, dependencies = [], {}
    torch = None
    for name in ('torch', 'torchvision', 'transformers', 'cv2', 'huggingface_hub', 'safetensors'):
        try:
            module = import_module(name)
            if name == 'torch':
                torch = module
            if name == 'transformers':
                for symbol in ('AutoProcessor', 'AutoModelForZeroShotObjectDetection', 'Sam2Processor', 'Sam2Model'):
                    getattr(module, symbol)
            dependencies[name] = {'importable': True, 'version': getattr(module, '__version__', None)}
        except Exception as exc:
            dependencies[name] = {'importable': False, 'error': str(exc)}
            errors.append(f'{name}: {exc}. Install requirements-semantic.txt in this Python environment.')
    device = {'requested': requested, 'selected': None, 'precision': precision,
              'cuda_available': None, 'cuda_build': None, 'tensor_check': 'not_run'}
    if torch is not None:
        try:
            device['cuda_build'] = torch.version.cuda
            device['cuda_available'] = torch.cuda.is_available()
            selected, reason = select_device(torch, requested)
            device.update(selected=selected, reason=reason)
            if device['cuda_available']:
                props = torch.cuda.get_device_properties(torch.cuda.current_device())
                device.update(gpu_name=props.name, gpu_vram_bytes=props.total_memory)
            if selected == 'cuda':
                device['tensor_check'] = 'failed'
            validate_execution(torch, selected, precision)
            if selected == 'cuda':
                device['tensor_check'] = 'passed'
        except Exception as exc:
            device['error'] = str(exc)
            errors.append(str(exc))
    try:
        models = model_cache_status()
        if not all(item['cached'] for item in models.values()):
            errors.append('Pinned model files are missing. Run --download-models explicitly once with network access.')
    except Exception as exc:
        models = {'error': str(exc)}
        errors.append(f'Cannot inspect the local model cache: {exc}')
    return {'ready': not errors, 'dependencies': dependencies, 'device': device,
            'models': models, 'model_inference': 'not_run', 'errors': errors}
