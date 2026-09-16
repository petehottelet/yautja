import shutil
import unittest
from tools.check_docs import check, option_entries, anchors, prose_warnings
from tools.verify_readme import verify


class DocumentationTests(unittest.TestCase):
    def test_reference_media_and_links_match_source(self):
        self.assertEqual(check()['errors'],[])

    def test_anchor_and_duplicate_entry_validation(self):
        self.assertEqual(anchors('# One\n# One\n```bash\n# not a heading\n```\n<a id="old"></a>'),{'one','one-1','old'})
        with self.assertRaises(ValueError): option_entries('#### one\n\n#### one\n')

    def test_prose_warnings_find_history_with_line_numbers(self):
        text = 'The original palette is blue.\n\nBoth new options default off.\nAliases remain supported.\nClassic is a product tier.'
        self.assertEqual([w['line'] for w in prose_warnings(text)], [1, 3, 4, 5])

    def test_prose_warnings_allow_runtime_language_and_skip_code(self):
        text = '''Existing files require overwrite. Still images freeze animation.
LED idle cells remain visible. Code and original glyph artwork are MIT licensed.
```bash
echo "Classic now selects the original palette"
```
~~~~text
Both new options default off.
~~~~
<!-- quick-start-base: Classic now selects -->
Use `Classic` or ``the original palette`` as literal data.
[Reference](https://example.com/Classic) <a id="Classic"></a>
The previous frame supplies the motion trail. A new filename protects the source.
'''
        self.assertEqual(prose_warnings(text), [])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'Video fixture needs FFmpeg')
    def test_copyable_base_journey(self):
        result=verify(fast=True)
        self.assertIn('reuse',result['passed'])
        self.assertIn('catalog-target',result['passed'])
        self.assertIn('wave_display',result['exercised_families'])
