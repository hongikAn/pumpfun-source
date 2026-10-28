
/home/ahi200/pumpfun-work/20261028-amm-inverse-arithmetic/late-max/input.o:	file format elf64-sbf

Disassembly of section .text.inverse_return:

0000000000000000 <inverse_return>:
       0:	mov64 r7, 0x1
       1:	ldxh r8, [r2 + 0x10]
       2:	mov64 r4, r3
       3:	jeq r8, 0x0, +0x2 <LBB0_2>
       4:	mov64 r4, 0x0
       5:	jne r3, 0x0, +0x3 <LBB0_3>

0000000000000030 <LBB0_2>:
       6:	stxdw [r1 + 0x8], r4
       7:	stxdw [r1 + 0x0], r7
       8:	exit

0000000000000048 <LBB0_3>:
       9:	jne r8, 0x2710, +0xb <LBB0_8>
      10:	ldxdw r5, [r2 + 0x8]
      11:	mov64 r4, r5
      12:	add64 r4, r3
      13:	mov64 r7, 0x0
      14:	mov64 r2, 0x1
      15:	jlt r4, r5, +0x1 <LBB0_6>
      16:	mov64 r2, 0x0

0000000000000088 <LBB0_6>:
      17:	and64 r2, 0x1
      18:	jne r2, 0x0, -0xd <LBB0_2>

0000000000000098 <LBB0_7>:
      19:	mov64 r7, 0x1
      20:	ja -0xf <LBB0_2>

00000000000000a8 <LBB0_8>:
      21:	mov64 r7, 0x0
      22:	jlt r8, 0x2711, +0x1 <LBB0_9>
      23:	ja -0x12 <LBB0_2>

00000000000000c0 <LBB0_9>:
      24:	stxdw [r10 - 0x28], r2
      25:	stxdw [r10 - 0x30], r1
      26:	mov64 r1, r10
      27:	add64 r1, -0x10
      28:	mov64 r6, 0x2710
      29:	stxdw [r10 - 0x38], r3
      30:	mov64 r2, r3
      31:	mov64 r3, 0x0
      32:	mov64 r4, 0x2710
      33:	mov64 r5, 0x0
      34:	call -0x1
      35:	mov64 r9, 0x1
      36:	ldxdw r1, [r10 - 0x10]
      37:	mov64 r2, 0x1
      38:	jlt r1, r8, +0x1 <LBB0_11>
      39:	mov64 r2, 0x0

0000000000000140 <LBB0_11>:
      40:	ldxdw r3, [r10 - 0x8]
      41:	sub64 r3, r2
      42:	sub64 r1, r8
      43:	mov64 r2, r1
      44:	add64 r2, 0x270f
      45:	mov64 r4, 0x1
      46:	jlt r2, r1, +0x1 <LBB0_13>
      47:	mov64 r4, 0x0

0000000000000180 <LBB0_13>:
      48:	add64 r3, r4
      49:	sub64 r6, r8
      50:	mov64 r5, 0x1
      51:	jgt r8, 0x2710, +0x1 <LBB0_15>
      52:	mov64 r5, 0x0

00000000000001a8 <LBB0_15>:
      53:	neg64 r5
      54:	mov64 r1, r10
      55:	add64 r1, -0x20
      56:	mov64 r4, r6
      57:	call -0x1
      58:	ldxdw r4, [r10 - 0x20]
      59:	ldxdw r2, [r10 - 0x38]
      60:	jlt r4, r2, +0x1 <LBB0_17>
      61:	mov64 r9, 0x0

00000000000001f0 <LBB0_17>:
      62:	ldxdw r3, [r10 - 0x18]
      63:	ldxdw r1, [r10 - 0x30]
      64:	ldxdw r5, [r10 - 0x28]
      65:	jeq r3, 0x0, +0x1 <LBB0_19>
      66:	mov64 r9, 0x0

0000000000000218 <LBB0_19>:
      67:	and64 r9, 0x1
      68:	jne r9, 0x0, -0x3f <LBB0_2>
      69:	mov64 r6, 0x1
      70:	jlt r4, r2, +0x1 <LBB0_22>
      71:	mov64 r6, 0x0

0000000000000240 <LBB0_22>:
      72:	mov64 r0, r3
      73:	sub64 r0, r6
      74:	mov64 r7, r4
      75:	sub64 r7, r2
      76:	ldxdw r5, [r5 + 0x8]
      77:	mov64 r6, 0x1
      78:	jge r7, r5, +0x1 <LBB0_24>
      79:	mov64 r6, 0x0

0000000000000280 <LBB0_24>:
      80:	jeq r0, 0x0, +0x1 <LBB0_26>
      81:	mov64 r6, 0x1

0000000000000290 <LBB0_26>:
      82:	and64 r6, 0x1
      83:	jne r6, 0x0, +0x4 <LBB0_29>
      84:	mov64 r7, 0x1
      85:	jeq r3, 0x0, -0x50 <LBB0_2>
      86:	mov64 r7, 0x0
      87:	ja -0x52 <LBB0_2>

00000000000002c0 <LBB0_29>:
      88:	mov64 r4, r2
      89:	add64 r4, r5
      90:	mov64 r7, 0x0
      91:	mov64 r3, 0x1
      92:	jlt r4, r2, +0x1 <LBB0_31>
      93:	mov64 r3, 0x0

00000000000002f0 <LBB0_31>:
      94:	and64 r3, 0x1
      95:	jne r3, 0x0, -0x5a <LBB0_2>
      96:	ja -0x4e <LBB0_7>
