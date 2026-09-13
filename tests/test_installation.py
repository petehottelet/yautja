"""Version and environment diagnostics used by agents to select one interpreter."""
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from yautja import __version__
from yautja.runtime import installation_info


class InstallationTests(unittest.TestCase):
    def test_version_entrypoint_and_lightweight_import(self):
        with tempfile.TemporaryDirectory() as td:
            output = subprocess.check_output([sys.executable, '-m', 'yautja', '--version'], cwd=td, text=True)
            self.assertEqual(output.strip(), 'Yautja ' + metadata.version('yautja'))
            self.assertEqual(__version__, metadata.version('yautja'))
            loaded = subprocess.check_output([sys.executable, '-c',
                'import sys,json,yautja,yautja.runtime; print(json.dumps(sorted(sys.modules)))'], cwd=td, text=True)
            self.assertTrue({'torch', 'transformers', 'numpy', 'PIL'}.isdisjoint(json.loads(loaded)))

    def test_missing_cli_path_keeps_exact_python_escape_hatch(self):
        with patch.dict('os.environ', {'PATH': ''}):
            info = installation_info()
        self.assertFalse(info['scripts_on_path'])
        self.assertIsNone(info['cli_on_path'])
        self.assertFalse(info['cli_matches_environment'])
        self.assertEqual(info['module_command'], [sys.executable, '-m', 'yautja'])
        self.assertEqual(info['version'], __version__)

    def test_wrong_cli_on_path_is_detected(self):
        with patch('yautja.runtime.shutil.which', return_value=str(Path(sys.prefix).parent / 'elsewhere/yautja')):
            self.assertFalse(installation_info()['cli_matches_environment'])
