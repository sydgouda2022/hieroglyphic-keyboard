"""Fail-closed register for open Late Egyptian build inputs only.

An open-license dataset does not require negotiated permission, but it still
has attribution and potentially ShareAlike obligations. Registry status is NOT
proof that files have been acquired and verified. Neither app contacts sources.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "sources/late_egyptian_registry.json"
APPROVED = ('TLA-LE19', 'AED', 'AES', 'ORAEC')
RIGHTS = {'cc_by_sa_4', 'per_file_cc_by_sa_or_cc0'}
OPEN_LICENSES = {'CC-BY-SA-4.0', 'CC BY-SA 4.0', 'CC0', 'CC0-1.0'}
REQUIRED = ('id', 'family', 'label', 'priority', 'kind', 'role', 'version', 'url',
            'data_url', 'rights', 'availability', 'ingestion', 'publishable',
            'independence_group', 'stage_policy', 'usage', 'runtime_dependency')


def compatible_license(source: dict, license_name: str) -> bool:
    """Published source-level terms must match the selected file's terms."""
    name = license_name.strip().upper() if isinstance(license_name, str) else ''
    if source['rights'] == 'cc_by_sa_4':
        return name in {'CC-BY-SA-4.0', 'CC BY-SA 4.0'}
    if source['rights'] == 'per_file_cc_by_sa_or_cc0':
        return name in OPEN_LICENSES
    return False


def validate_registry(registry: dict) -> dict:
    if (registry.get('schema') != 1 or registry.get('language') != 'egy'
            or registry.get('stage') != 'Late Egyptian'
            or registry.get('open_source_only') is not True):
        raise ValueError('Registry must be a v1 open-only Late Egyptian registry')
    if (registry.get('runtime_external_sources') is not False
            or registry.get('runtime_database') != 'lexicon.sqlite3'):
        raise ValueError('Apps must use only the canonical local lexicon release')
    sources=registry.get('sources')
    if not isinstance(sources,list) or [s.get('id') for s in sources] != list(APPROVED):
        raise ValueError('Registry must contain exactly the approved open source editions')
    priorities=set()
    for source in sources:
        for field in REQUIRED:
            if field not in source or source[field] is None or source[field]=='':
                raise ValueError('Source missing field: '+field)
        if source['priority'] in priorities:
            raise ValueError('Duplicate priority')
        priorities.add(source['priority'])
        if source['usage']!='build_time_only' or source['runtime_dependency'] is not False:
            raise ValueError('External sources must be build-time only')
        if source['rights'] not in RIGHTS:
            raise ValueError('Restricted or unverified license source rejected: '+source['id'])
        if source['id']=='ORAEC' and source['rights']!='per_file_cc_by_sa_or_cc0':
            raise ValueError('ORAEC must preserve per-file license verification')
        if source['id']!='ORAEC' and source['rights']!='cc_by_sa_4':
            raise ValueError('Source expected CC-BY-SA license: '+source['id'])
        if source['publishable'] is not True:
            raise ValueError('Nonpublishable sources do not belong in active registry')
        if source['availability']!='public_data_release':
            raise ValueError('Nonpublic source rejected: '+source['id'])
    if [s['priority'] for s in sources] != sorted(priorities):
        raise ValueError('Source priorities not ordered')
    return {'registered_editions':len(sources),
            'source_families':len({s['family'] for s in sources}),
            'eligible_after_verification':len(sources),
            'permission_required_sources':0}


def read_registry(path:Path=DEFAULT)->dict:
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    validate_registry(data)
    return data


def source_by_id(registry:dict,source_id:str)->dict|None:
    return next((x for x in registry['sources'] if x['id']==source_id),None)


def verified_source_manifest(registry:dict,pinned_files:dict[str,dict])->dict:
    """Require verified local bytes and compatible published open-data license.

    Inputs contain path, version, sha256, license and attribution. No network access.
    """
    validate_registry(registry)
    if not pinned_files:raise ValueError('No acquired source files')
    output=[]
    for source_id,info in pinned_files.items():
        source=source_by_id(registry,source_id)
        if source is None:
            raise PermissionError('Source excluded (not in open-only registry): '+source_id)
        if any(not info.get(k) for k in ('path','version','sha256','license','attribution')):
            raise ValueError('Missing file, pinned hash, version, license or attribution: '+source_id)
        if not re.fullmatch('[0-9a-f]{64}',info['sha256']):
            raise ValueError('Invalid sha256 pin')
        if not compatible_license(source,info['license']):
            raise ValueError('Open source license mismatch for '+source_id)
        path=Path(info['path'])
        if not path.is_file() or not path.stat().st_size:
            raise FileNotFoundError('Missing/empty source file: '+str(path))
        with path.open('rb') as file:
            digest=hashlib.file_digest(file,'sha256').hexdigest()
        if digest!=info['sha256']:
            raise ValueError('Source SHA-256 mismatch: '+source_id)
        output.append(dict(id=source_id,version=info['version'],
             license=info['license'],attribution=info['attribution'],
             url=source['data_url'],sha256=digest,lineage=source['independence_group']))
    return {'schema':1,'sources':output}


def main():
    p=argparse.ArgumentParser(description='Audit open-only Late Egyptian sources')
    p.add_argument('command',choices=['status','validate'])
    p.add_argument('--registry',type=Path,default=DEFAULT)
    args=p.parse_args()
    registry=read_registry(args.registry)
    if args.command=='status':
        for s in registry['sources']:
            print(f"{s['priority']:02d} {s['id']:<10} OPEN_AFTER_PINNING  {s['rights']}")
    print(json.dumps(validate_registry(registry),sort_keys=True))

if __name__=='__main__':main()
