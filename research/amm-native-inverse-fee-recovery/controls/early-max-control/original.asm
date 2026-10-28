
/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source/evidence/original/pump_amm/deployed.so:	file format elf64-sbf

Disassembly of section .text:

00000000000ee4b0 <custom_panic>:
  124378:	mov64 r7, 0x1
  124379:	ldxh r8, [r2 + 0x10]
  124380:	mov64 r4, r3
  124381:	jeq r8, 0x0, +0x2 <custom_panic+0x4a50>
  124382:	mov64 r4, 0x0
  124383:	jne r3, 0x0, +0x3 <custom_panic+0x4a68>
  124384:	stxdw [r1 + 0x8], r4
  124385:	stxdw [r1 + 0x0], r7
  124386:	exit
  124387:	jne r8, 0x2710, +0xb <custom_panic+0x4ac8>
  124388:	ldxdw r5, [r2 + 0x8]
  124389:	mov64 r4, r5
  124390:	add64 r4, r3
  124391:	mov64 r7, 0x0
  124392:	mov64 r2, 0x1
  124393:	jlt r4, r5, +0x1 <custom_panic+0x4aa8>
  124394:	mov64 r2, 0x0
  124395:	and64 r2, 0x1
  124396:	jne r2, 0x0, -0xd <custom_panic+0x4a50>
  124397:	mov64 r7, 0x1
  124398:	ja -0xf <custom_panic+0x4a50>
  124399:	mov64 r7, 0x0
  124400:	jlt r8, 0x2711, +0x1 <custom_panic+0x4ae0>
  124401:	ja -0x12 <custom_panic+0x4a50>
  124402:	stxdw [r10 - 0x28], r2
  124403:	stxdw [r10 - 0x30], r1
  124404:	mov64 r1, r10
  124405:	add64 r1, -0x10
  124406:	mov64 r6, 0x2710
  124407:	stxdw [r10 - 0x38], r3
  124408:	mov64 r2, r3
  124409:	mov64 r3, 0x0
  124410:	mov64 r4, 0x2710
  124411:	mov64 r5, 0x0
  124412:	call 0x5109
  124413:	mov64 r9, 0x1
  124414:	ldxdw r1, [r10 - 0x10]
  124415:	mov64 r2, 0x1
  124416:	jlt r1, r8, +0x1 <custom_panic+0x4b60>
  124417:	mov64 r2, 0x0
  124418:	ldxdw r3, [r10 - 0x8]
  124419:	sub64 r3, r2
  124420:	sub64 r1, r8
  124421:	mov64 r2, r1
  124422:	add64 r2, 0x270f
  124423:	mov64 r4, 0x1
  124424:	jlt r2, r1, +0x1 <custom_panic+0x4ba0>
  124425:	mov64 r4, 0x0
  124426:	add64 r3, r4
  124427:	sub64 r6, r8
  124428:	mov64 r5, 0x1
  124429:	jgt r8, 0x2710, +0x1 <custom_panic+0x4bc8>
  124430:	mov64 r5, 0x0
  124431:	neg64 r5
  124432:	mov64 r1, r10
  124433:	add64 r1, -0x20
  124434:	mov64 r4, r6
  124435:	call 0x4e4a
  124436:	ldxdw r4, [r10 - 0x20]
  124437:	ldxdw r2, [r10 - 0x38]
  124438:	jlt r4, r2, +0x1 <custom_panic+0x4c10>
  124439:	mov64 r9, 0x0
  124440:	ldxdw r3, [r10 - 0x18]
  124441:	ldxdw r1, [r10 - 0x30]
  124442:	ldxdw r5, [r10 - 0x28]
  124443:	jeq r3, 0x0, +0x1 <custom_panic+0x4c38>
  124444:	mov64 r9, 0x0
  124445:	and64 r9, 0x1
  124446:	jne r9, 0x0, -0x3f <custom_panic+0x4a50>
  124447:	mov64 r6, 0x1
  124448:	jlt r4, r2, +0x1 <custom_panic+0x4c60>
  124449:	mov64 r6, 0x0
  124450:	mov64 r0, r3
  124451:	sub64 r0, r6
  124452:	mov64 r7, r4
  124453:	sub64 r7, r2
  124454:	ldxdw r5, [r5 + 0x8]
  124455:	mov64 r6, 0x1
  124456:	jge r7, r5, +0x1 <custom_panic+0x4ca0>
  124457:	mov64 r6, 0x0
  124458:	jeq r0, 0x0, +0x1 <custom_panic+0x4cb0>
  124459:	mov64 r6, 0x1
  124460:	and64 r6, 0x1
  124461:	jne r6, 0x0, +0x4 <custom_panic+0x4ce0>
  124462:	mov64 r7, 0x1
  124463:	jeq r3, 0x0, -0x50 <custom_panic+0x4a50>
  124464:	mov64 r7, 0x0
  124465:	ja -0x52 <custom_panic+0x4a50>
  124466:	mov64 r4, r2
  124467:	add64 r4, r5
  124468:	mov64 r7, 0x0
  124469:	mov64 r3, 0x1
  124470:	jlt r4, r2, +0x1 <custom_panic+0x4d10>
  124471:	mov64 r3, 0x0
  124472:	and64 r3, 0x1
  124473:	jne r3, 0x0, -0x5a <custom_panic+0x4a50>
  124474:	ja -0x4e <custom_panic+0x4ab8>
