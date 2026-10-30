"""Observed formatted wrappers only; these are necessary template guards.

DA634/DA810 pass5000 bytes to DB03C, which passes end=start+capacity to
DB160. Exact exhaustion reports an error and forces NUL at end-1.
D8FD4 receives2048 UTF16 units in the observed UI/tutorial paths.
Variable expansion needs its own final-output bound; template size alone
does not establish every possible formatted result.
"""
FORMAT_UTF8_CAPACITY=5000
DECODE_UTF16_CAPACITY=2048

def check_template(text,scope):
    if len(text.encode('utf-8'))>=FORMAT_UTF8_CAPACITY:
        raise ValueError(f'{scope} exceeds observed4999-byte UTF8 formatter payload budget')
    if len(text.encode('utf-16le'))//2>=DECODE_UTF16_CAPACITY:
        raise ValueError(f'{scope} exceeds observed2047-unit UTF16 payload budget')
