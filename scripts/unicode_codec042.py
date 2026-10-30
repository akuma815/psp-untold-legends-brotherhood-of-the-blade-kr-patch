"""Experimental literal Hangul UTF8; undeclared missing glyphs still fail."""
def encode_unicode(text,book,probes=()):
    for char in text:
        code=ord(char)
        if code<=255 or 0xac00<=code<=0xd7a3 or code in probes:continue
        raise ValueError(f'Unmapped Unicode diagnostic character U+{code:04X}')
    return text

def decode_unicode(text,book,probes=()):return encode_unicode(text,book,probes)
