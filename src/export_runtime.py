"""Export a small native-script prediction index from the canonical SQLite master.

Renpet and MdwNfr read the same *lexicon release*, not raw research corpora.
A browser may read this JSON index, while Python can query the SQLite master.
Public publishing of a derivative index requires separate source permission review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Literal

OPEN_DATA_LICENSES = {'CC-BY-SA-4.0', 'CC BY-SA 4.0', 'CC0', 'CC0-1.0'}


def make_runtime_pack(db_path: Path, distribution: Literal['local', 'public'] = 'local') -> dict:
    if distribution not in {'local','public'}:
        raise ValueError('distribution must be local or public')
    connection = sqlite3.connect(f'file:{Path(db_path).resolve()}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        if connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Master lexicon failed SQLite integrity check')
        meta = {r['key']:r['value'] for r in connection.execute('SELECT key,value FROM metadata')}
        if meta.get('schema_version') != '1' or meta.get('scope') != 'Late Egyptian':
            raise ValueError('Not a supported Late Egyptian master')
        sources = [dict(x) for x in connection.execute('SELECT * FROM source ORDER BY id')]
        if distribution == 'public':
            restricted = [s['id'] for s in sources if s['rights'].upper() not in OPEN_DATA_LICENSES]
            if restricted:
                raise PermissionError('Public distribution requires source review: '+', '.join(restricted))
        rows=[]
        query = '''
          SELECT s.id, s.surface, s.lemma_id, s.stage, s.morphology_json,
                 (SELECT COUNT(*) FROM evidence e WHERE e.spelling_id=s.id) AS evidence_count,
                 (SELECT COUNT(DISTINCT e.independence_group) FROM evidence e WHERE e.spelling_id=s.id) AS lineage_count,
                 (SELECT e.source_id FROM evidence e WHERE e.spelling_id=s.id ORDER BY e.source_id,e.source_ref LIMIT 1) AS source_id,
                 (SELECT e.source_ref FROM evidence e WHERE e.spelling_id=s.id ORDER BY e.source_id,e.source_ref LIMIT 1) AS source_ref
          FROM spelling s ORDER BY s.surface, s.id
        '''
        for item in connection.execute(query):
            row=dict(item)
            rows.append({'id':row['id'], 'language':'egy', 'surface':row['surface'],
                         'key':row['surface'], 'stage':row['stage'], 'attested':True,
                         'lemmaId':row['lemma_id'], 'sourceId':row['source_id'],
                         'sourceRef':row['source_ref'],
                         'evidenceCount':row['evidence_count'],
                         'independentLineages':row['lineage_count'],
                         'morphology':json.loads(row['morphology_json'])})
        if not rows:
            raise ValueError('Cannot publish empty runtime lexicon')
        # sort by normalized index, preserving stable ids for the shared JS predictor
        rows.sort(key=lambda row: (row['key'],row['id']))
        identity=hashlib.sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
        return {'schema':1,'language':'egy','stage':'Late Egyptian',
                'release':identity[:20], 'distribution':distribution,
                'sourceEditions':len(sources), 'rows':rows}
    finally:
        connection.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',required=True,type=Path)
    p.add_argument('--out',required=True,type=Path)
    p.add_argument('--distribution',choices=['local','public'],default='local')
    args=p.parse_args()
    result=make_runtime_pack(args.db,args.distribution)
    out=args.out
    if out.exists():
        raise FileExistsError('Refusing to overwrite runtime release: '+str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps({'release':result['release'],'entries':len(result['rows']),
                      'distribution':result['distribution']}))

if __name__=='__main__':main()
