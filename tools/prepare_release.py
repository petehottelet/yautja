"""Build and validate all release artifacts before any publishing step."""
import argparse
import gzip
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import zipfile

from .build_skill_bundle import ROOT, FILES, manifest, project, wheel_path, write_archive


def normalize_sdist(path, epoch):
    """Fix tar ownership and gzip metadata so retries keep the same PyPI bytes."""
    data = io.BytesIO()
    with tarfile.open(path, 'r:gz') as original, gzip.GzipFile(fileobj=data, mode='wb', filename='', mtime=int(epoch)) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for item in sorted(original.getmembers(), key=lambda item: item.name):
                item.uid = item.gid = 0
                item.uname = item.gname = ''
                item.mtime = int(epoch)
                item.mode = 0o755 if item.isdir() else 0o644
                item.pax_headers = {}
                archive.addfile(item, original.extractfile(item) if item.isfile() else None)
    path.write_bytes(data.getvalue())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', help='When supplied, must match the project version')
    args = parser.parse_args(argv)
    meta = project()
    if args.tag and args.tag != 'v' + meta['version']:
        parser.error('Release tag must match pyproject.toml')
    epoch = os.environ.get('SOURCE_DATE_EPOCH')
    if not epoch:
        epoch = subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=ROOT, text=True).strip()
    env = dict(os.environ, SOURCE_DATE_EPOCH=epoch)
    dist = ROOT / 'dist'
    subprocess.run([sys.executable, '-m', 'build', '--no-isolation', str(ROOT), '--outdir', str(dist)], env=env, check=True)
    wheel = wheel_path()
    sdist = dist / f"{meta['name'].replace('-', '_')}-{meta['version']}.tar.gz"
    normalize_sdist(sdist, epoch)
    with tarfile.open(sdist) as archive:
        members = set(archive.getnames())
        prefix = f"{meta['name']}-{meta['version']}/skills/yautja/"
        missing = [name for name in FILES if prefix + name not in members]
        if missing:
            raise ValueError('Source archive is missing skill resources: ' + ', '.join(missing))
    subprocess.run([sys.executable, '-m', 'twine', 'check', '--strict', str(wheel), str(sdist)], check=True)
    if wheel.stat().st_size >= 1_000_000:
        raise ValueError('Application wheel must be smaller than 1 MB')
    with zipfile.ZipFile(wheel) as archive:
        font = 'yautja/assets/fonts/Michroma-Regular.ttf'
        if font not in archive.namelist() or 'yautja/assets/fonts/Michroma-OFL.txt' not in archive.namelist():
            raise ValueError('Application wheel is missing the bundled analysis font or its license')
        if any(not (name.startswith('yautja/') or name.startswith(f"yautja-{meta['version']}.dist-info/"))
               or (name != font and name.lower().endswith(('.gif', '.mp4', '.ttf', '.otf', '.woff'))) for name in archive.namelist()):
            raise ValueError('Unexpected content in the application wheel')
    entries = manifest(wheel)
    bundle = dist / 'yautja-skill.zip'
    write_archive(bundle, entries)
    with tempfile.TemporaryDirectory(prefix='yautja-repro-') as folder:
        second = Path(folder)
        subprocess.run([sys.executable, '-m', 'build', '--no-isolation', str(ROOT), '--outdir', str(second)], env=env, check=True)
        normalize_sdist(second / sdist.name, epoch)
        if sdist.read_bytes() != (second / sdist.name).read_bytes():
            raise ValueError('Source archive reproducibility check failed')
        if wheel.read_bytes() != (second / wheel.name).read_bytes():
            raise ValueError('Wheel reproducibility check failed')
        write_archive(second / bundle.name, entries)
        if bundle.read_bytes() != (second / bundle.name).read_bytes():
            raise ValueError('Skill bundle reproducibility check failed')
    artifacts = [wheel, sdist, bundle]
    sums = ''.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n' for path in artifacts)
    (dist / 'SHA256SUMS.txt').write_text(sums, encoding='utf-8', newline='\n')
    print('Validated wheel, sdist, and deterministic skill bundle. Publishing has not run.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
