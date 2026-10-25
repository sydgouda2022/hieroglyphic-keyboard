"""Build same manifest for Renpet and MdwNfr from approved publisher catalog.

Until complete corpus import, uses the explicitly incomplete verified development data.
Does not promote a development release to 'complete'. Safe for deterministic CI.
"""
import argparse
import hashlib
import json
from pathlib import Path


def publish(catalog: Path, destination: Path):
    original=Path(catalog).read_bytes()
    package=json.loads(original)
    if package.get('format')!='mdwnfr-predict-v1':raise ValueError('Invalid catalog format')
    meta=package.get('metadata') or {}
    entries=package.get('entries') or []
    if not entries or meta.get('spelling_records')!=len(entries) or type(meta.get('complete')) is not bool:
        raise ValueError('Invalid catalog release counts')
    refs=set()
    for e in entries:
        ref=e.get('ref')
        if not isinstance(ref,str) or not ref or ref in refs or not isinstance(e.get('signs'),str) or not any(0x13000<=ord(c)<=0x1342f for c in e['signs']):
            raise ValueError('Invalid written form or duplicate ref')
        refs.add(ref)
    digest=hashlib.sha256(original).hexdigest()
    release='late-egyptian-'+('complete-' if meta['complete'] else 'development-')+digest[:16]
    manifest={'format':'egyptian-lexicon-install-v1','language':'egy','stage':'Late Egyptian',
              'release':release,'bytes':len(original),'sha256':digest,
              'spelling_records':len(entries),'complete':meta['complete']}
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'lexicon.json').write_bytes(original)
    (destination/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(publish(a.catalog,a.out),sort_keys=True))