; Public glyph input remains real Unicode; private column lookup uses direct pointers.
; Same externally modified GPRs as original C95D8:a0,a1,a2,v0. No stack/FPR/RA use.
unicode_selector:
    andi a1,a1,0xffff
    ori a2,zero,0xac00
    subu a2,a1,a2
    sltiu v0,a2,11172
    bne v0,zero,unicode_hangul
    nop
    sltiu a2,a1,256
    bne a2,zero,unicode_latin1
    nop
    addiu a0,a0,0x17c
    addiu v0,a0,0x7e0
    jr ra
    nop
unicode_latin1:
    sll v0,a1,5
    addiu a0,a0,0x17c
    addu v0,a0,v0
    jr ra
    nop
unicode_hangul:
    addiu a2,a2,256
    sll v0,a2,5
    addiu a0,a0,0x17c
    ori a2,zero,1
    addu v0,a0,v0
    jr ra
    nop
