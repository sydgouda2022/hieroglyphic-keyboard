#!/usr/bin/env python3
"""Audit, but DO NOT import, AES Unicode signs by documented corpus/date.
The audit is a prerequisite for a defensible Late Egyptian stage filter.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,sys
from pathlib import Path
from aes_unicode import decode_aes_hiero

def encoded(s):
    return isinstance(s,str) and bool(s) and len(s)<=256 and all(
        0x13000<=ord(c)<=0x1342F or 0x13460<=ord(c)<=0x143FF for c in s
    )

def audit(paths):
    full=collections.Counter()
    examples=collections.defaultdict(list)
    invalid_examples=collections.defaultdict(list)
    group_rows={}
    unique=set()
    for path in paths:
        path=Path(path)
        raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest()
        x=json.loads(raw)
        if not isinstance(x,dict):raise ValueError('AES expects sentence dictionary')
        tally=collections.Counter()
        for sid,sentence in x.items():
            if not isinstance(sentence,dict):continue
            date=str(sentence.get('date','')).strip() or '[none]'
            group=str(sentence.get('corpus','')).strip() or '[unknown]'
            key=(group,date)
            tokens=sentence.get('token') or []
            tally[(date,'sentences')]+=1
            full[(key,'sentences')]+=1
            for token in tokens:
                if not isinstance(token,dict):continue
                tally[(date,'tokens')]+=1
                text=token.get('hiero_unicode')
                if not isinstance(text,str) or not text.strip():continue
                tally[(date,'encoded_nonempty')]+=1
                decoded=decode_aes_hiero(text)
                if decoded:
                    tally[(date,'valid')]+=1
                    full[(key,'valid')]+=1
                    unique.add((str(token.get('lemmaID') or ''),decoded))
                    if len(examples[key])<2:examples[key].append({
                        'sentence':sid,'lemma':token.get('lemmaID'),'writing':decoded,
                        'date':date,'token_id':token.get('_id')
                    })
                else:
                    tally[(date,'invalid_unicode')]+=1
                    if len(invalid_examples[key])<3:invalid_examples[key].append({
                        'sentence':sid,'lemma':token.get('lemmaID'),
                        'field_repr':repr(text[:120]),
                        'unicode_points':[hex(ord(c)) for c in text[:32]],
                        'hiero':str(token.get('hiero',''))[:80]
                    })
        print('AES_FILE',json.dumps({'filename':path.name,'sha256':h,'bytes':len(raw),
            'sentences':len(x),'date_counts':[{'date':k[0],'kind':k[1],'n':n} for k,n in tally.most_common(50)]
        },ensure_ascii=False),flush=True)
        group_rows[path.name]=dict(tally)
    print('AES_UNIQUE_LEMMA_SPELLINGS',len(unique))
    for (group,date),kind in sorted(full):
        if kind!='sentences':continue
        print('AES_STAGE',json.dumps({'corpus':group,'date':date,
           'sentences':full[((group,date),'sentences')],
           'unicode_word_tokens':full[((group,date),'valid')],
           'example':examples[(group,date)],'invalid_examples':invalid_examples[(group,date)]
        },ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('json',nargs='+')
    audit(p.parse_args().json)
