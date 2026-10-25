"""Strict Unicode Egyptian hieroglyphic word/format validator.

Accept complete native signs and valid quadrat format operations, but never
treat lacunae, editorial markup, unpaired format operators, or transliteration
as an attested complete spelling. No MdC-to-Unicode guessing is performed.
"""
from __future__ import annotations

SIGN_RANGES=((0x13000,0x1342F),(0x13460,0x143FF))
OPERATORS=frozenset(range(0x13430,0x13437)) | frozenset(range(0x13439,0x1343C))
OPEN_TO_CLOSE={0x13437:0x13438,0x1343C:0x1343D,0x1343E:0x1343F}
CLOSE=set(OPEN_TO_CLOSE.values())
MIRROR=0x13440
FORMAT_CHARS=frozenset(range(0x13430,0x13441))

def is_sign(char: str) -> bool:
    return len(char)==1 and any(lo<=ord(char)<=hi for lo,hi in SIGN_RANGES)

def has_format_controls(text: str) -> bool:
    return isinstance(text,str) and any(ord(ch) in FORMAT_CHARS for ch in text)

def native_word(text: str) -> bool:
    if not isinstance(text,str) or not text or len(text)>256:return False
    stack=[]
    expect_operand=True
    pending_mirror=False
    sign_count=0
    for ch in text:
        cp=ord(ch)
        if is_sign(ch):
            sign_count+=1
            expect_operand=False
            pending_mirror=False
        elif cp==MIRROR:
            # Mirroring is a prefix modifier. Never permit a dangling mirror.
            if not expect_operand or pending_mirror:return False
            pending_mirror=True
        elif cp in OPEN_TO_CLOSE:
            if pending_mirror:return False
            stack.append(OPEN_TO_CLOSE[cp])
            expect_operand=True
        elif cp in CLOSE:
            if pending_mirror or expect_operand or not stack or stack[-1]!=cp:return False
            stack.pop()
            expect_operand=False
        elif cp in OPERATORS:
            if expect_operand or pending_mirror:return False
            expect_operand=True
        else:
            # Including damaged/blank signs and all unassigned format values.
            return False
    return sign_count>0 and not expect_operand and not pending_mirror and not stack
