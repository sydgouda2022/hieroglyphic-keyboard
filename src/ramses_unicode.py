"""Audit complete native hieroglyphic spellings in the pinned Ramses word model.

The 2023 MaReTE CC BY 4.0 word-model gives MdC sign sequences and estimated
transliteration frequencies, but NOT individual witness IDs or lemma IDs.
This module never invents lemmata or turns transliteration into signs.
"""
import collections,hashlib,json,re,unicodedata
from pathlib import Path
from hieroglyphic_unicode import native_word

RAMSES_MODEL_SHA256='b399acfef9462c76f4df97794a97369c24f33dc6d87269f315e41a5d16103691'
RAMSES_SOURCE_REV='c612a91407bddf8d546beedaf46edd5190a67eef'
_SIGN=re.compile(r'(?i)^(?:AA|NL|NU|[A-Z])([0-9]{1,3})([A-Z]?)$')
_TOKEN=re.compile(r'(?i)^(AA|NL|NU|[A-Z])([0-9]{1,3})([A-Z]?)$')
# The Ramses files encode a word as space-separated MdC sign codes.
# Any noncanonical sign, number shorthand, markup, or MdC layout operator
# rejects the ENTIRE word rather than producing a guessed partial spelling.
def ramses_native_word(mdc):
    if not isinstance(mdc,str) or not mdc or len(mdc)>2048:return None
    if '\t' in mdc or '\n' in mdc or mdc.startswith(' ') or mdc.endswith(' '):return None
    tokens=mdc.split(' ')
    if not 1<=len(tokens)<=256 or not all(tokens):return None
    out=[]
    for token in tokens:
        m=_TOKEN.fullmatch(token)
        if not m:return None
        cat,number,variant=m.groups()
        key=f'EGYPTIAN HIEROGLYPH {cat.upper()}{number.zfill(3)}{variant.upper()}'
        try:glyph=unicodedata.lookup(key)
        except KeyError:return None
        out.append(glyph)
    result=''.join(out)
    return result if native_word(result) else None

def audit_ramses(model_path):
    raw=Path(model_path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=RAMSES_MODEL_SHA256:raise ValueError('Ramses word model not pinned to verified sha256')
    model=json.loads(raw)
    if not isinstance(model,dict) or 'Ramses' not in model.get('modelName','') or not isinstance(model.get('words'),list):
        raise ValueError('Wrong source model')
    originals=collections.Counter()
    accepted=collections.Counter()
    sources=collections.defaultdict(list)
    rejected=collections.Counter()
    for row in model['words']:
        if not isinstance(row,dict):raise ValueError('Malformed model')
        mdc=row.get('encoding')
        glyphs=ramses_native_word(mdc)
        if glyphs is None:
            rejected['unconvertible']+=1
            if isinstance(mdc,str):
                rejected['mdc_'+mdc.split(' ',1)[0][:20]]+=1
            continue
        if glyphs in sources and mdc not in sources[glyphs] and len(sources[glyphs])<24:
            sources[glyphs].append(mdc)
        if not sources[glyphs]:sources[glyphs].append(mdc)
        original=originals[mdc];originals[mdc]+=1
        if original:rejected['duplicate_source_encoding']+=1
        frequency=0
        for item in row.get('interpretations',[]):
            if not isinstance(item,dict):continue
            n=item.get('freq',0)
            if isinstance(n,int) and n>=0:frequency+=n
        accepted[glyphs]+=max(1,frequency)
    return accepted,sources,{
      'source_revision':RAMSES_SOURCE_REV,'source_sha256':sha,
      'input_model_records':len(model['words']),
      'converted_unique_unicode_spellings':len(accepted),
      'converted_sign_sequence_instances':sum(originals.values()),
      'excluded_encoding_rows':rejected['unconvertible'],
      'top_rejected_first_tokens':rejected.most_common(30),
      'accepted_example_spellings':[[s,frequency,src[0]] for s,frequency,src in
         ((s,accepted[s],sources[s]) for s in list(accepted)[:12])]
    }
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser()
 p.add_argument('--model',required=True)
 p.add_argument('--report',required=True)
 args=p.parse_args()
 counts,refs,report=audit_ramses(args.model)
 Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print('RAMSES_AUDIT',json.dumps(report,ensure_ascii=False,sort_keys=True))
