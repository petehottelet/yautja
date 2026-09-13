"""Build a small, deterministic skill bundle containing the already-built wheel."""
import argparse
from email.parser import BytesParser
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 developer environment
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
FILES = ('SKILL.md', 'LICENSE', 'agents/openai.yaml', 'references/runtime.md',
         'references/semantic.md', 'references/dependencies.md', 'references/colors.md', 'references/targets.md')
# --replace migrates only the old distribution's known files, never whole folders.
LEGACY_FILES = ('requirements.txt', 'requirements-semantic.txt', 'VERSION',
                'assets/glyphs.json', 'scripts/yautja.py', 'scripts/render.py',
                'scripts/thermal.py', 'scripts/semantic.py', 'scripts/runtime.py', 'scripts/colors.py')


def project():
    return tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']


def wheel_path(path=None):
    meta = project()
    filename = f"{meta['name'].replace('-', '_')}-{meta['version']}-py3-none-any.whl"
    wheel = Path(path) if path else ROOT / 'dist' / filename
    if wheel.name != filename or not wheel.is_file():
        raise ValueError(f'Build the matching wheel first: {filename}; select it with --wheel.')
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        info = [name for name in names if name.endswith('.dist-info/METADATA')]
        if len(info) != 1 or 'yautja/assets/glyphs.json' not in names:
            raise ValueError('Wheel must contain package metadata and glyph resources.')
        metadata = BytesParser().parsebytes(archive.read(info[0]))
        if metadata['Name'] != meta['name'] or metadata['Version'] != meta['version']:
            raise ValueError('Wheel metadata does not match pyproject.toml.')
        if archive.testzip() is not None:
            raise ValueError('Wheel failed its integrity check.')
    return wheel


def manifest(wheel=None):
    result = {name: ROOT / 'skills' / 'yautja' / name for name in FILES}
    for name, path in result.items():
        if not path.is_file():
            raise ValueError(f'missing required file: {name}')
    if result['LICENSE'].read_bytes() != (ROOT / 'LICENSE').read_bytes():
        raise ValueError('The skill LICENSE must match the project LICENSE.')
    selected = wheel_path(wheel)
    result['wheels/' + selected.name] = selected
    return result


def write_archive(destination, entries):
    destination = Path(destination)
    if destination.resolve() in {p.resolve() for p in entries.values()}:
        raise ValueError('Archive cannot replace one of its source files.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.yautja-bundle-', dir=destination.parent) as folder:
        temporary = Path(folder) / 'skill.zip'
        with zipfile.ZipFile(temporary, 'w') as archive:
            for name, path in entries.items():
                entry = zipfile.ZipInfo('yautja/' + name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        os.replace(temporary, destination)


def install(target, entries, replace=False):
    target = Path(target)
    if target.exists() and not replace:
        raise ValueError(f'{target} exists; use --replace to update known skill files')
    stale = list(LEGACY_FILES)
    stale += [str(p.relative_to(target)) for p in (target / 'wheels').glob('yautja-*-py3-none-any.whl')
              if 'wheels/' + p.name not in entries]
    # Validate every destination before making changes, including old files.
    for name in [*entries, *stale]:
        path = target / name
        if not path.resolve().is_relative_to(target.resolve()) or path.is_symlink():
            raise ValueError(f'Refusing a skill path outside the installation: {name}')
        if path.exists() and not path.is_file():
            raise ValueError(f'Expected a file at {path}')
    for name, source in entries.items():
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.resolve() != source.resolve():
            shutil.copy2(source, destination)
    if replace:
        for name in stale:
            (target / name).unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, help='Exact built wheel; defaults to dist/ and the project version')
    parser.add_argument('--zip', type=Path)
    parser.add_argument('--install', choices=['claude', 'codex', 'both'])
    parser.add_argument('--replace', action='store_true', help='Replace known skill files and remove obsolete bundled code/wheels')
    args = parser.parse_args(argv)
    if not args.zip and not args.install:
        parser.error('choose --zip or --install')
    try:
        entries = manifest(args.wheel)
        targets = []
        if args.install in ('claude', 'both'):
            targets.append(Path.home() / '.claude' / 'skills' / 'yautja')
        if args.install in ('codex', 'both'):
            targets.append(Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'skills' / 'yautja')
        if not args.replace and any(target.exists() for target in targets):
            raise ValueError('An installation exists; use --replace to update known skill files')
        if args.zip:
            write_archive(args.zip, entries)
            print(f'Created {args.zip.resolve()} ({len(entries)} files)')
        for target in targets:
            install(target, entries, args.replace)
            print(f'Installed {target}')
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
