"""Conservative bound for source3081 through the observed70E84 numeric pipeline.

051/052 bind each numeric slot from the same16-unit UTF16 staging buffer.
D8FD4 reserves its last unit and always NUL-terminates valid positive-capacity
calls, even on truncation. This bounds storage, not numeric semantic accuracy.
"""
import re

def check_ability3081_expansion(text):
    if '\0' in text or text.count('$')!=4 or re.findall(r'\$[0-9A-Za-z]+',text)!=['$1','$2','$3','$4']:
        raise ValueError('Ability3081 requires exactly the four observed ordered slots')
    literal=text
    for n in range(1,5):literal=literal.replace('$'+str(n),'')
    # Any valid15-unit UTF16 result needs at most45 UTF8 bytes. Numeric ASCII
    # is smaller, but no ASCII-only assumption is needed for this bound.
    units=len(literal.encode('utf-16le'))//2+4*15+1
    byte_count=len(literal.encode('utf-8'))+4*45+1
    if units>2048:raise ValueError(f'Ability3081 expanded UTF16 bound {units} exceeds2048 including NUL')
    if byte_count>5000:raise ValueError(f'Ability3081 expanded UTF8 bound {byte_count} exceeds5000 including NUL')
    return {'max_UTF16_units_including_NUL':units,'max_UTF8_bytes_including_NUL':byte_count,
            'numeric_slots':4,'max_staged_UTF16_units_per_slot':15,'max_UTF8_bytes_per_slot':45}
