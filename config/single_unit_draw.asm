; Relocatable Allegrex hook. Entry is original C9560 JAL's RA=C9568+base.
; Original a0=font,a1=context,a2=material,a3=metric,t0=XY read-only.
; Ordinary metrics tail-call original quad. Virtual metrics unpack seven pairs.
; No absolute addresses, relocations, embedded data, or moved source instructions.
entry:
    lhu t9,0(a3)
    sltiu t8,t9,256
    bne t8,zero,ordinary
    nop
    sltiu t8,t9,11428
    beq t8,zero,ordinary
    nop
    addiu sp,sp,-96
    sw s0,32(sp)
    sw s1,36(sp)
    sw s2,40(sp)
    sw s3,44(sp)
    sw s4,48(sp)
    sw s5,52(sp)
    sw s6,56(sp)
    sw ra,60(sp)
    swc1 f0,64(sp)
    swc1 f2,68(sp)
    or s0,a0,zero
    or s1,a1,zero
    or s2,a2,zero
    addiu s3,a3,2
    addiu s4,ra,-768
    ori s5,zero,0
    lw t1,0(t0)
    lw t2,4(t0)
    sw t1,16(sp)
    sw t2,20(sp)
pair:
    lbu t1,0(s3)
    lbu t2,1(s3)
    lbu t3,2(s3)
    andi t4,t2,15
    sll t4,t4,8
    or t1,t1,t4
    srl s6,t2,4
    sll t3,t3,4
    or s6,s6,t3
    addiu t1,t1,11428
    sll t1,t1,5
    addu a3,s0,t1
    addiu a3,a3,380
    or a0,s0,zero
    or a1,s1,zero
    or a2,s2,zero
    jalr s4,ra
    addiu t0,sp,16
    lwc1 f0,16(sp)
    lui t1,0x3f80
    mtc1 t1,f2
    add.s f0,f0,f2
    swc1 f0,16(sp)
    addiu t1,s6,11428
    sll t1,t1,5
    addu a3,s0,t1
    addiu a3,a3,380
    or a0,s0,zero
    or a1,s1,zero
    or a2,s2,zero
    jalr s4,ra
    addiu t0,sp,16
    lwc1 f0,16(sp)
    lui t1,0x3f80
    mtc1 t1,f2
    add.s f0,f0,f2
    swc1 f0,16(sp)
    addiu s3,s3,3
    addiu s5,s5,1
    ori t1,zero,2
    bne s5,t1,no_gap
    nop
    addiu s3,s3,8
no_gap:
    sltiu t1,s5,7
    bne t1,zero,pair
    nop
    lwc1 f0,64(sp)
    lwc1 f2,68(sp)
    lw s0,32(sp)
    lw s1,36(sp)
    lw s2,40(sp)
    lw s3,44(sp)
    lw s4,48(sp)
    lw s5,52(sp)
    lw s6,56(sp)
    lw ra,60(sp)
    or v0,zero,zero
    jr ra
    addiu sp,sp,96
ordinary:
    addiu t9,ra,-768
    jr t9
    nop
