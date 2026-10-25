"""Measure exact new Late Egyptian wordforms from explicitly selected AES documents.
This is an audit, never a date-only inference or permission for broad corpus import.
"""
from __future__ import annotations
import collections
import hashlib
import json
from pathlib import Path
from aes_unicode import decode_aes_hiero

def audit(source, whitelisted, baseline):
    aes=Path(source);base=Path(baseline)
    corpus=json.loads(aes.read_text())
    spec=json.loads(Path(whitelisted).read_text())
    assert spec['schema']==1 and len({x['id'] for x in spec['documents']})==len(spec['documents'])
    doc={x['id']:x for x in spec['documents']}
    before=set()
    for line in base.read_text().splitlines():
        if not line.strip():continue
        row=json.loads(line)
        signs=(row.get('hieroglyphs') or '').split()
        lemmas=[x.split('|',1)[0] for x in (row.get('lemmatization') or '').split()]
        if len(signs)==len(lemmas):
            before.update((lemmas[i],signs[i]) for i in range(len(signs)))
    found=collections.defaultdict(set)
    counts=collections.Counter()
    total=0
    for sentence_id,s in corpus.items():
        did=s.get('text')
        if did not in doc:continue
        spec_doc=doc[did]
        if s.get('date') not in spec_doc['allowed_dates']:
            counts[(did,'excluded_date')]+=1
            continue
        counts[(did,'sentences')]+=1
        for token in s.get('token') or []:
            form=decode_aes_hiero(token.get('hiero_unicode'))
            if not form:continue
            lemma=token.get('lemmaID')
            if not lemma or not str(lemma).isdigit():
                counts[(did,'unlinked')]+=1
                continue
            key=str(lemma),form
            counts[(did,'tokens')]+=1
            found[did].add(key)
            total+=1
    for did,item in doc.items():
        val=found[did]
        print(json.dumps({'title':item['title'],'id':did,'sentences':counts[(did,'sentences')],
            'attested_word_occurrences':counts[(did,'tokens')],
            'distinct_lemma_spellings':len(val),
            'additional_over_TLA_lemma_and_spelling':len(val-before),
            'unlinked_tokens':counts[(did,'unlinked')],
            'excluded_date':counts[(did,'excluded_date')]},ensure_ascii=False))
    allpairs=set().union(*found.values())
    print('TOTAL',json.dumps({'selected_documents':len(doc),'word_occurrences':total,
        'distinct_pairs':len(allpairs),'new_lemma_spellings':len(allpairs-before),
        'source_sha256':hashlib.sha256(aes.read_bytes()).hexdigest()},sort_keys=True))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--aes',required=True)
    p.add_argument('--whitelist',required=True)
    p.add_argument('--tla',required=True)
    a=p.parse_args();audit(a.aes,a.whitelist,a.tla)
