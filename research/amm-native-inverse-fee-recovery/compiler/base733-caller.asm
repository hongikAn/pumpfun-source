
/home/ahi200/pumpfun-work/20261028-amm-fee-wrapper/value-match/symbols.so:	file format elf64-sbf

Disassembly of section .text:

000000000002a3d8 <_ZN18pump_amm_recovered5utils12transfer_fee17amount_before_fee17h2c1d02fd8f1c202fE>:
   21627:	mov64 r6, r1
   21628:	ldxdw r1, [r2 + 0x0]
   21629:	jne r1, 0x0, +0x2 <LBB209_8>
   21630:	stxdw [r6 + 0x8], r3
   21631:	ja +0xf <LBB209_2>

000000000002a400 <LBB209_8>:
   21632:	ldxdw r1, [r2 + 0x8]
   21633:	ldxdw r4, [r2 + 0x10]
   21634:	ldxh r2, [r2 + 0x18]
   21635:	stxh [r10 - 0x118], r2
   21636:	stxdw [r10 - 0x120], r4
   21637:	stxdw [r10 - 0x128], r1
   21638:	mov64 r1, r10
   21639:	add64 r1, -0x138
   21640:	mov64 r2, r10
   21641:	add64 r2, -0x128
   21642:	call 0x1b729
   21643:	ldxdw r1, [r10 - 0x138]
   21644:	jeq r1, 0x0, +0x4 <LBB209_4>
   21645:	ldxdw r1, [r10 - 0x130]
   21646:	stxdw [r6 + 0x8], r1

000000000002a478 <LBB209_2>:
   21647:	stdw [r6 + 0x0], 0x2
   21648:	ja +0x3f <LBB209_3>

000000000002a488 <LBB209_4>:
   21649:	mov64 r1, r10
   21650:	add64 r1, -0x70
   21651:	lddw r2, 0x1242c8
   21653:	call 0x17afb
   21654:	stdw [r10 - 0x48], 0x0
   21655:	stdw [r10 - 0x50], 0x1
   21656:	stdw [r10 - 0x58], 0x0
   21657:	lddw r1, 0x12a2a0
   21659:	stxdw [r10 - 0x18], r1
   21660:	mov64 r1, r10
   21661:	add64 r1, -0x58
   21662:	stxdw [r10 - 0x20], r1
   21663:	stb [r10 - 0x8], 0x3
   21664:	stdw [r10 - 0x10], 0x20
   21665:	stdw [r10 - 0x30], 0x0
   21666:	stdw [r10 - 0x40], 0x0
   21667:	mov64 r2, r10
   21668:	add64 r2, -0x40
   21669:	lddw r1, 0x1242c8
   21671:	call 0x185de
   21672:	jeq r0, 0x0, +0xa <LBB209_6>
   21673:	mov64 r3, r10
   21674:	add64 r3, -0x110
   21675:	lddw r1, 0x124382
   21677:	mov64 r2, 0x37
   21678:	lddw r4, 0x12a2d0
   21680:	lddw r5, 0x12a2f0
   21682:	call 0x1e191

000000000002a598 <LBB209_6>:
   21683:	ldxdw r1, [r10 - 0x48]
   21684:	stxdw [r10 - 0xc8], r1
   21685:	ldxdw r1, [r10 - 0x50]
   21686:	stxdw [r10 - 0xd0], r1
   21687:	ldxdw r1, [r10 - 0x58]
   21688:	stxdw [r10 - 0xd8], r1
   21689:	ldxdw r1, [r10 - 0x70]
   21690:	stxdw [r10 - 0xf0], r1
   21691:	ldxdw r1, [r10 - 0x68]
   21692:	stxdw [r10 - 0xe8], r1
   21693:	ldxdw r1, [r10 - 0x60]
   21694:	stxdw [r10 - 0xe0], r1
   21695:	lddw r1, 0x124a97
   21697:	stxdw [r10 - 0x108], r1
   21698:	stw [r10 - 0x78], 0x1787
   21699:	stb [r10 - 0xc0], 0x2
   21700:	stw [r10 - 0xf8], 0x43
   21701:	stdw [r10 - 0x100], 0x2b
   21702:	stdw [r10 - 0x110], 0x0
   21703:	mov64 r1, r10
   21704:	add64 r1, -0x148
   21705:	mov64 r2, r10
   21706:	add64 r2, -0x110
   21707:	call 0x1c17c
   21708:	ldxdw r1, [r10 - 0x148]
   21709:	ldxdw r2, [r10 - 0x140]
   21710:	stxdw [r6 + 0x8], r2
   21711:	stxdw [r6 + 0x0], r1

000000000002a680 <LBB209_3>:
   21712:	exit
