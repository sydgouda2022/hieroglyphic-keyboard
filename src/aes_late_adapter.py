"""Import only individually curated Late Egyptian documents from openly reused AES.

AES 'hiero_unicode' uses numeric HTML references, decoded exactly by
aes_unicode. A generic 'NK' historical date is NEVER sufficient: the text ID
must occur in the reviewed document whitelist. Known damaged/unlinked
tokens are omitted, never repaired by guess.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json
from aes_unicode import decode_aes_hiero
from gardiner_unicode import decoded_aes_token

AES_SAWLIT_SHA='b3d5eb695584be976b9981392eb4e149d13f447f677cf445b5a954898bc82ef4'

def curated_aes_rows(aes_path,whitelist_path):
    raw=Path(aes_path).read_bytes()
    fingerprint=hashlib.sha256(raw).hexdigest()
    if fingerprint!=AES_SAWLIT_SHA:raise ValueError('AES edition differs from verified source bytes')
    manifest=json.loads(Path(whitelist_path).read_text(encoding='utf-8'))
    if manifest.get('schema')!=1 or manifest.get('edition')!='AES 35276d2527cca1a055e31ed5f6683e777717170f':
        raise ValueError('Unapproved AES source-identity or stage whitelist')
    whitelisted={}
    for item in manifest.get('documents',[]):
        doc_id=item.get('id')
        if not doc_id or doc_id in whitelisted or not item.get('stage_basis') or not item.get('title'):
            raise ValueError('Invalid or duplicated individual document approval')
        dates=item.get('allowed_dates')
        if not isinstance(dates,list) or not dates or any(x not in ('NK','TIP - Roman times') for x in dates):
            raise ValueError('AES date filter must be explicit and historically bounded')
        whitelisted[doc_id]=item
    if not whitelisted:raise ValueError('Empty documented Late Egyptian source whitelist')
    sentences=json.loads(raw)
    if not isinstance(sentences,dict):raise ValueError('Invalid AES sentence collection')
    counter=Counter()
    references=defaultdict(list)
    stats=Counter()
    used_documents=set()
    for sid,s in sentences.items():
        if not isinstance(s,dict):continue
        text_id=s.get('text')
        item=whitelisted.get(text_id)
        if item is None:continue
        if s.get('date') not in item['allowed_dates']:
            stats['rejected_wrong_date']+=1
            continue
        stats['selected_sentences']+=1
        for token in s.get('token') or []:
            if not isinstance(token,dict):continue
            word,encoding=decoded_aes_token(token)
            if not word:
                stats['rejected_missing_or_incomplete_signs']+=1
                continue
            lemma=str(token.get('lemmaID') or '')
            if not lemma.isdigit():
                stats['rejected_missing_lemma']+=1
                continue
            key=(lemma,word)
            ref=str(token.get('_id') or '')
            if not ref:
                stats['rejected_missing_token_id']+=1
                continue
            counter[key]+=1
            if len(references[key])<24:references[key].append(f'{text_id}/{sid}/{ref}/{encoding}')
            used_documents.add(text_id)
            stats['qualified_tokens']+=1
            stats['qualified_'+encoding+'_tokens']+=1
    stats['curated_documents_with_unicode']=len(used_documents)
    stats['distinct_lemma_spellings']=len(counter)
    return counter,references,dict(stats),fingerprint
