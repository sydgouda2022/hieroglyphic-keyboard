#!/usr/bin/env python3
"""Build the reusable, self-contained browser library without the demo application.

Copy the resulting folder to any static host under the consuming app's origin.
The font is fetched from a fixed Google Fonts revision, never from Renpet.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
FONT_REVISION="e7db6ca603fd4862010383ff17ffd6cc4ffac1c0"
FONT_BLOB_SHA1="1a9b2535f87764db260f0bfbf1653f7a8c293449"
FONT_URL=("https://raw.githubusercontent.com/google/fonts/"+FONT_REVISION+
 "/ofl/notosansegyptianhieroglyphs/NotoSansEgyptianHieroglyphs-Regular.ttf")
MODULES=("keyboard_api.mjs","keyboard_ui.mjs","keyboard_search.mjs",
 "_generic_search.mjs","keyboard_catalog.js","lexicon_install.mjs")
RELEASE=("manifest.json","lexicon.json","coverage.json")

def font_blob_sha(raw:bytes)->str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()

def font_bytes(path:Path|None=None)->bytes:
    if path is not None:
        data=Path(path).read_bytes()
    else:
        req=Request(FONT_URL,headers={"User-Agent":"HieroglyphicKeyboardBuilder/1.0"})
        with urlopen(req,timeout=45) as response:
            data=response.read(2_000_000)
    if font_blob_sha(data)!=FONT_BLOB_SHA1:
        raise ValueError("Google Noto Egyptian font failed pinned Git SHA-1 validation")
    return data

def populate(destination:Path,font:bytes)->dict:
    """Populate an existing empty directory with portable versioned library assets."""
    dst=Path(destination)
    if any(dst.iterdir()):
        raise FileExistsError("Library asset destination must be empty")
    manifest=json.loads((ROOT/"release/manifest.json").read_text(encoding="utf-8"))
    raw=(ROOT/"release/lexicon.json").read_bytes()
    if len(raw)!=manifest["bytes"] or hashlib.sha256(raw).hexdigest()!=manifest["sha256"]:
        raise ValueError("Canonical lexicon manifest and payload do not match")
    sign_catalog=json.loads((ROOT/"release/signs.json").read_text(encoding="utf-8"))
    if sign_catalog.get("schema")!=1 or set(sign_catalog["pages"])!={"uni","bi","tri"}:
        raise ValueError("Invalid curated sign catalog")
    for name in MODULES:shutil.copy2(ROOT/"src"/name,dst/name)
    shutil.copy2(ROOT/"release/signs.json",dst/"signs.json")
    (dst/"lexicon").mkdir()
    for name in RELEASE:shutil.copy2(ROOT/"release"/name,dst/"lexicon"/name)
    (dst/"package.json").write_text('{"type":"module","version":"1.0.0"}\n',encoding="utf-8")
    (dst/"font.ttf").write_bytes(font)
    shutil.copy2(ROOT/"web/OFL-NotoEgyptian.txt",dst/"OFL-NotoEgyptian.txt")
    (dst/"hiero-font.css").write_text(
        '@font-face{font-family:"Hiero Noto";src:url("./font.ttf") format("truetype");font-display:swap;}\n'
        'hieroglyphic-keyboard{--hiero-font:"Hiero Noto","Noto Sans Egyptian Hieroglyphs",serif;}\n',
        encoding="utf-8")
    return {"spelling_records":manifest["spelling_records"],
            "sha256":manifest["sha256"],"font_git_sha1":FONT_BLOB_SHA1}

def build(output:Path,font_file:Path|None=None)->dict:
    output=Path(output).resolve()
    if output.exists():raise FileExistsError("Refusing to overwrite existing bundle: "+str(output))
    stage=output.with_name(output.name+".build")
    if stage.exists():raise FileExistsError("Previous build staging directory exists: "+str(stage))
    if output==ROOT or output in [ROOT/"src",ROOT/"web",ROOT/"release"]:
        raise ValueError("Cannot write build to source directory")
    font=font_bytes(font_file)
    stage.mkdir(parents=True)
    try:
        result=populate(stage,font)
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage)
        raise
    return {"output":str(output),**result}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=ROOT/"dist-library")
    parser.add_argument("--font",type=Path,default=None,help="Pinned font file for offline builds")
    args=parser.parse_args()
    print(json.dumps(build(args.out,args.font),indent=2))

if __name__=="__main__":
    main()
