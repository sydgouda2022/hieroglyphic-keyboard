"""Unambiguous Gardiner sign-sequence to Unicode transcription.
Uses Python's pinned Unicode Character Database sign names, without
interpreting MdC geometry or filling damaged/unknown glyphs.
"""
import re,unicodedata
from hieroglyphic_unicode import native_word

LABEL=re.compile(r"(?i)^(A{1,2}|NL|NU|[A-Z])([0-9]{1,3})([A-Z]?)$")
SEQUENCE=re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")

def gardiner_sequence(value):
    if not isinstance(value,str) or not value or len(value)>2048 or not SEQUENCE.fullmatch(value):return None
    units=value.split('-')
    if len(units)>256:return None
    rendered=[]
    for unit in units:
        m=LABEL.fullmatch(unit)
        if not m:return None
        category,num,suffix=m.groups()
        try:ch=unicodedata.lookup('EGYPTIAN HIEROGLYPH '+category.upper()+num.zfill(3)+suffix.upper())
        except KeyError:return None
        rendered.append(ch)
    output=''.join(rendered)
    return output if native_word(output) else None

def decoded_aes_token(token):
    """Return (written Unicode sequence, encoding method), or (None,None).

    If an explicitly supplied Unicode spelling is damaged, NEVER substitute
    a Gardiner sequence behind the user's back.
    """
    from aes_unicode import decode_aes_hiero
    direct=token.get('hiero_unicode')
    if isinstance(direct,str) and direct.strip():
        x=decode_aes_hiero(direct)
        return (x,'encoded_unicode') if x else (None,None)
    x=gardiner_sequence(token.get('hiero'))
    return (x,'gardiner_sequence') if x else (None,None)
