#!/usr/bin/env python3
"""Build a self-contained static PWA. External source data is BUILD-TIME only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
FONT_COMMIT = "2002064e2cfad4af716e345a053ad5c5972e7e3f"
FONT_BLOB_SHA1 = "1a9b2535f87764db260f0bfbf1653f7a8c293449"
FONT_URL = ("https://raw.githubusercontent.com/sydgouda2022/renpet/" +
            FONT_COMMIT + "/web/assets/fonts/NotoSansEgyptianHieroglyphs-Regular.ttf")


def font_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode()
    return hashlib.sha1(header + raw).hexdigest()


def build(output: Path, font_file: Path | None = None) -> dict:
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite build: {output}")
    if output == ROOT or ROOT in output.parents and output.name in {"src", "web", "release"}:
        raise ValueError("Refusing to overwrite source directories")
    font = Path(font_file).read_bytes() if font_file else None
    if font is None:
        request = Request(FONT_URL, headers={"User-Agent": "hieroglyphic-keyboard-builder"})
        with urlopen(request, timeout=45) as response:
            font = response.read(2_000_000)
    if font_blob_sha(font) != FONT_BLOB_SHA1:
        raise ValueError("Egyptian font did not match pinned Git blob SHA-1")
    manifest = json.loads((ROOT / "release/manifest.json").read_text())
    lexicon = (ROOT / "release/lexicon.json").read_bytes()
    if hashlib.sha256(lexicon).hexdigest() != manifest["sha256"] or len(lexicon) != manifest["bytes"]:
        raise ValueError("Canonical lexicon integrity check failed")
    signs = json.loads((ROOT / "release/signs.json").read_text())
    if signs["schema"] != 1 or set(signs["pages"]) != {"uni", "bi", "tri"}:
        raise ValueError("Invalid keyboard signs")
    stage = output.with_name(output.name + ".build")
    if stage.exists():
        raise FileExistsError(f"Unclean previous build: {stage}")
    try:
        shutil.copytree(ROOT / "web", stage)
        for name in ("keyboard_search.mjs", "_generic_search.mjs", "lexicon_install.mjs"):
            shutil.copy2(ROOT / "src" / name, stage / name)
        shutil.copy2(ROOT / "release/signs.json", stage / "signs.json")
        (stage / "lexicon").mkdir()
        for name in ("manifest.json", "lexicon.json", "coverage.json"):
            shutil.copy2(ROOT / "release" / name, stage / "lexicon" / name)
        (stage / "font.ttf").write_bytes(font)
        stage.rename(output)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return {"output": str(output), "spelling_records": manifest["spelling_records"],
            "font_sha1": FONT_BLOB_SHA1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--font", type=Path, help="Existing pinned font file; allows offline build")
    args = parser.parse_args()
    print(json.dumps(build(args.out, args.font), indent=2))


if __name__ == "__main__":
    main()
