"""Release archives depend on file content, not checkout timestamps."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools import build_skill_bundle as package_skill


class PackageTests(unittest.TestCase):
    def test_archive_is_stable_across_mtimes_and_changes_with_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'SKILL.md'
            source.write_bytes(b'portable skill\n')
            archive = root / 'skill.zip'
            with patch('sys.stdout', new_callable=io.StringIO):
                entries = {'SKILL.md': source}
                package_skill.write_archive(archive, entries)
                original = archive.read_bytes()
                os.utime(source, (946684800, 946684800))
                package_skill.write_archive(archive, entries)
                self.assertEqual(archive.read_bytes(), original)
                source.write_bytes(b'updated skill\n')
                package_skill.write_archive(archive, entries)
                self.assertNotEqual(archive.read_bytes(), original)

    def test_missing_manifest_file_fails_before_creating_archive(self):
        with tempfile.TemporaryDirectory() as td, patch.object(package_skill, 'ROOT', Path(td)):
            with self.assertRaisesRegex(ValueError, 'missing required file: SKILL.md'):
                package_skill.manifest()

    def test_wrong_wheel_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'matching wheel'):
            package_skill.wheel_path('yautja-0.0.1-py3-none-any.whl')

    def test_replace_updates_known_files_and_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'new.md'
            source.write_text('new skill')
            target = root / 'installed'
            (target / 'scripts').mkdir(parents=True)
            (target / 'scripts/yautja.py').write_text('old runtime')
            (target / 'scripts/custom.py').write_text('keep this')
            (target / 'notes.md').write_text('user notes')
            with self.assertRaisesRegex(ValueError, '--replace'):
                package_skill.install(target, {'SKILL.md': source})
            package_skill.install(target, {'SKILL.md': source}, replace=True)
            self.assertEqual((target / 'SKILL.md').read_text(), 'new skill')
            self.assertFalse((target / 'scripts/yautja.py').exists())
            self.assertEqual((target / 'scripts/custom.py').read_text(), 'keep this')
            self.assertEqual((target / 'notes.md').read_text(), 'user notes')
