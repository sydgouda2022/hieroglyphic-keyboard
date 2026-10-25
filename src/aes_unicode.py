"""Strictly decode AES's published HTML numeric Egyptian hieroglyph notation.

AES serializes Unicode as '&#x131d3;' strings. Only complete hieroglyph
entity sequences are accepted, preserving all signs and excluding damage and
transcription-only fragments. Chronological language-stage validation is separate.
"""
import re
from hieroglyphic_unicode import native_word,is_sign

_ENTITY = re.compile(r"&#(?:x[0-9a-fA-F]{4,6}|[0-9]{5,7});")
def is_hieroglyph(char):
    n=ord(char)
    return is_sign(char) or 0x13430<=n<=0x13440

def decode_aes_hiero(text):
    if not isinstance(text,str) or not text or len(text)>4096:return None
    pieces=[]
    cursor=0
    for match in _ENTITY.finditer(text):
        if match.start()>cursor:
            fragment=text[cursor:match.start()]
            if not fragment or any(not is_hieroglyph(x) for x in fragment):return None
            pieces.append(fragment)
        try:
            n=int(match.group(0)[3:-1],16) if match.group(0).startswith('&#x') else int(match.group(0)[2:-1],10)
        except ValueError:return None
        if not 0x13000<=n<=0x143ff or not is_hieroglyph(chr(n)):return None
        pieces.append(chr(n))
        cursor=match.end()
    if cursor<len(text):
        tail=text[cursor:]
        if any(not is_hieroglyph(x) for x in tail):return None
        pieces.append(tail)
    joined=''.join(pieces)
    return joined if native_word(joined) else None
