# Lane macro-idioms (AMM sell cashback)

Approach: vary the Anchor macro and `?` spellings (require!/err!/error!, map_err/Into/From, ? vs match,
ok_or vs ok_or_else) site by site, keeping every error-macro line number the same. 41 scored builds.

## Best
No size-9024 improvement. Best structural candidates match existing classes:
- b2 class (owner `!=` on 444 + `if ata.is_writable == false { return err!(..) }` on 467): 169/291, size 9040 (`best_sell.rs`).
- e0f+ok (`== false` else-if chain + `} else { Ok(()) }?;`): 134/316, size 9008 (key 7bb5400442fa26d8).

## Findings
- Line 467: 9 idioms collapse into exactly 2 output classes. Plain bool test (require!, `if x {} else {..}`,
  `match x {..}` either order, `let true = x else {..}`, `if let false = x`) gives the owner_ne image.
  Anything that builds a comparison (`== false`, `false == x`, `matches!(x,false)`, `x ^ true`, `!x == true`) gives b2.
- Cross product {b2, e0, e0f heads} x {`?`, `else {Ok(())}?`, `else {}`} x {464 require!, `!=`}: 18 builds,
  only the 4-5 classes that were already known. The 464 spelling and an empty `else {}` never change the output.
- Macro alias forms produce the same bytes (they expand to the same tokens, or the conversion is erased):
  `err!(E)` vs `Err(error!(E))`, `require!(c,E)` vs `if !(c) {return err!(E)}`,
  `Err::<(),_>(error!(E))?`, `.map_err(Error::from)?` at 481, `match {Ok(())=>{},Err(e)=>return Err(e)}` at 489/503/504.
- These are NOT erased and make things worse: `if let Err(e) = x { return Err(e); }` (489/503/504),
  `validate_pool_v2(..)` as a tail expression, an explicit match at 481, and any explicit ProgramError conversion
  at 397/413/419/424/425/445 (dist 157-426). So the original used plain `?` at every conversion site.

## Dead ends (do not retry)
Every macro alias and identity-conversion spelling listed above; explicit conversions at the ProgramError sites.

## Next ideas
Source spelling is now pinned down to the bool/comparison form and the if/else-if/value structure; macro forms are exhausted.
What remains is block placement (MachineBlockPlacement chains for err467 and the shared return join), which belongs to
the IR and placement lanes. Possibly worth trying: structure-level changes downstream of tfu (scoping `ata`/`accumulator` drops),
since they change the return-join predecessors.

Tools: combo.py (head/tail/key generator), mk.py (line replacer), runq.py (2-slot queue), blocks.py (IR block-order summary).
