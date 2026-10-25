#!/usr/bin/env python3
"""Export versioned, headless browser API assets; no app, HTML, font or PWA."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

ROOT=Path(__file__).resolve().parents[1]
API_VERSION=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version']
MODULES=('keyboard_api.mjs','keyboard_search.mjs','keyboard_catalog.js','lexicon_install.mjs')
DATA=('manifest.json','lexicon.json','coverage.json')

def export_api(destination:Path)->dict:
    target=Path(destination).resolve()
    if target.exists():raise FileExistsError('Refuse to overwrite API release: '+str(target))
    if target==ROOT or target in (ROOT/'src',ROOT/'release'):
        raise ValueError('Cannot overwrite repository source')
    manifest=json.loads((ROOT/'release/manifest.json').read_text(encoding='utf-8'))
    payload=(ROOT/'release/lexicon.json').read_bytes()
    if manifest.get('format')!='egyptian-lexicon-install-v1' or (
      len(payload)!=manifest.get('bytes') or
      hashlib.sha256(payload).hexdigest()!=manifest.get('sha256')
    ):
        raise ValueError('Release manifest does not match native lexicon payload')
    target.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+target.name+'.stage-',dir=target.parent))
    try:
        for name in MODULES:shutil.copy2(ROOT/'src'/name,stage/name)
        (stage/'lexicon').mkdir()
        for name in DATA:shutil.copy2(ROOT/'release'/name,stage/'lexicon'/name)
        shutil.copy2(ROOT/'docs/THIRD_PARTY_NOTICES.md',stage/'THIRD_PARTY_NOTICES.md')
        (stage/'package.json').write_text(
          json.dumps({'type':'module','version':API_VERSION},sort_keys=True)+'\n',encoding='utf-8')
        os.replace(stage,target)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return {'output':str(target),'api_version':API_VERSION,
            'lexicon_records':manifest['spelling_records'],'lexicon_sha256':manifest['sha256']}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'dist-api')
    args=parser.parse_args()
    print(json.dumps(export_api(args.out),indent=2))

if __name__=='__main__':main()
