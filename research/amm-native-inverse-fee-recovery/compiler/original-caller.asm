
/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-source/evidence/original/pump_amm/deployed.so:	file format elf64-sbf

Disassembly of section .text:

0000000000000120 <.text>:
   59760:	mov64 r6, r1
   59761:	ldxdw r1, [r2 + 0x0]
   59762:	jne r1, 0x0, +0x2 <.text+0x74a88>
   59763:	stxdw [r6 + 0x8], r3
   59764:	ja +0xf <.text+0x74b00>
   59765:	ldxdw r1, [r2 + 0x18]
   59766:	stxdw [r10 - 0x118], r1
   59767:	ldxdw r1, [r2 + 0x10]
   59768:	stxdw [r10 - 0x120], r1
   59769:	ldxdw r1, [r2 + 0x8]
   59770:	stxdw [r10 - 0x128], r1
   59771:	mov64 r1, r10
   59772:	add64 r1, -0x138
   59773:	mov64 r2, r10
   59774:	add64 r2, -0x128
   59775:	call 0xfc5a
   59776:	ldxdw r1, [r10 - 0x138]
   59777:	jeq r1, 0x0, +0x4 <.text+0x74b10>
   59778:	ldxdw r1, [r10 - 0x130]
   59779:	stxdw [r6 + 0x8], r1
   59780:	stdw [r6 + 0x0], 0x2
   59781:	ja +0x3f <.text+0x74d08>
   59782:	mov64 r1, r10
   59783:	add64 r1, -0x70
   59784:	lddw r2, 0x11c040
   59786:	call 0xf4
   59787:	stdw [r10 - 0x48], 0x0
   59788:	stdw [r10 - 0x50], 0x1
   59789:	stdw [r10 - 0x58], 0x0
   59790:	lddw r1, 0x1221e0
   59792:	stxdw [r10 - 0x18], r1
   59793:	mov64 r1, r10
   59794:	add64 r1, -0x58
   59795:	stxdw [r10 - 0x20], r1
   59796:	stb [r10 - 0x8], 0x3
   59797:	stdw [r10 - 0x10], 0x20
   59798:	stdw [r10 - 0x30], 0x0
   59799:	stdw [r10 - 0x40], 0x0
   59800:	mov64 r2, r10
   59801:	add64 r2, -0x40
   59802:	lddw r1, 0x11c040
   59804:	call 0xbd7
   59805:	jeq r0, 0x0, +0xa <.text+0x74c20>
   59806:	mov64 r3, r10
   59807:	add64 r3, -0x110
   59808:	lddw r1, 0x11c0fa
   59810:	mov64 r2, 0x37
   59811:	lddw r4, 0x122210
   59813:	lddw r5, 0x122230
   59815:	call 0x13c4b
   59816:	ldxdw r1, [r10 - 0x48]
   59817:	stxdw [r10 - 0xc8], r1
   59818:	ldxdw r1, [r10 - 0x50]
   59819:	stxdw [r10 - 0xd0], r1
   59820:	ldxdw r1, [r10 - 0x58]
   59821:	stxdw [r10 - 0xd8], r1
   59822:	ldxdw r1, [r10 - 0x70]
   59823:	stxdw [r10 - 0xf0], r1
   59824:	ldxdw r1, [r10 - 0x68]
   59825:	stxdw [r10 - 0xe8], r1
   59826:	ldxdw r1, [r10 - 0x60]
   59827:	stxdw [r10 - 0xe0], r1
   59828:	lddw r1, 0x11d044
   59830:	stxdw [r10 - 0x108], r1
   59831:	stw [r10 - 0x78], 0x1787
   59832:	stb [r10 - 0xc0], 0x2
   59833:	stw [r10 - 0xf8], 0x43
   59834:	stdw [r10 - 0x100], 0x2b
   59835:	stdw [r10 - 0x110], 0x0
   59836:	mov64 r1, r10
   59837:	add64 r1, -0x148
   59838:	mov64 r2, r10
   59839:	add64 r2, -0x110
   59840:	call 0x11c36
   59841:	ldxdw r1, [r10 - 0x148]
   59842:	ldxdw r2, [r10 - 0x140]
   59843:	stxdw [r6 + 0x8], r2
   59844:	stxdw [r6 + 0x0], r1
   59845:	exit
