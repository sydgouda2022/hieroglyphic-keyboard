"""Publish an immutable Egyptian lexicon/manifest pair atomically.

A SHA-256 manifest provides byte integrity, not a cryptographic signature.
Source license/attribution review remains required for distribution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from hieroglyphic_unicode import native_word
from source_registry import read_registry


def publish(catalog: Path, destination: Path, *, verify_provenance: bool = True) -> dict:
    source=Path(catalog)
    original=source.read_bytes()
    package=json.loads(original)
    if package.get("format")!="mdwnfr-predict-v1":
        raise ValueError("Invalid catalog format")
    metadata=package.get("metadata") or {}
    entries=package.get("entries")
    if not isinstance(entries,list) or not entries or metadata.get("stage")!="Late Egyptian" or (
        metadata.get("spelling_records")!=len(entries) or type(metadata.get("complete")) is not bool
    ):
        raise ValueError("Invalid Late Egyptian release metadata")
    if verify_provenance:
        expected={row['id']:row['sha256'] for row in read_registry()['sources']}
        fields={'TLA-LE19':'tla_sha256','AED-TEI':'aed_sha256',
                'AES-LATE-CURATED':'aes_sha256','RAMSES-WORD-MODEL-2023':'ramses_model_sha256'}
        if metadata.get('tla_sha256')!=expected['TLA-LE19']:
            raise ValueError('Unverified TLA corpus source fingerprint')
        for key,field in fields.items():
            present=metadata.get(field)
            if present is not None and present!=expected[key]:
                raise ValueError('Unregistered corpus source fingerprint: '+key)
    refs=set()
    for item in entries:
        if not isinstance(item,dict):
            raise ValueError("Invalid spelling row")
        reference=item.get("ref")
        if (not isinstance(reference,str) or not reference or reference in refs
                or not native_word(item.get("signs"))
                or not isinstance(item.get("source"),str) or not item["source"]
                or type(item.get("attestations")) is not int or item["attestations"]<0):
            raise ValueError("Invalid native spelling, provenance, or duplicate ref")
        if item["source"]=="RAMSES-WORD-MODEL-2023" and item.get("lexical_identity_verified") is not False:
            raise ValueError("Unlinked model form cannot claim verified lemma identity")
        refs.add(reference)
    digest=hashlib.sha256(original).hexdigest()
    release="late-egyptian-"+("complete-" if metadata["complete"] else "development-")+digest[:16]
    manifest={"format":"egyptian-lexicon-install-v1","language":"egy","stage":"Late Egyptian",
              "release":release,"bytes":len(original),"sha256":digest,
              "spelling_records":len(entries),"complete":metadata["complete"]}
    destination=Path(destination)
    if destination.exists():
        raise FileExistsError("Refusing to replace existing immutable release: "+str(destination))
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix="."+destination.name+".stage-",dir=destination.parent))
    try:
        (stage/"lexicon.json").write_bytes(original)
        (stage/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
        os.replace(stage,destination)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return manifest


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(publish(args.catalog,args.out),sort_keys=True))
