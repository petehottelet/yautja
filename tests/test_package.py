"""Release archives depend on file content, not checkout timestamps."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import package_skill


class PackageTests(unittest.TestCase):
    def test_archive_is_stable_across_mtimes_and_changes_with_content(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'SKILL.md'
            source.write_bytes(b'portable skill\n')
            archive = root / 'skill.zip'
            with patch.object(package_skill, 'ROOT', root), patch.object(package_skill, 'FILES', ('SKILL.md',)), \
                    patch.object(sys, 'argv', ['package_skill.py', '--zip', str(archive)]), \
                    patch('sys.stdout', new_callable=io.StringIO):
                package_skill.main()
                original = archive.read_bytes()
                os.utime(source, (946684800, 946684800))
                package_skill.main()
                self.assertEqual(archive.read_bytes(), original)
                source.write_bytes(b'updated skill\n')
                package_skill.main()
                self.assertNotEqual(archive.read_bytes(), original)
