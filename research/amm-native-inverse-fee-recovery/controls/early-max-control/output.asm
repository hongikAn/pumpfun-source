
/home/ahi200/pumpfun-work/20261028-amm-inverse-arithmetic/early-max-control/input.o:	file format elf64-sbf

Disassembly of section .text.inverse_return:

0000000000000000 <inverse_return>:
       0:	mov64 r7, 0x1
       1:	ldxh r9, [r2 + 0x10]
       2:	mov64 r4, r3
       3:	jeq r9, 0x0, +0x2 <LBB0_2>
       4:	mov64 r4, 0x0
       5:	jne r3, 0x0, +0x3 <LBB0_3>

0000000000000030 <LBB0_2>:
       6:	stxdw [r1 + 0x8], r4
       7:	stxdw [r1 + 0x0], r7
       8:	exit

0000000000000048 <LBB0_3>:
       9:	ldxdw r8, [r2 + 0x8]
      10:	jne r9, 0x2710, +0xa <LBB0_8>
      11:	mov64 r4, r8
      12:	add64 r4, r3
      13:	mov64 r7, 0x0
      14:	mov64 r2, 0x1
      15:	jlt r4, r8, +0x1 <LBB0_6>
      16:	mov64 r2, 0x0

0000000000000088 <LBB0_6>:
      17:	and64 r2, 0x1
      18:	jne r2, 0x0, -0xd <LBB0_2>

0000000000000098 <LBB0_7>:
      19:	mov64 r7, 0x1
      20:	ja -0xf <LBB0_2>

00000000000000a8 <LBB0_8>:
      21:	mov64 r7, 0x0
      22:	jlt r9, 0x2711, +0x1 <LBB0_9>
      23:	ja -0x12 <LBB0_2>

00000000000000c0 <LBB0_9>:
      24:	stxdw [r10 - 0x28], r1
      25:	mov64 r1, r10
      26:	add64 r1, -0x10
      27:	stxdw [r10 - 0x30], r3
      28:	mov64 r2, r3
      29:	mov64 r3, 0x0
      30:	mov64 r4, 0x2710
      31:	mov64 r5, 0x0
      32:	call -0x1
      33:	mov64 r6, 0x1
      34:	ldxdw r1, [r10 - 0x10]
      35:	mov64 r2, 0x1
      36:	jlt r1, r9, +0x1 <LBB0_11>
      37:	mov64 r2, 0x0

0000000000000130 <LBB0_11>:
      38:	ldxdw r3, [r10 - 0x8]
      39:	sub64 r3, r2
      40:	sub64 r1, r9
      41:	mov64 r2, r1
      42:	add64 r2, 0x270f
      43:	mov64 r4, 0x1
      44:	jlt r2, r1, +0x1 <LBB0_13>
      45:	mov64 r4, 0x0

0000000000000170 <LBB0_13>:
      46:	add64 r3, r4
      47:	mov64 r4, 0x2710
      48:	sub64 r4, r9
      49:	mov64 r5, 0x1
      50:	jgt r9, 0x2710, +0x1 <LBB0_15>
      51:	mov64 r5, 0x0

00000000000001a0 <LBB0_15>:
      52:	neg64 r5
      53:	mov64 r1, r10
      54:	add64 r1, -0x20
      55:	call -0x1
      56:	ldxdw r4, [r10 - 0x20]
      57:	ldxdw r2, [r10 - 0x30]
      58:	jlt r4, r2, +0x1 <LBB0_17>
      59:	mov64 r6, 0x0

00000000000001e0 <LBB0_17>:
      60:	ldxdw r3, [r10 - 0x18]
      61:	ldxdw r1, [r10 - 0x28]
      62:	jeq r3, 0x0, +0x1 <LBB0_19>
      63:	mov64 r6, 0x0

0000000000000200 <LBB0_19>:
      64:	and64 r6, 0x1
      65:	jne r6, 0x0, -0x3c <LBB0_2>
      66:	mov64 r5, 0x1
      67:	jlt r4, r2, +0x1 <LBB0_22>
      68:	mov64 r5, 0x0

0000000000000228 <LBB0_22>:
      69:	mov64 r6, r4
      70:	sub64 r6, r2
      71:	mov64 r0, 0x1
      72:	jge r6, r8, +0x1 <LBB0_24>
      73:	mov64 r0, 0x0

0000000000000250 <LBB0_24>:
      74:	mov64 r6, r3
      75:	sub64 r6, r5
      76:	jeq r6, 0x0, +0x1 <LBB0_26>
      77:	mov64 r0, 0x1

0000000000000270 <LBB0_26>:
      78:	and64 r0, 0x1
      79:	jne r0, 0x0, +0x4 <LBB0_29>
      80:	mov64 r7, 0x1
      81:	jeq r3, 0x0, -0x4c <LBB0_2>
      82:	mov64 r7, 0x0
      83:	ja -0x4e <LBB0_2>

00000000000002a0 <LBB0_29>:
      84:	mov64 r4, r2
      85:	add64 r4, r8
      86:	mov64 r3, 0x1
      87:	jlt r4, r2, +0x1 <LBB0_31>
      88:	mov64 r3, 0x0

00000000000002c8 <LBB0_31>:
      89:	and64 r3, 0x1
      90:	jne r3, 0x0, -0x55 <LBB0_2>
      91:	ja -0x49 <LBB0_7>
