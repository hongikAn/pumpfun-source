# Lane mir-codegen-order (AMM sell swarm)

Approach: work out how rustc/LLVM orders the cashback blocks, then find source shapes that reproduce the original layout.

## Result: IR block-order oracle (normalized dist 91 -> 10, no source change yet)
- `-C save-temps -Zfewer-names=yes` gives the optimized module bitcode. Running `llc -O3 -mtriple=sbf -mattr=+store-imm,+jmp-ext -relocation-model=pic -function-sections -data-sections` on it reproduces rustc's cashback bytes exactly.
- `tools/reorder.py NAME 'X>Y' ...` moves optimized-IR block X after Y, runs llc and diffs the result against the original window with lddw/call immediates masked (`tools/norm.py`). `sweep.sh` and `pairsweep.sh` brute-force the moves.
- Moving `%192>%226` fixes Diff1 (borrow `jeq +1; ja`). Moving `%441>%529` fixes the ATA `jne +1; ja +49` and the create/try_from placement. Adding `%499>%619` gives dist 10. Only the placement of the shared tail `ldxdw r6,[r10-1304]; ja` is still wrong.
- Conclusion: at ISel the original had an extra block that is not a successor right after the borrow block AND right after the ATA data_is_empty block. That block needs phis/copies: a block holding only lifetime.end is deleted by CodeGenPrepare (oracle split test, dist unchanged).
- Mechanism: the line-444 and line-467 require! error chains are codegenned between the creation and the codegen of those blocks, so whatever those chains reference first is laid out next.

## Dead ends
- save-temps or --emit IR alone keeps value names: only rodata addresses differ, code is unchanged.
- A lifetime.end-only edge-split block after the borrow/ATA blocks has no effect.
