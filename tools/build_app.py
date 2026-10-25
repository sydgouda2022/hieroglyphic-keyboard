#!/usr/bin/env python3
"""Build the optional standalone PWA on top of the SAME reusable library."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
from build_library import ROOT,font_bytes,populate

def build(output:Path,font_file:Path|None=None)->dict:
    output=Path(output).resolve()
    if output.exists():raise FileExistsError("Refusing to overwrite existing build: "+str(output))
    if output==ROOT or output in [ROOT/"src",ROOT/"web",ROOT/"release"]:
        raise ValueError("Cannot write build to source directory")
    stage=output.with_name(output.name+".build")
    if stage.exists():raise FileExistsError("Previous build staging directory exists: "+str(stage))
    font=font_bytes(font_file)
    stage.mkdir(parents=True)
    try:
        # One shared library bundle; the demo has no special keyboard implementation.
        result=populate(stage,font)
        for item in (ROOT/"web").iterdir():
            if item.is_file():shutil.copy2(item,stage/item.name)
        # Populate already installed this pinned font and OFL notice.
        checks=("index.html","styles.css","app.mjs","editor-core.mjs",
                "keyboard_api.mjs","keyboard_ui.mjs","keyboard_search.mjs",
                "_generic_search.mjs","keyboard_catalog.js","lexicon_install.mjs",
                "signs.json","lexicon/manifest.json")
        digest=hashlib.sha256()
        for item in checks:
            digest.update(item.encode())
            digest.update((stage/item).read_bytes())
        worker=stage/"sw.js"
        contents=worker.read_text(encoding="utf-8")
        marker="const VERSION='hieroglyphic-keyboard-v1';"
        if contents.count(marker)!=1:raise ValueError("Service worker version marker missing")
        worker.write_text(contents.replace(marker,
            "const VERSION='hieroglyphic-keyboard-"+digest.hexdigest()[:16]+"';"),
            encoding="utf-8")
        stage.rename(output)
    except Exception:
        shutil.rmtree(stage)
        raise
    return {"output":str(output),**result}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=ROOT/"dist")
    parser.add_argument("--font",type=Path,default=None,help="Pinned font file for offline builds")
    args=parser.parse_args()
    print(json.dumps(build(args.out,args.font),indent=2))

if __name__=="__main__":
    main()
