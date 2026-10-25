import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from publish_release import publish

class PublisherTests(unittest.TestCase):
    def sample(self):
        return {"format":"mdwnfr-predict-v1",
            "metadata":{"stage":"Late Egyptian","complete":False,"spelling_records":1},
            "entries":[{"ref":"tla:1","signs":"𓄿𓂝","source":"TLA-LE19","attestations":1}]}
    def test_atomic_first_publish_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/"catalog.json";out=root/"dist"
            source.write_text(json.dumps(self.sample(),ensure_ascii=False))
            result=publish(source,out)
            self.assertEqual(result["spelling_records"],1)
            self.assertEqual(json.loads((out/"manifest.json").read_text())["sha256"],result["sha256"])
            with self.assertRaises(FileExistsError):publish(source,out)
    def test_rejects_malformed_native_forms(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/"catalog.json";out=root/"dist"
            catalog=self.sample();catalog["entries"][0]["signs"]="𓄿𓐱"
            source.write_text(json.dumps(catalog,ensure_ascii=False))
            with self.assertRaisesRegex(ValueError,"Invalid native spelling"):
                publish(source,out)
            self.assertFalse(out.exists())

if __name__=="__main__":unittest.main()
