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
    or a0,s1,zero
    ori a1,zero,6
    jal ensure_text_mode
    nop
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
    jal sprite_quad
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
    jal sprite_quad
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
    lw t9,0x484(a1)
    ori t8,zero,6
    bne t9,t8,ordinary_ready
    nop
    addiu sp,sp,-48
    sw a0,16(sp)
    sw a1,20(sp)
    sw a2,24(sp)
    sw a3,28(sp)
    sw t0,32(sp)
    sw ra,36(sp)
    or a0,a1,zero
    ori a1,zero,3
    jal ensure_text_mode
    nop
    lw a0,16(sp)
    lw a1,20(sp)
    lw a2,24(sp)
    lw a3,28(sp)
    lw t0,32(sp)
    lw ra,36(sp)
    addiu sp,sp,48
ordinary_ready:
    j 0xc9268
    nop

; Context mode6 is private to the new text batch. Other callers keep old quad.
sprite_quad:
    lw t9,0x484(a1)
    ori t8,zero,6
    bne t9,t8,sprite_ordinary
    nop
    addiu sp,sp,-64
    swc1 f20,24(sp)
    swc1 f22,28(sp)
    sw s0,32(sp)
    sw s1,36(sp)
    sw s2,40(sp)
    sw ra,48(sp)
    or s0,t0,zero
    or s1,a3,zero
    or s2,a1,zero
    lwc1 f12,24(s1)
    lwc1 f13,16(s1)
    lwc1 f14,28(s1)
    lwc1 f15,20(s1)
    sub.s f22,f12,f13
    sub.s f20,f14,f15
    lui t1,0x4400
    mtc1 t1,f12
    mul.s f22,f22,f12
    mul.s f20,f20,f12
    lhu t1,0(s1)
    sltiu t2,t1,128
    bne t2,zero,sprite_normal_color
    or a1,a2,zero
    sltiu t2,t1,144
    beq t2,zero,sprite_normal_color
    nop
sprite_white_hi:
    lui a1,0x16
sprite_white_lo:
    addiu a1,a1,0x11c0
sprite_normal_color:
    jal 0x9410c
    or a0,s2,zero
    lwc1 f12,16(s1)
    lwc1 f13,20(s1)
    swc1 f12,16(sp)
    swc1 f13,20(sp)
    or a0,s2,zero
    jal 0x94224
    addiu a1,sp,16
    or a0,s2,zero
    jal 0x94244
    or a1,s0,zero
    lwc1 f12,24(s1)
    lwc1 f13,28(s1)
    swc1 f12,16(sp)
    swc1 f13,20(sp)
    or a0,s2,zero
    jal 0x94224
    addiu a1,sp,16
    lwc1 f12,0(s0)
    lwc1 f13,4(s0)
    add.s f12,f12,f22
    add.s f13,f13,f20
    swc1 f12,16(sp)
    swc1 f13,20(sp)
    or a0,s2,zero
    jal 0x94244
    addiu a1,sp,16
    or v0,zero,zero
    lwc1 f20,24(sp)
    lwc1 f22,28(sp)
    lw s0,32(sp)
    lw s1,36(sp)
    lw s2,40(sp)
    lw ra,48(sp)
    jr ra
    addiu sp,sp,64
sprite_ordinary:
    j 0xc9268
    nop

