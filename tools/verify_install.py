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


def classic_quickstart():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    block = re.search(r'<!-- quick-start-classic:.*?-->\s*```bash\n(.*?)```', readme, re.S)
    if block is None:
        raise ValueError('README is missing its tested Classic quick-start block')
    commands = [shlex.split(line) for line in block.group(1).strip().splitlines()]
    if len(commands) != 4 or commands[0] != ['pip', 'install', 'yautja']:
        raise ValueError('Classic quick start must install from pip, then check version, doctor, and an image')
    return commands


def check_runtime(python, env, cwd, prefix):
    quickstart = classic_quickstart()
    version = 'Yautja ' + project()['version']
    assert run(quickstart[1], cwd, env).strip() == version
    assert run([python, '-m', 'yautja', '--version'], cwd, env).strip() == version
    doctor = json.loads(run(['yautja', '--doctor'], cwd, env))
    assert doctor['ready']
    assert Path(doctor['installation']['package']).resolve().is_relative_to(prefix.resolve())
    # pip's launcher may use python3.11 while module commands use python.
    # On macOS these can be separate executable copies in the same venv.
    assert Path(doctor['installation']['prefix']).resolve() == prefix.resolve(), doctor['installation']
    assert Path(doctor['installation']['python']).parent.resolve() == python.parent.resolve(), doctor['installation']
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
    assert shlex.split(image_command) == quickstart[3]
    # Still conversion must not need FFmpeg, even when PATH has only the venv.
    image_env = dict(env, PATH=str(python.parent))
    assert json.loads(run(quickstart[2], cwd, image_env))['ready']
    still = json.loads(run(quickstart[3], cwd, image_env))
    assert still['frames'] == 1 and still['media_type'] == 'image'
    run([python, '-c', "from PIL import Image; im=Image.open('photo-yautja.png'); assert im.size==(320,180); im.verify()"], cwd, env)
    effects = json.loads(run(['yautja', 'photo.jpg', 'effects.png', '--palette', 'abyss', '--heat-glow', '.6',
                              '--heat-glow-speed', '0', '--crt-vertical-lines', '--crt-grid', '--crt-crosshatch', '--crt-strength', '.25',
                              '--crt-bleed', '.4', '--no-target-flash', '--wave-style', 'rorschach-hollow',
                              '--wave-width', '.14', '--wave-height', '1', '--thermal-levels', '6',
                              '--thermal-band-softness', '.3', '--target-shape', 'square-mil', '--neon',
                              '--neon-intensity', '.8', '--neon-spread', '.4', '--neon-flicker', '.3',
                              '--neon-elements', 'timecode=0,target=.5', '--HUDglyphs', 'cyber',
                              '--neon-core-whiten', '0'], cwd, image_env))
    assert effects['palette'] == 'abyss' and effects['heat_glow'] == .6 and effects['crt_vertical_lines']
    assert effects['crt_bleed'] == .4 and effects['targets'] == []
    assert effects['crt_grid'] and effects['crt_crosshatch']
    assert effects['hud_colors']['waveform'] == '#267085'
    assert effects['wave_style'] == 'rorschach-hollow' and effects['wave_height'] == 1
    assert effects['thermal_levels'] == 6 and effects['thermal_band_softness'] == .3
    assert effects['target_shape'] == 'square-mil'
    assert effects['neon'] and effects['neon_intensity'] == .8 and effects['neon_spread'] == .4
    assert effects['neon_flicker'] == .3 and effects['neon_intensities']['target-flash'] == .5
    assert effects['hud_glyphs'] == 'cyber' and effects['neon_core_whiten'] == 0
    neon_preset = ROOT / 'skills/yautja/assets/presets/abyss-neon.json'
    run(['yautja', '--preset-file', neon_preset, '--thermal', 'classic', '--save-preset', 'neon.json'], cwd, image_env)
    neon = json.loads(run(['yautja', 'photo.jpg', 'neon.png', '--preset-file', 'neon.json'], cwd, image_env))
    assert neon['neon'] and neon['palette'] == 'abyss' and neon['target_colors'] == ['#267085', '#267085']
    presets = json.loads(run(['yautja', '--list-presets'], cwd, image_env))
    assert any(p['id'] == 'hottropic' and p['name'] == 'HotTropic' for p in presets['presets'])
    run(['yautja', '--stylepreset', 'hottropic', '--thermal', 'classic',
         '--save-preset', 'saved-look.json', '--preset-name', 'Saved HotTropic'], cwd, image_env)
    preset = json.loads(run(['yautja', 'photo.jpg', 'preset.png', '--preset-file', 'saved-look.json'], cwd, image_env))
    assert preset['preset_name'] == 'Saved HotTropic' and preset['preset_kind'] == 'custom'
    assert preset['thermal_levels'] == 12 and preset['hud'] is False
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
                # Run the public install command verbatim against only this
                # release's prepared wheelhouse; network access stays disabled.
                run(classic_quickstart()[0], cwd, dict(env, PIP_FIND_LINKS=str(wheelhouse)))
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
