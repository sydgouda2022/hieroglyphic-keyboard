import tempfile
import unittest
import sys
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from export_api import export_api

class ExportTests(unittest.TestCase):
    def test_api_export_contains_only_library_and_verifiable_release(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'api'
            result=export_api(dest)
            assert result['api_version']=='2.0.0'
            self.assertTrue((dest/'keyboard_api.mjs').is_file())
            self.assertTrue((dest/'keyboard_search.mjs').is_file())
            self.assertTrue((dest/'lexicon/manifest.json').is_file())
            self.assertTrue((dest/'THIRD_PARTY_NOTICES.md').is_file())
            self.assertEqual(json.loads((dest/'package.json').read_text())['type'],'module')
            for forbidden in ('index.html','sw.js','app.mjs','keyboard_ui.mjs','font.ttf','manifest.webmanifest','styles.css'):
                self.assertFalse((dest/forbidden).exists(),forbidden)
            with self.assertRaises(FileExistsError):
                export_api(dest)

if __name__=='__main__':unittest.main()
