property_integer_group:
    addiu sp,sp,-16
    sw ra,12(sp)
    jal 0x6fcf4
    nop
    beq zero,zero,property_group_normalize
    nop
property_percent_group:
    addiu sp,sp,-16
    sw ra,12(sp)
    jal 0x6fe20
    nop
property_group_normalize:
    beq v0,zero,property_group_done
    or t0,v0,zero
    ori t1,zero,2048
property_group_leading:
    lhu t2,0(t0)
    ori t3,zero,32
    bne t2,t3,property_group_body
    nop
    addiu t1,t1,-1
    beq t1,zero,property_group_done
    addiu t0,t0,2
    beq zero,zero,property_group_leading
    nop
property_group_body:
    beq t2,zero,property_group_done
    ori t3,zero,160
    ori t4,zero,32
    bne t2,t4,property_group_next
    nop
    sh t3,0(t0)
property_group_next:
    addiu t1,t1,-1
    beq t1,zero,property_group_done
    addiu t0,t0,2
    lhu t2,0(t0)
    beq zero,zero,property_group_body
    nop
property_group_done:
    lw ra,12(sp)
    jr ra
    addiu sp,sp,16
