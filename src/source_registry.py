"""Pinned registry for the ONE Late Egyptian canonical compiler and release.

Checks exact source bytes, not permission to republish without attribution.
The Ramses MaReTE model is an open CC-BY licensed derivative, not the
restricted Ramses bulk manuscript dataset. ORAEC remains unimported.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

REGISTRY=Path(__file__).resolve().parents[1]/"sources/late_egyptian_registry.json"

def read_registry(path:Path=REGISTRY)->dict:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema")!=2 or data.get("language")!="egy" or data.get("stage")!="Late Egyptian":
        raise ValueError("Unsupported Late Egyptian source registry")
    ids=set()
    for entry in data.get("sources",[]):
        if not all(entry.get(f) for f in ("id","sha256","license","url","lineage","identity")):
            raise ValueError("Incomplete source provenance")
        if entry["id"] in ids or not re.fullmatch(r'[0-9a-f]{64}',entry["sha256"]):
            raise ValueError("Duplicate or invalid source fingerprint")
        ids.add(entry["id"])
    if ids!={"TLA-LE19","AED-TEI","AES-LATE-CURATED","RAMSES-WORD-MODEL-2023"}:
        raise ValueError("Unexpected source editions")
    if data.get("policy",{}).get("complete") is not False:
        raise ValueError("Historical coverage is not certified complete")
    return data

def verify_source_files(files:dict[str,Path],registry:dict|None=None)->dict:
    approved={s["id"]:s for s in (registry or read_registry())["sources"]}
    if not files or set(files)-set(approved):
        raise PermissionError("Unregistered Late Egyptian source")
    verified={}
    for source_id,path in files.items():
        file=Path(path)
        if not file.is_file():
            raise FileNotFoundError(file)
        sha=hashlib.sha256()
        with file.open("rb") as stream:
            for part in iter(lambda:stream.read(1<<20),b""):
                sha.update(part)
        actual=sha.hexdigest()
        if actual!=approved[source_id]["sha256"]:
            raise ValueError("Source SHA-256 mismatch: "+source_id)
        verified[source_id]=actual
    return verified
