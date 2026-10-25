import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from source_registry import read_registry,verify_source_files

class RegistryTests(unittest.TestCase):
    def test_real_build_pins_and_disclosure(self):
        registry=read_registry()
        self.assertEqual(len(registry["sources"]),4)
        self.assertFalse(registry["policy"]["complete"])
        self.assertIn("RAMSES-WORD-MODEL-2023",{x["id"] for x in registry["sources"]})
        self.assertEqual(len(registry["candidates"]),1)
    def test_pinned_bytes_rejected_on_change(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"corpus";path.write_bytes(b"actual")
            fake={"sources":[{"id":"TLA-LE19","sha256":hashlib.sha256(b"actual").hexdigest()}]}
            self.assertEqual(verify_source_files({"TLA-LE19":path},fake)["TLA-LE19"],fake["sources"][0]["sha256"])
            path.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError,"SHA-256"):verify_source_files({"TLA-LE19":path},fake)
    def test_reject_unknown_source(self):
        with self.assertRaises(PermissionError):verify_source_files({"not-approved":Path("/tmp/anything")})

if __name__=="__main__":unittest.main()
