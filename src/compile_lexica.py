"""Independent Late Egyptian lexicon compiler. No other language is compiled."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from hieroglyphic_unicode import native_word, has_format_controls
from source_registry import verify_source_files

TEI='{http://www.tei-c.org/ns/1.0}'
XML='{http://www.w3.org/XML/1998/namespace}'

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def hieroglyphic(s):
    return native_word(s)

def xml_entries(path):
    for _event,el in ET.iterparse(path,events=('end',)):
        if el.tag==TEI+'entry':
            yield el
            el.clear()

def aed_metadata(path):
    results={}
    for e in xml_entries(path):
        label=e.get(XML+'id','')
        if not label.startswith('tla') or not label[3:].isdigit():
            continue
        head=e.find('.//'+TEI+'form/'+TEI+'orth')
        gram=e.find('.//'+TEI+'gramGrp/'+TEI+'term')
        gloss=None
        for cit in e.findall('.//'+TEI+'sense/'+TEI+'cit'):
            if cit.get(XML+'lang')=='en' and cit.get('type')=='translation':
                gloss=' '.join(''.join(cit.itertext()).split());break
        results[label[3:]]={
            'headword': ''.join(head.itertext()).strip() if head is not None else '',
            'pos': ''.join(gram.itertext()).strip() if gram is not None else '',
            'gloss':gloss or '',
            'aed_ref':label,
        }
    return results

def source_rows(path):
    """Each whitespace-delimited Unicode hieroglyph cluster is an attested token.

    Link lemma IDs only if the complete token/lemma alignment is unambiguous.
    Unicode words with unavailable nonstandard glyph notation are excluded,
    rather than pretending a partial sign sequence is complete.
    """
    counts=collections.Counter()
    evidence=collections.defaultdict(list)
    stats=collections.Counter()
    with Path(path).open(encoding='utf-8-sig') as stream:
        for line_number,line in enumerate(stream,1):
            if not line.strip():continue
            stats['sentences']+=1
            row=json.loads(line)
            surface_tokens=(row.get('hieroglyphs') or '').split()
            lemma_tokens=(row.get('lemmatization') or '').split()
            mapped=[]
            for fragment in lemma_tokens:
                m=re.fullmatch(r'(\d+)\|(.+)',fragment)
                if not m:break
                mapped.append(m.group(1))
            aligned=len(mapped)==len(surface_tokens)==len(lemma_tokens)
            if aligned:stats['aligned_sentences']+=1
            for i,spelling in enumerate(surface_tokens):
                if not hieroglyphic(spelling):
                    stats['unencoded_word_tokens']+=1
                    continue
                lemma=(mapped[i] if aligned else 'unresolved')
                key=(lemma,unicodedata.normalize('NFC',spelling))
                counts[key]+=1
                if has_format_controls(spelling):stats['formatted_word_tokens']+=1
                # Bound evidence per spelling so corpus references remain compact.
                if len(evidence[key])<24:evidence[key].append(line_number)
                stats['encoded_word_tokens']+=1
    return counts,evidence,stats

def db_connect(path):
    dest=Path(path)
    if dest.exists():raise FileExistsError('Refuse accidental overwrite: '+str(dest))
    dest.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(str(dest))
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA journal_mode=DELETE')
    db.executescript('''
      CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
      CREATE TABLE lemma(id TEXT PRIMARY KEY,headword TEXT,pos TEXT,gloss TEXT);
      CREATE TABLE spelling(id TEXT PRIMARY KEY,lemma_id TEXT NOT NULL REFERENCES lemma(id),
        native_form TEXT NOT NULL,dialect_mask INTEGER NOT NULL DEFAULT 0,
        frequency INTEGER NOT NULL DEFAULT 0,
        UNIQUE(lemma_id,native_form,dialect_mask));
      CREATE TABLE attestation(id TEXT PRIMARY KEY,spelling_id TEXT NOT NULL REFERENCES spelling(id),
        source TEXT NOT NULL,original_ref TEXT NOT NULL,source_sha256 TEXT NOT NULL);
      CREATE INDEX idx_spelling_native ON spelling(native_form);
      CREATE INDEX idx_attestation_word ON attestation(spelling_id);
    ''')
    return db

def persist_json(path, payload):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')

def _compile_egyptian(tla_path,aed_path,out,aes_path=None,aes_whitelist=None,ramses_path=None,*,verify_pins=True):
    """Produce one stage-filtered SQLite master and identical browser spellings.

    Production builds reject source files whose bytes differ from registry pins.
    Tests can explicitly pass verify_pins=False for synthetic fixture inputs.
    AES never enters by historical date alone. The source file must match its
    pinned SHA-256 and each document ID must have explicit philological approval.
    """
    if verify_pins:
        pins={'TLA-LE19':tla_path}
        if aed_path:pins['AED-TEI']=aed_path
        if aes_path:pins['AES-LATE-CURATED']=aes_path
        if ramses_path:pins['RAMSES-WORD-MODEL-2023']=ramses_path
        verify_source_files(pins)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    counts,evidence,stats=source_rows(tla_path)
    aed=aed_metadata(aed_path) if aed_path else {}
    sha_tla=digest(tla_path)
    sha_aed=digest(aed_path) if aed_path else None
    aes_counts,aes_evidence,aes_stats,sha_aes={},{},{},None
    if bool(aes_path)!=bool(aes_whitelist):
        raise ValueError('AES source and individual text whitelist must be supplied together')
    if aes_path:
        from aes_late_adapter import curated_aes_rows
        aes_counts,aes_evidence,aes_stats,sha_aes=curated_aes_rows(aes_path,aes_whitelist)
    ramses_counts,ramses_refs,ramses_stats={}, {}, {}
    sha_ramses=None
    if ramses_path:
        from ramses_unicode import audit_ramses
        ramses_counts,ramses_refs,ramses_stats=audit_ramses(ramses_path)
        sha_ramses=ramses_stats['source_sha256']
    db=db_connect(out/'lexicon.sqlite3')
    db.execute('INSERT INTO metadata VALUES (?,?)',('language','egy'))
    db.execute('INSERT INTO metadata VALUES (?,?)',('stage','Late Egyptian'))
    db.execute('INSERT INTO metadata VALUES (?,?)',('tla_sha256',sha_tla))
    if sha_aed:db.execute('INSERT INTO metadata VALUES (?,?)',('aed_sha256',sha_aed))
    if sha_aes:db.execute('INSERT INTO metadata VALUES (?,?)',('aes_curated_sha256',sha_aes))
    if sha_ramses:db.execute('INSERT INTO metadata VALUES (?,?)',('ramses_model_sha256',sha_ramses))
    db.execute('''CREATE TABLE IF NOT EXISTS corpus_form (
      native_form TEXT PRIMARY KEY, original_encodings_json TEXT NOT NULL,
      frequency INTEGER NOT NULL, source_sha256 TEXT NOT NULL)''')
    entries=[]
    known={}
    for (lemma,form),frequency in sorted(counts.items()):
        lexical_id=('tla19:'+lemma if lemma!='unresolved' else 'unresolved:'+hashlib.sha256(form.encode()).hexdigest()[:12])
        a=aed.get(lemma,{})
        db.execute('INSERT OR IGNORE INTO lemma VALUES (?,?,?,?)',(lexical_id,a.get('headword',''),a.get('pos',''),a.get('gloss','')))
        record_id='tla19:'+hashlib.sha256((lexical_id+'|'+form).encode()).hexdigest()[:20]
        db.execute('INSERT INTO spelling(id,lemma_id,native_form,frequency) VALUES (?,?,?,?)',
                   (record_id,lexical_id,form,frequency))
        for at in evidence[(lemma,form)]:
            ref='line:'+str(at)
            att_id=hashlib.sha256((record_id+ref).encode()).hexdigest()[:24]
            db.execute('INSERT OR IGNORE INTO attestation VALUES (?,?,?,?,?)',(att_id,record_id,'TLA-LE19',ref,sha_tla))
        known[(lemma,form)]=len(entries)
        entries.append({'ref':record_id,'signs':form,'lemma':lexical_id,
                        'source':'TLA-LE19','primary':True,'attestations':frequency,'lexical_identity_verified':lemma!='unresolved'})
    added=0
    for (lemma,form),frequency in sorted(aes_counts.items()):
        lexical_id='tla19:'+lemma
        a=aed.get(lemma,{})
        db.execute('INSERT OR IGNORE INTO lemma VALUES (?,?,?,?)',(lexical_id,a.get('headword',''),a.get('pos',''),a.get('gloss','')))
        record_id='tla19:'+hashlib.sha256((lexical_id+'|'+form).encode()).hexdigest()[:20]
        key=(lemma,form)
        if key in known:
            existing=entries[known[key]]
            existing['attestations']+=frequency
            existing['source']='TLA-LE19+AES-LATE-CURATED'
            db.execute('UPDATE spelling SET frequency=frequency+? WHERE id=?',(frequency,record_id))
        else:
            db.execute('INSERT INTO spelling(id,lemma_id,native_form,frequency) VALUES (?,?,?,?)',
                       (record_id,lexical_id,form,frequency))
            entries.append({'ref':record_id,'signs':form,'lemma':lexical_id,
                'source':'AES-LATE-CURATED','primary':True,'attestations':frequency})
            known[key]=len(entries)-1
            added+=1
        for reference in aes_evidence[key]:
            eid=hashlib.sha256((record_id+'|AES|'+reference).encode()).hexdigest()[:24]
            db.execute('INSERT OR IGNORE INTO attestation VALUES (?,?,?,?,?)',
                       (eid,record_id,'AES-LATE-CURATED',reference,sha_aes))
    # Ramses model documents word-level SIGN SEQUENCES, but not lemma identities
    # or individual witness IDs. Never attach its evidence to a TLA lemma just
    # because a written surface matches: homography is extremely common.
    old_surfaces={entry['signs'] for entry in entries}
    ramses_new=0
    for form,frequency in sorted(ramses_counts.items()):
        original_mdcs=ramses_refs[form]
        db.execute('INSERT INTO corpus_form VALUES (?,?,?,?)',
                   (form,json.dumps(original_mdcs,ensure_ascii=False,separators=(',',':')),frequency,sha_ramses))
        if form in old_surfaces:continue
        digest_form=hashlib.sha256(form.encode()).hexdigest()[:20]
        lexical_id='ramses-unlinked:'+digest_form
        record_id='ramses:'+digest_form
        db.execute('INSERT INTO lemma VALUES (?,?,?,?)',(lexical_id,'','',''))
        db.execute('INSERT INTO spelling(id,lemma_id,native_form,frequency) VALUES (?,?,?,?)',
                   (record_id,lexical_id,form,frequency))
        for encoding in original_mdcs:
            ref='model:mdc:'+encoding
            eid=hashlib.sha256((record_id+'|'+ref).encode()).hexdigest()[:24]
            db.execute('INSERT OR IGNORE INTO attestation VALUES (?,?,?,?,?)',
                       (eid,record_id,'RAMSES-WORD-MODEL-2023',ref,sha_ramses))
        known[(lexical_id,form)]=len(entries)
        entries.append({'ref':record_id,'signs':form,'lemma':lexical_id,
                        'source':'RAMSES-WORD-MODEL-2023','primary':True,
                        'attestations':frequency,'lexical_identity_verified':False})
        ramses_new+=1
    db.commit()
    if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
        raise ValueError('Canonical SQLite integrity check failed')
    sql_count=db.execute('SELECT COUNT(*) FROM spelling').fetchone()[0]
    if sql_count!=len(entries) or len(entries)!=len(known):
        raise ValueError('Canonical SQLite / JSON spelling count mismatch')
    missing=db.execute('SELECT COUNT(*) FROM spelling s WHERE NOT EXISTS(SELECT 1 FROM attestation a WHERE a.spelling_id=s.id)').fetchone()[0]
    if missing:
        raise ValueError('A native spelling is missing provenance references')
    match_count=db.execute("SELECT COUNT(*) FROM lemma WHERE headword != ''").fetchone()[0]
    distinct_verified_lemmas=len({e['lemma'] for e in entries if not e['lemma'].startswith(('ramses-unlinked:','unresolved:'))})
    native_surfaces=len({e['signs'] for e in entries})
    db.close()
    sources={'TLA-LE19':sha_tla,'AED-TEI':sha_aed}
    if sha_aes:sources['AES-LATE-CURATED']=sha_aes
    if sha_ramses:sources['RAMSES-WORD-MODEL-2023']=sha_ramses
    payload={'format':'mdwnfr-predict-v1',
        'metadata':{'name':'Late Egyptian Attested Unicode Lexicon','complete':False,
                    'stage':'Late Egyptian', 'lexemes':distinct_verified_lemmas,
                    'spelling_records':len(entries),
                    'source_corpus':'TLA Late Egyptian v19; AED crosswalk'+('; individually approved AES Late Egyptian manuscripts' if sha_aes else '')+('; Ramses 2023 word model with unidentified lemmata' if sha_ramses else ''),
                    'tla_sha256':sha_tla,'aed_sha256':sha_aed,'aes_sha256':sha_aes,
                    'aes_additional_spelling_records':added,
                    'ramses_unlinked_spelling_records':ramses_new,
                    'ramses_model_sha256':sha_ramses,
                    'unique_native_surfaces':native_surfaces,
                    'aed_matched_lemmas':match_count,
                    'evidence_status':'source-filtered-not-exhaustive'},'entries':entries}
    persist_json(out/'lexicon.json',payload)
    report={'language':'egy','stage':'Late Egyptian','unique_spellings':len(entries),
            'distinct_lemmas':distinct_verified_lemmas,
            'unique_native_surfaces':native_surfaces,'ramses_new_spelling_records':ramses_new,
            'ramses_duplicate_existing_surfaces':len(ramses_counts)-ramses_new,
            'ramses_corpus_word_model_records':len(ramses_counts),
            'ramses_conversion_audit':ramses_stats,
            'aed_dictionary_entries':len(aed),'aed_matched_lemmas':match_count,
            'aes_new_lemma_spelling_records':added,'aes_audit':aes_stats,**stats,
            'sources':sources,
            'claim':'Verified TLA and curated AES spellings plus unlinked Ramses word-model sign sequences; corpus-level Ramses evidence is not per-witness lemma attestation'}
    persist_json(out/'coverage.json',report)
    return report

def build_egyptian(tla_path,aed_path,out,aes_path=None,aes_whitelist=None,ramses_path=None,*,verify_pins=True):
    """Build a complete output directory or leave no output on failure."""
    destination=Path(out)
    if destination.exists():
        raise FileExistsError('Refuse to overwrite existing release: '+str(destination))
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.'+destination.name+'.building-',dir=destination.parent))
    try:
        report=_compile_egyptian(tla_path,aed_path,stage,aes_path,aes_whitelist,
                                 ramses_path,verify_pins=verify_pins)
        os.replace(stage,destination)
        return report
    finally:
        if stage.exists():shutil.rmtree(stage)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--tla',type=Path,required=True)
    p.add_argument('--aed',type=Path,required=True)
    p.add_argument('--aes',type=Path)
    p.add_argument('--aes-whitelist',type=Path)
    p.add_argument('--ramses',type=Path)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build_egyptian(a.tla,a.aed,a.out,a.aes,a.aes_whitelist,a.ramses),sort_keys=True))
