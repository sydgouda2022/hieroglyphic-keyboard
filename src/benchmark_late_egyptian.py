"""Honest leave-one-document-out Late Egyptian Unicode spelling coverage.

Compare (a) TLA v19 baseline and (b) TLA + other curated AES documents.
The evaluated AES document itself never contributes vocabulary to its test.
Results are limited to complete Unicode and lemma-linked word occurrences;
unencoded text is explicitly counted and NEVER silently scored as covered.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from pathlib import Path
import argparse,json,hashlib
from aes_unicode import decode_aes_hiero
from gardiner_unicode import decoded_aes_token
from aes_late_adapter import AES_SAWLIT_SHA

def get_baseline(path):
    from compile_lexica import source_rows
    counts,_,stats=source_rows(path)
    return set(counts),stats

def benchmark(aes_path,whitelist_path,tla_path):
    source=Path(aes_path).read_bytes()
    if hashlib.sha256(source).hexdigest()!=AES_SAWLIT_SHA:
        raise ValueError('Unverified AES source revision')
    manifest=json.loads(Path(whitelist_path).read_text())
    if manifest.get('schema')!=1 or manifest.get('edition')!='AES 35276d2527cca1a055e31ed5f6683e777717170f':
        raise ValueError('Incorrect curated AES document list')
    approved={x['id']:x for x in manifest['documents']}
    base,stats=get_baseline(tla_path)
    document_tokens=defaultdict(list)
    excluded=Counter()
    for sid,s in json.loads(source).items():
        docid=s.get('text')
        if docid not in approved:continue
        if s.get('date') not in approved[docid]['allowed_dates']:
            excluded[(docid,'wrong_date')]+=1
            continue
        for token in s.get('token') or []:
            surface,_encoding=decoded_aes_token(token)
            lemma=str(token.get('lemmaID') or '')
            if not surface or not lemma.isdigit():
                excluded[(docid,'unscorable')]+=1
                continue
            document_tokens[docid].append((lemma,surface))
    by_doc={docid:set(tokens) for docid,tokens in document_tokens.items()}
    reports=[]
    all_tokens=0;total_base=0;total_other=0
    type_n=0;type_base=0;type_other=0
    for docid,item in approved.items():
        tokens=document_tokens[docid]
        types=by_doc.get(docid,set())
        others=base | set().union(*(v for k,v in by_doc.items() if k!=docid))
        eligible=len(tokens)
        base_hits=sum(pair in base for pair in tokens)
        other_hits=sum(pair in others for pair in tokens)
        base_type_hits=len(types&base)
        other_type_hits=len(types&others)
        all_tokens+=eligible;total_base+=base_hits;total_other+=other_hits
        type_n+=len(types);type_base+=base_type_hits;type_other+=other_type_hits
        reports.append({
          'document_id':docid,'title':item['title'],
          'eligible_lemma_linked_unicode_tokens':eligible,
          'unscorable_tokens':excluded[(docid,'unscorable')],
          'distinct_lemma_spellings':len(types),
          'tla_token_coverage':round(base_hits/eligible,4) if eligible else None,
          'leave_document_out_token_coverage':round(other_hits/eligible,4) if eligible else None,
          'tla_type_coverage':round(base_type_hits/len(types),4) if types else None,
          'leave_document_out_type_coverage':round(other_type_hits/len(types),4) if types else None,
        })
    return {'benchmark':'curated_aes_late_egyptian_leave_one_document_out_v1',
       'not_a_complete_historical_coverage_claim':True,
       'training_policy':'each selected AES document excluded from its own scoring; TLA included',
       'scope':'only complete, lemma-linked Unicode words; excludes unencoded/damaged and other historical stages',
       'documents':reports,
       'total_eligible_tokens':all_tokens,
       'overall_tla_token_coverage':round(total_base/all_tokens,4) if all_tokens else None,
       'overall_leave_document_out_token_coverage':round(total_other/all_tokens,4) if all_tokens else None,
       'total_distinct_document_types':type_n,
       'overall_tla_type_coverage':round(type_base/type_n,4) if type_n else None,
       'overall_leave_document_out_type_coverage':round(type_other/type_n,4) if type_n else None}

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--aes',type=Path,required=True)
 p.add_argument('--whitelist',type=Path,required=True)
 p.add_argument('--tla',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();result=benchmark(a.aes,a.whitelist,a.tla)
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))
