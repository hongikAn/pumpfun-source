# AMM native inverse transfer fee and its caller

This ordinary Rust change recovers two complete original functions: inverse fee
arithmetic at **0xf2ed0 (776 bytes, 97 instructions)** and `amount_before_fee` at
**0x74b80 (688 bytes)**. The same normal full-build recipe improves from
**733 to 735/785 normalized functions**, and **148 to 159 raw-equal bodies**,
with no normalized or raw losses. The two new normalized matches are exactly
these functions; the eleven raw gains are previously normalized functions,
listed independently in `helper-static.json`. Neither new target is raw equal.

## Source and compiler cause

The parent is the complete source of [PR408](https://github.com/lalalune/pumpfun-source/pull/408).
Only two of its 54 files change, shown in `source.patch` and `proposed/`:

- Add checked inverse arithmetic to the existing native fee dependency, retaining
  its reference ABI. The old root converted to SPL's packed fee representation.
- Copy `amount_before_fee`'s native `Some` payload by value, remove that packed
  conversion, and call the native method. Blank lines preserve error Source67.

Earlier archived native `inverse_match`/`inverse_return` attempts loaded
`maximum_fee` before the guards and emitted only 736 bytes. Reading the original
instructions showed that the struct pointer instead survives wide arithmetic;
the maximum is read in the 100%-fee branch and after division. The new source
reads the field where used. Qualified LLVM IR retains those two late loads;
the backend then emits the complete original 776-byte function.

`controls/early-max-control` is an unchanged extracted qualification control,
not a new retry of that failed source hypothesis. It emits 92 instructions;
`controls/late-max` emits all 97 original instructions after two call masks.
These standalone objects alone are not the recovery result. The full normal
contract build and its repeat establish the reported count, and actual callee
checks below resolve both formerly masked calls.

The native diagnostic rlib differs in metadata under extra LLVM/MIR emission.
Its **entire code object is byte-identical** to the normal rlib's object; both
archives and objects are retained and checked. The root IR-capture build strips
to the normal candidate exactly. Its unstripped output is not a normal repeat.
The root's 24-byte native local copy emits three full-word copies, matching the
original rather than the parent's two words plus a u16.

## Complete calls and data

`helper.py` checks both actual arithmetic callees (`__multi3`, 352 bytes, and
`__udivti3`, 72 bytes), including their raw equality. The 776-byte root has no
relocated data references. `analyze.py` checks the caller's five direct callees,
including the actual new inverse method, and all seven relocated root references:

| Offset | Referent |
|---:|---|
|192,336|Overflow discriminant23|
|240|48-byte vtable, size24/alignment8, all four method bodies|
|384|55-byte Display panic string|
|408|32-byte vtable, size0/alignment1, both method bodies|
|424|Panic Location, including actual filename pointer, length, line and column|
|544|43-byte transfer_fee.rs Source filename; adjacent line67/error6023|

All four incoming calls exist in original, parent and candidate. This is not a
claim that every enclosing caller or transitive data reference matches.

## Normal builds and provenance

The baseline is PR408's retained normal repeat, not a fresh baseline compilation.
Two new normal builds compile the native crate and root and produce identical
complete stripped and unstripped ELFs. SDK, target, flags, lock graph and all
393 external dependency artifacts remain unchanged. Three native dependency
artifacts change because that dependency's source changes. No assembly, binary
patch, IR edit, dummy export, new dependency or flag change is used.

| Artifact | SHA-256 |
|---|---|
|Original AMM|`6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`|
|Parent733 stripped|`f7c4850c6529bf40ffc490753b0a3470aed9b5d630023c8a7df5bd3992c6dee6`|
|Candidate/repeat735 stripped|`785e9078efb31e8ff472075bd079394fba33d564e67371bac7c51461c7686b34`|
|Candidate/repeat735 with symbols|`9b4d6a1aaed8a31e807905d50894c715abd17bb980b3defffec2309c2be2fd57`|

The first generator accidentally renamed one field to `maximum_self` and failed
compilation. Its exact source, command and log are retained in `failed-generator/`;
there is no candidate or measurement for it. The corrected build is the first
measured full candidate. A subsequent metadata-equality assertion was rejected;
code-object qualification above records the narrower verified result.

## Execution on these exact artifacts

New local original/733/735 executions retain actual loaded ELF hashes, signed
transactions, full non-executable message-account pre/post state, ordered logs,
inner CPI and return data. No old receipt was relabeled.

- 680 liquidity + 1,011 buy + 575 sell inputs: **2,266 triples / 6,798 signed
  transactions**. No functional difference or log regression. Existing
  non-compute log differences stay 0/76/88. VMs are reused with restored inputs.
- **216 fresh-VM triples / 648 signed transactions** cover the existing fee,
  epoch, decoder and arithmetic controls. Outcomes remain182success,
  20account-validation rejections,12quote6007rejections and2inverse6023errors.
  Both inverse errors execute the recovered `transfer_fee.rs:67` source path;
  full rollback is verified except for the5,000lamport payer fee. There are
  no state/CPI/return/non-compute-log differences.

The corpus is bounded and partly overlapping. Compute-unit equality, whole-ELF
identity, original source spelling/build provenance and full transitive graph
closure remain unproved. Existing unrelated admin stack diagnostics remain;
Cargo exit0 does not prove all paths safe. Maintained checkpoint metrics are
not promoted by this research-source packet.

## Audit and replay

```sh
python -I -B research/amm-native-inverse-fee-recovery/verify.py
python research/amm-native-inverse-fee-recovery/materialize.py /tmp/inverse-source
python research/amm-native-inverse-fee-recovery/rebuild.py --source /tmp/inverse-source --sdk /path/to/v144/sdk --cargo-home /path/to/cargo-home --target-dir /path/to/target --output /tmp/inverse-build
python -I -B research/amm-native-inverse-fee-recovery/focused.py --control /path/to/733.so --candidate /tmp/inverse-build/candidate.so --output /tmp/inverse-focused/report.json
```

The verifier audits saved evidence. Rebuild uses the captured offline/locked
Linux Docker recipe, requires local SDK/cache, disables networking and checks
both complete output hashes. `builds/`, `compiler/`, `runtime/commands.json`
and `controllers/` retain actual commands and original local paths. Originals,
captured fixtures and previously sealed packets are unchanged. Public PR409's
`curve/fees.rs` source-coordinate patch is a separate scope.