; Same allocator ceiling, texture/material setup and format as original flush.
; Only the mode6 text batch emits GU_SPRITES (two vertices per rectangle).
sprite_flush:
    lw t9,0x484(a0)
    ori t8,zero,6
    bne t9,t8,sprite_flush_ordinary
    nop
    addiu sp,sp,-64
    sw s0,16(sp)
    sw s1,20(sp)
    sw s2,24(sp)
    sw s3,28(sp)
    sw s4,32(sp)
    sw ra,36(sp)
    or s0,a0,zero
    lw t0,0x4b0(s0)
    beq t0,zero,sprite_flush_done
    nop
    jal 0x12ba3c
    nop
    lw t0,0x4b0(s0)
    sll s4,t0,5
    sll t0,t0,2
    addu s4,s4,t0
    addu t0,v0,s4
    lui t1,8
    addiu t1,t1,-0x8000
    sltu t1,t1,t0
    bne t1,zero,sprite_flush_done
    nop
    jal 0x12b34c
    or a0,s4,zero
    or s1,v0,zero
    or a0,s1,zero
    addiu a1,s0,0x4b4
    jal 0x11f748
    or a2,s4,zero
    jal 0x94408
    or a0,s0,zero
    lui s2,5
    addu s2,s0,s2
    ori s3,zero,0
sprite_material_loop:
    lw t0,-0x78dc(s2)
    bne t0,zero,sprite_have_material
    nop
    lw t0,-0x78e0(s2)
sprite_have_material:
    lw t0,28(t0)
    slt t0,s3,t0
    beq t0,zero,sprite_flush_done
    nop
    or a0,s0,zero
    jal 0x951ac
    or a1,s3,zero
    ori a0,zero,6
    ori a1,zero,0x1ff
    lw a2,0x4b0(s0)
    or a3,zero,zero
    jal 0x12c398
    or t0,s1,zero
    addiu s3,s3,1
    beq zero,zero,sprite_material_loop
    nop
sprite_flush_done:
    sw zero,0x484(s0)
    or v0,zero,zero
    lw s0,16(sp)
    lw s1,20(sp)
    lw s2,24(sp)
    lw s3,28(sp)
    lw s4,32(sp)
    lw ra,36(sp)
    jr ra
    addiu sp,sp,64
sprite_flush_ordinary:
    j 0x93f08
    nop

; Only switch the font triangle/sprite modes. Preserve every volatile FPR
; across the larger flush call graph, beyond original quad's clobber set.
ensure_text_mode:
    lw t9,0x484(a0)
    beq t9,a1,ensure_mode_done
    nop
    ori t8,zero,3
    beq t9,t8,ensure_mode_change
    nop
    ori t8,zero,6
    bne t9,t8,ensure_mode_done
    nop
ensure_mode_change:
    addiu sp,sp,-128
    sw a0,16(sp)
    sw a1,20(sp)
    sw ra,24(sp)
    swc1 f0,32(sp)
    swc1 f1,36(sp)
    swc1 f2,40(sp)
    swc1 f3,44(sp)
    swc1 f4,48(sp)
    swc1 f5,52(sp)
    swc1 f6,56(sp)
    swc1 f7,60(sp)
    swc1 f8,64(sp)
    swc1 f9,68(sp)
    swc1 f10,72(sp)
    swc1 f11,76(sp)
    swc1 f12,80(sp)
    swc1 f13,84(sp)
    swc1 f14,88(sp)
    swc1 f15,92(sp)
    swc1 f16,96(sp)
    swc1 f17,100(sp)
    swc1 f18,104(sp)
    swc1 f19,108(sp)
    jal sprite_flush
    nop
    lw a0,16(sp)
    jal 0x93ed8
    lw a1,20(sp)
    lwc1 f0,32(sp)
    lwc1 f1,36(sp)
    lwc1 f2,40(sp)
    lwc1 f3,44(sp)
    lwc1 f4,48(sp)
    lwc1 f5,52(sp)
    lwc1 f6,56(sp)
    lwc1 f7,60(sp)
    lwc1 f8,64(sp)
    lwc1 f9,68(sp)
    lwc1 f10,72(sp)
    lwc1 f11,76(sp)
    lwc1 f12,80(sp)
    lwc1 f13,84(sp)
    lwc1 f14,88(sp)
    lwc1 f15,92(sp)
    lwc1 f16,96(sp)
    lwc1 f17,100(sp)
    lwc1 f18,104(sp)
    lwc1 f19,108(sp)
    lw ra,24(sp)
    addiu sp,sp,128
ensure_mode_done:
    jr ra
    nop

