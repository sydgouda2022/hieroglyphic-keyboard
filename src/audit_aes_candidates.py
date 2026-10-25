"""Audit pending Late Egyptian documents; NO release import from this manifest.
Source is pinned AES literary corpus. Report exact new forms against all
previously approved TLA + AES evidence and expose sample Unicode spellings.
"""
import argparse,collections,hashlib,json
from pathlib import Path
from aes_unicode import decode_aes_hiero
from gardiner_unicode import decoded_aes_token
from aes_late_adapter import AES_SAWLIT_SHA,curated_aes_rows
from compile_lexica import source_rows

def audit(aes,whitelist,candidates,tla):
 aes=Path(aes)
 if hashlib.sha256(aes.read_bytes()).hexdigest()!=AES_SAWLIT_SHA:raise ValueError("Unpinned AES candidate file")
 approved,_,_,_=curated_aes_rows(aes,whitelist)
 tla_counts,_,_=source_rows(tla)
 baseline=set(approved)|set(tla_counts)
 man=json.loads(Path(candidates).read_text())
 assert man['schema']==1 and 'Candidate audit only' in man['purpose']
 items={x['id']:x for x in man['documents']}
 assert len(items)==len(man['documents'])
 rows={key:collections.Counter() for key in items}
 meta={key:collections.Counter() for key in items}
 examples=collections.defaultdict(list)
 for sid,s in json.loads(aes.read_bytes()).items():
  doc=s.get('text')
  if doc not in items:continue
  if s.get('date') not in items[doc]['allowed_dates']:
   meta[doc]['excluded_date']+=1;continue
  meta[doc]['sentences']+=1
  for tok in s.get('token') or []:
   written,encoding=decoded_aes_token(tok)
   lemma=str(tok.get('lemmaID') or '')
   if not written or not lemma.isdigit():
    meta[doc]['unscorable']+=1;continue
   key=(lemma,written)
   rows[doc][key]+=1
   meta[doc]['qualified_'+encoding]+=1
   if key not in baseline and len(examples[doc])<4 and key not in [tuple(x) for x in examples[doc]]:
    examples[doc].append([lemma,written])
 total=set()
 for doc,item in items.items():
  current=set(rows[doc]);novel=current-baseline;total |= current
  print('CANDIDATE',json.dumps({'id':doc,'title':item['title'],
   'sentences':meta[doc]['sentences'],'complete_lemma_linked_unicode_tokens':sum(rows[doc].values()),
   'unique_pairs':len(current),'new_over_current_approved':len(novel),
   'excluded_unscorable_tokens':meta[doc]['unscorable'],
   'unicode_tokens':meta[doc]['qualified_encoded_unicode'],
   'gardiner_sequence_tokens':meta[doc]['qualified_gardiner_sequence'],
   'new_examples':examples[doc]},ensure_ascii=False),flush=True)
 print('CANDIDATE_TOTAL',json.dumps({'documents':len(items),'unique_pairs':len(total),
  'additional_pairs_if_all_approved':len(total-baseline)},ensure_ascii=False),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser()
 for k in ('aes','whitelist','candidates','tla'):p.add_argument('--'+k,required=True)
 a=p.parse_args();audit(a.aes,a.whitelist,a.candidates,a.tla)
