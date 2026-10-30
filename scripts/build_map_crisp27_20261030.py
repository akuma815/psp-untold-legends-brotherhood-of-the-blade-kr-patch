"""Source-derived schema27 entry; reuses original Expected-Write folder builder.

The dispatch extension is process-local. Frozen older builder/scripts stay intact.
"""
import build_font_folder as builder
from map_crisp27_20261030 import derive_crisp

base=builder.derive
def derive(variant,diagnostic=None,font_route_probe=None):
    if diagnostic is not None and diagnostic.get('schema_version')==27:
        assert variant=='unicode_hangul_alias_fallback' and font_route_probe is None
        return derive_crisp(diagnostic)
    return base(variant,diagnostic,font_route_probe)

if __name__=='__main__':
    builder.derive=derive
    builder.main()
