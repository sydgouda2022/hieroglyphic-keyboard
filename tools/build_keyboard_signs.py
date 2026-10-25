#!/usr/bin/env python3
"""Generate the Renpet-friendly sign pages from the ONE approved catalog."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"src/keyboard_catalog.js"
TARGET=ROOT/"release/signs.json"
MARK="export const SIGN_CATALOG="

def project(source: str) -> dict:
    if MARK not in source:
        raise ValueError("Catalog export was not found")
    data=json.loads(source.split(MARK,1)[1].strip().rstrip(";"))
    mapping={"uni":"single","bi":"dual","tri":"triple"}
    pages={}
    for page,group in mapping.items():
        seen=set()
        output=[]
        for item in data[group]:
            code,glyph=item["code"],item["glyph"]
            if not code or not glyph or code in seen:
                raise ValueError("Duplicate/invalid sign: "+repr(code))
            seen.add(code)
            output.append([glyph,code])
        if not output:raise ValueError("Empty sign page: "+page)
        pages[page]=output
    return {"schema":1,"source":"src/keyboard_catalog.js","pages":pages}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    rendered=json.dumps(project(SOURCE.read_text(encoding="utf-8")),ensure_ascii=False,separators=(",",":"))+"\n"
    if args.check:
        if TARGET.read_text(encoding="utf-8")!=rendered:
            raise SystemExit("Sign pages are stale. Regenerate from the source catalog.")
    else:
        TARGET.write_text(rendered,encoding="utf-8")

if __name__=="__main__":main()
