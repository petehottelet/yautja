"""Exercise clean wheel and extracted-skill installs outside the source checkout."""
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile

from .build_skill_bundle import ROOT, project, wheel_path


def run(command, cwd, env):
    command = [str(part) for part in command]
    # Windows CreateProcess does not search the supplied child's PATH. Resolve
    # it explicitly so this checks the selected venv on every operating system.
    command[0] = shutil.which(command[0], path=env.get('PATH')) or command[0]
    result = subprocess.run(command, cwd=cwd, env=env,
                            text=True, encoding='utf-8', capture_output=True)
    if result.returncode:
        raise RuntimeError(f'Command failed: {command}\n{result.stdout}\n{result.stderr}')
    return result.stdout


def environment(path):
    venv.EnvBuilder(with_pip=True).create(path)
    scripts = path / ('Scripts' if os.name == 'nt' else 'bin')
    python = scripts / ('python.exe' if os.name == 'nt' else 'python')
    env = dict(os.environ)
    for key in ('PYTHONPATH', 'PYTHONHOME', 'PIP_EXTRA_INDEX_URL', 'PIP_FIND_LINKS'):
        env.pop(key, None)
    env.update(PATH=str(scripts) + os.pathsep + env.get('PATH', ''),
               PIP_NO_INDEX='1', PIP_NO_CACHE_DIR='1', PIP_CONFIG_FILE=os.devnull,
               PIP_DISABLE_PIP_VERSION_CHECK='1', PYTHONNOUSERSITE='1',
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               HTTP_PROXY='http://127.0.0.1:9', HTTPS_PROXY='http://127.0.0.1:9', ALL_PROXY='http://127.0.0.1:9')
    return python, env


def check_runtime(python, env, cwd, prefix):
    version = 'Yautja ' + project()['version']
    assert run(['yautja', '--version'], cwd, env).strip() == version
    assert run([python, '-m', 'yautja', '--version'], cwd, env).strip() == version
    doctor = json.loads(run(['yautja', '--doctor'], cwd, env))
    assert doctor['ready']
    assert Path(doctor['installation']['package']).resolve().is_relative_to(prefix.resolve())
    assert Path(doctor['installation']['python']).resolve() == python.resolve()
    assert doctor['installation']['cli_matches_environment']
    assert doctor['environment']['system_site_packages'] is False
    run([python, '-m', 'pip', 'check'], cwd, env)
    # These are the Classic conversion commands in SKILL.md, executed verbatim.
    text = (ROOT / 'skills/yautja/SKILL.md').read_text(encoding='utf-8')
    command = next(line.strip() for line in text.splitlines() if line.strip() == 'yautja "input.mov" "output-yautja.mp4"')
    report = json.loads(run(shlex.split(command), cwd, env))
    assert report['frames'] == 6 and report['audio_preserved']
    run(['ffmpeg', '-v', 'error', '-xerror', '-i', 'output-yautja.mp4', '-f', 'null', '-'], cwd, env)
    image_command = 'yautja "photo.jpg" "photo-yautja.png"'
    assert image_command in text
    # Still conversion must not need FFmpeg, even when PATH has only the venv.
    image_env = dict(env, PATH=str(python.parent))
    still = json.loads(run(shlex.split(image_command), cwd, image_env))
    assert still['frames'] == 1 and still['media_type'] == 'image'
    run([python, '-c', "from PIL import Image; im=Image.open('photo-yautja.png'); assert im.size==(320,180); im.verify()"], cwd, env)
    print(f'Passed isolated install and image/video conversion: {prefix.name}')


def main():
    wheel = wheel_path()
    with tempfile.TemporaryDirectory(prefix='yautja-install-') as folder:
        root = Path(folder).resolve()
        bundle = root / 'bundle'
        with zipfile.ZipFile(ROOT / 'dist/yautja-skill.zip') as archive:
            for item in archive.infolist():
                if not (bundle / item.filename).resolve().is_relative_to(bundle):
                    raise ValueError('Unsafe bundle path')
            archive.extractall(bundle)
        skill = bundle / 'yautja'
        embedded, = (skill / 'wheels').glob('*.whl')
        assert embedded.read_bytes() == wheel.read_bytes()
        wheelhouse = skill / 'wheelhouse'
        # Preparation is online. All install/convert commands below are offline.
        subprocess.run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
                        '--dest', str(wheelhouse), str(embedded)], check=True)
        fixture = root / 'fixture'
        fixture.mkdir()
        run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=12:duration=0.5',
             '-f', 'lavfi', '-i', 'sine=frequency=330:duration=0.5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-shortest', 'input.mov'], fixture, os.environ.copy())
        run(['ffmpeg', '-v', 'error', '-i', 'input.mov', '-frames:v', '1', 'photo.jpg'], fixture, os.environ.copy())
        for kind, cwd in (('wheel-venv', root / 'outside'), ('skill-venv', skill)):
            cwd.mkdir(exist_ok=True)
            for name in ('input.mov', 'photo.jpg'):
                shutil.copyfile(fixture / name, cwd / name)
            prefix = root / kind
            python, env = environment(prefix)
            if kind == 'wheel-venv':
                run([python, '-m', 'pip', 'install', '--no-index', '--no-cache-dir',
                     '--find-links', wheelhouse, wheel], cwd, env)
            else:
                reference = (skill / 'references/runtime.md').read_text(encoding='utf-8')
                block = re.search(r'<!-- offline-install:.*?-->\s*```bash\n(.*?)```', reference, re.S).group(1)
                for line in block.strip().splitlines():
                    command = shlex.split(line)
                    if command[0] == 'python':
                        command[0] = str(python)
                    run(command, cwd, env)
            check_runtime(python, env, cwd, prefix)
        # Rebuild from the sdist, whose wheel must contain the same bytes.
        sdist = ROOT / 'dist' / f"{project()['name']}-{project()['version']}.tar.gz"
        source = root / 'source'
        with tarfile.open(sdist) as archive:
            for item in archive.getmembers():
                target = (source / item.name).resolve()
                if not target.is_relative_to(source) or not (item.isfile() or item.isdir()):
                    raise ValueError('Unexpected sdist member')
                if item.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.extractfile(item).read())
        checkout, = source.iterdir()
        env = dict(os.environ)
        env.setdefault('SOURCE_DATE_EPOCH', subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=ROOT, text=True).strip())
        run([sys.executable, '-m', 'build', '--wheel', '--no-isolation', '--outdir', root / 'rebuilt'], checkout, env)
        assert (root / 'rebuilt' / wheel.name).read_bytes() == wheel.read_bytes(), 'sdist wheel differs from source wheel'
        print('Passed sdist rebuild with identical wheel bytes.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
