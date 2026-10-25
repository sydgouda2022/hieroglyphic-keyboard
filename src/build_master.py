"""Build one canonical *local* Late Egyptian lexicon from normalized attestations.

Source editions are BUILD INPUTS ONLY. The runtime schema stores lexical data,
spelling text, compact evidence identifiers and source lineage; it never bundles
source PDFs, unprocessed corpora or a corpus API client.

Dedupe deliberately only uses explicitly reviewed canonicalLemmaId links.
A shared Unicode spelling is not enough to establish identical lexical meaning.
Private build ≠ permission to publish: rights review happens at distribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import unicodedata
from pathlib import Path

SCHEMA_VERSION = 1
EXPECTED_LANGUAGE = 'egy'
EXPECTED_STAGE = 'Late Egyptian'


def _hash(*parts: str) -> str:
    value = json.dumps(parts, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(value).hexdigest()[:24]


def _require_native(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Missing native-script spelling')
    value = unicodedata.normalize('NFC', text)
    if not any(0x13000 <= ord(c) <= 0x1342F for c in value):
        raise ValueError('Spelling has no Unicode Egyptian sign')
    return value


def _schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
        PRAGMA foreign_keys=ON;
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE source (
          id TEXT PRIMARY KEY, edition TEXT NOT NULL, independence_group TEXT NOT NULL,
          rights TEXT NOT NULL, sha256 TEXT NOT NULL
        );
        CREATE TABLE lemma (
          id TEXT PRIMARY KEY, stage TEXT NOT NULL, headword TEXT NOT NULL,
          gloss TEXT, part_of_speech TEXT
        );
        CREATE TABLE spelling (
          id TEXT PRIMARY KEY, lemma_id TEXT NOT NULL REFERENCES lemma(id),
          surface TEXT NOT NULL, stage TEXT NOT NULL,
          morphology_json TEXT NOT NULL,
          UNIQUE(lemma_id,surface,stage,morphology_json)
        );
        CREATE TABLE evidence (
          id TEXT PRIMARY KEY,
          spelling_id TEXT NOT NULL REFERENCES spelling(id),
          source_id TEXT NOT NULL REFERENCES source(id),
          source_ref TEXT NOT NULL, original_record_id TEXT NOT NULL,
          independence_group TEXT NOT NULL, attestation_key TEXT,
          UNIQUE(spelling_id,source_id,source_ref,original_record_id)
        );
        CREATE INDEX idx_spelling_surface ON spelling(surface);
        CREATE INDEX idx_evidence_spelling ON evidence(spelling_id);
        CREATE INDEX idx_evidence_source ON evidence(source_id);
    ''')


def _validated_sources(manifest: dict, *, allow_test_sources: bool = False) -> dict:
    if manifest.get('schema') != 1 or not isinstance(manifest.get('sources'), list):
        raise ValueError('Invalid source manifest')
    sources = {}
    for s in manifest['sources']:
        if any(not isinstance(s.get(k), str) or not s[k] for k in ('id', 'version', 'license', 'sha256')):
            raise ValueError('Missing pinned source metadata')
        if len(s['sha256']) != 64 or any(x not in '0123456789abcdef' for x in s['sha256']):
            raise ValueError('Invalid pinned source SHA-256')
        if s['id'] in sources:
            raise ValueError('Duplicate source edition')
        sources[s['id']] = s
    if not allow_test_sources:
        from source_registry import read_registry, source_by_id, compatible_license
        active = read_registry()
        for source_id, record in sources.items():
            approved = source_by_id(active, source_id)
            if approved is None:
                raise PermissionError('Excluded source cannot enter canonical lexicon: ' + source_id)
            if not compatible_license(approved, record['license']):
                raise PermissionError('Open-data license mismatch for: ' + source_id)
            if not record.get('attribution') or not record.get('url'):
                raise ValueError('Production source manifest needs attribution and publication URL')
    return sources


def _canonical_lemma(row: dict) -> str:
    key = row.get('canonicalLemmaId')
    if key:
        if not isinstance(key, str):
            raise ValueError('canonicalLemmaId must be a reviewed text identifier')
        return key
    # Never infer cross-source semantic equivalence from a spelling.
    local = row.get('lemmaId') or row['id']
    return 'isolated:' + row['sourceId'] + ':' + str(local)


def build_master(records: list[dict], manifest: dict, output: Path, *, allow_test_sources: bool = False) -> dict:
    sources = _validated_sources(manifest, allow_test_sources=allow_test_sources)
    if not records:
        raise ValueError('No normalized records')
    output = Path(output)
    if output.exists():
        raise FileExistsError('Refusing to overwrite existing lexicon: ' + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + '.build')
    if temp.exists():
        raise FileExistsError('Unclean earlier build: ' + str(temp))
    conn = sqlite3.connect(temp)
    try:
        _schema(conn)
        conn.execute('INSERT INTO metadata VALUES (?,?)',('schema_version',str(SCHEMA_VERSION)))
        conn.execute('INSERT INTO metadata VALUES (?,?)',('scope',EXPECTED_STAGE))
        conn.execute('INSERT INTO metadata VALUES (?,?)',('build_input_mode','build_time_only'))
        for sid,s in sorted(sources.items()):
            conn.execute('INSERT INTO source VALUES (?,?,?,?,?)',(
                sid, s['version'], s.get('lineage') or sid, s['license'], s['sha256']))
        # Sorting makes the build deterministic independent of input arrival order.
        for row in sorted(records, key=lambda r:(str(r.get('sourceId','')),str(r.get('id','')),str(r.get('sourceRef','')))):
            for k in ('id','sourceId','sourceRef'):
                if not isinstance(row.get(k),str) or not row[k]:
                    raise ValueError('Missing normalized '+k)
            if row['sourceId'] not in sources:
                raise ValueError('Unregistered source '+row['sourceId'])
            if row.get('attested') is not True:
                raise ValueError('Unattested guess cannot be stored as attestation')
            if row.get('language') != EXPECTED_LANGUAGE or row.get('stage') != EXPECTED_STAGE:
                raise ValueError('Master must contain explicitly identified Late Egyptian only')
            surface = _require_native(row.get('surface'))
            lemma_id = _canonical_lemma(row)
            headword = str(row.get('headword') or surface)
            morphology = row.get('morphology') or {}
            if not isinstance(morphology, dict):
                raise ValueError('Morphology must be an object')
            morphology_json = json.dumps(morphology,sort_keys=True,ensure_ascii=False,separators=(',',':'))
            sid = _hash(lemma_id, surface, EXPECTED_STAGE, morphology_json)
            conn.execute('INSERT OR IGNORE INTO lemma VALUES (?,?,?,?,?)',(
                lemma_id, EXPECTED_STAGE, headword, row.get('gloss'), row.get('partOfSpeech')))
            # Same form + same reviewed lemma + same morphology is one spelling,
            # even if cited in several dictionaries.
            conn.execute('INSERT OR IGNORE INTO spelling VALUES (?,?,?,?,?)',(
                sid, lemma_id, surface, EXPECTED_STAGE, morphology_json))
            lineage = sources[row['sourceId']].get('lineage') or row['sourceId']
            attkey = str(row['attestationKey']) if row.get('attestationKey') is not None else None
            eid = _hash(sid,row['sourceId'],row['sourceRef'],row['id'])
            conn.execute('INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?)',(
                eid, sid, row['sourceId'], row['sourceRef'], row['id'], lineage, attkey))
        for k,sql in (
            ('lemma_count','SELECT COUNT(*) FROM lemma'),
            ('spelling_count','SELECT COUNT(*) FROM spelling'),
            ('evidence_count','SELECT COUNT(*) FROM evidence')):
            conn.execute('INSERT INTO metadata VALUES (?,?)',(k,str(conn.execute(sql).fetchone()[0])))
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        if integrity != 'ok':
            raise ValueError('SQLite integrity check failed: '+str(integrity))
        summary = dict(lemmas=conn.execute('SELECT COUNT(*) FROM lemma').fetchone()[0],
                       spellings=conn.execute('SELECT COUNT(*) FROM spelling').fetchone()[0],
                       evidence=conn.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
                       source_editions=conn.execute('SELECT COUNT(*) FROM source').fetchone()[0],
                       build_input_mode='build_time_only')
        conn.commit()
        conn.close()
        temp.replace(output)
        return summary
    except Exception:
        conn.close()
        if temp.exists(): temp.unlink()
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--records',type=Path,required=True,help='Normalized attested Late Egyptian JSONL')
    p.add_argument('--manifest',type=Path,required=True,help='Verified source edition manifest')
    p.add_argument('--out',type=Path,required=True,help='Canonical lexicon.sqlite3 output')
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    records=[json.loads(l) for l in args.records.read_text(encoding='utf-8').splitlines() if l.strip()]
    print(json.dumps(build_master(records,manifest,args.out),sort_keys=True))


if __name__ == '__main__': main()
