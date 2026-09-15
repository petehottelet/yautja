import shutil
import unittest
from tools.check_docs import check, option_entries, anchors
from tools.verify_readme import verify


class DocumentationTests(unittest.TestCase):
    def test_reference_media_and_links_match_source(self):
        self.assertEqual(check()['errors'],[])

    def test_anchor_and_duplicate_entry_validation(self):
        self.assertEqual(anchors('# One\n# One\n```bash\n# not a heading\n```\n<a id="old"></a>'),{'one','one-1','old'})
        with self.assertRaises(ValueError): option_entries('#### one\n\n#### one\n')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Video fixture needs FFmpeg')
    def test_copyable_classic_journey(self):
        result=verify(fast=True)
        self.assertIn('reuse',result['passed'])
        self.assertIn('catalog-target',result['passed'])
        self.assertIn('wave_display',result['exercised_families'])
