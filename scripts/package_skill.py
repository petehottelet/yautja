#!/usr/bin/env python3
"""Install/archive a fixed manifest; never sweep a worktree or media folder."""
import argparse
import os
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = ('SKILL.md', 'requirements.txt', 'LICENSE', 'VERSION', 'agents/openai.yaml',
         'assets/glyphs.json', 'references/runtime.md', 'scripts/render.py', 'scripts/yautja.py',
         'requirements-semantic.txt', 'references/semantic.md', 'references/dependencies.md',
         'scripts/thermal.py', 'scripts/semantic.py', 'scripts/runtime.py', 'scripts/colors.py',
         'references/colors.md')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, help='Build a portable yautja/ skill archive')
    parser.add_argument('--install', choices=['claude', 'codex', 'both'])
    parser.add_argument('--replace', action='store_true', help='Update only known skill files in existing installations')
    args = parser.parse_args()
    if not args.zip and not args.install:
        parser.error('choose --zip or --install')
    for name in FILES:
        if not (ROOT / name).is_file():
            parser.error(f'missing required file: {name}')
    targets = []
    if args.install in ('claude', 'both'):
        targets.append(Path.home() / '.claude' / 'skills' / 'yautja')
    if args.install in ('codex', 'both'):
        targets.append(Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'skills' / 'yautja')
    for target in targets:
        if target.exists() and not args.replace:
            parser.error(f'{target} exists; use --replace to update the known skill files')
    if args.zip:
        args.zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(args.zip, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in FILES:
                # Stable metadata makes identical source bytes produce identical
                # release checksums across checkouts and operating systems.
                entry = zipfile.ZipInfo('yautja/' + name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, (ROOT / name).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        print(f'Created {args.zip.resolve()} ({len(FILES)} portable files)')
    for target in targets:
        for name in FILES:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
        print(f'Installed {target}')


if __name__ == '__main__':
    main()
