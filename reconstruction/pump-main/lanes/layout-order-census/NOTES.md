# Lane layout-order-census: function order and data layout, preparing the raw step

Baseline: origin/main d2cb88d (`$BASE/unstripped.so`, 1019 normalized / 188 raw, 831 normalized-only).
Analysis only so far: no maintained source changes. Tools in `tools/` (paths point at this lane's
`$OUT=~/.cache/pumpfun-reconstruction/lanes/layout-order-census`; they reuse the harness `score.py` masking).

| file | what |
| --- | --- |
| `tools/census.py`, `tools/refine.py` | pair all 1035 original windows with candidate units (normalized class, then callee-consistency and pointee-bytes refinement for the 62 ambiguous classes; the 16 unmatched pinned by name). Result: 8218 call operands point at the paired callee, 1226 identical immediates, 6 inconsistent (ambiguity residue). |
| `tools/predict.py` | layout model: recompute every unit address for a hypothetical order/size set and re-check every masked operand of the 1019 matched windows (relative call distance, absolute `.text` lddw, data lddw). Reproduces the official 188 raw on the baseline exactly. |
| `tools/breaks.py` | adjacent-pair order breaks, classified. Output: `order-breaks-baseline.txt`. |
| `tools/rodiff.py` | byte alignment of `.rodata`. Output: `rodata-diff-baseline.txt`. |
| `tools/xbuild.py`, `tools/rustc-linuxvv`, `tools/rustc-linux-v2` | experiment-only builder (crate rename, Linux-host cargo metadata shims). Never a proposal recipe. |
| `predict-baseline.txt` | all model scenarios below. |

## 1. How the compiler orders functions (verified on our build)

- Main crate = one CGU (codegen-units=1). Inside it rustc emits mono items sorted by
  `(local def index or None, symbol name)`:
  - **U block** (0x120..0x149e0, 142 units): instances of *upstream* generic items
    (`anchor_lang`, `core`, `alloc`, `borsh` ...) sorted by mangled name, hence by the legacy
    `17h<hash>` suffix within one generic (`Account<T>::try_from` x9, `Error::with_values` x6, ...).
    That hash mixes in the instantiating crate's StableCrateId (crate name plus Cargo `-C metadata`)
    and the def-path hashes of the type arguments.
  - **L block** (0x149e0..0x17c930, 483 units): local items in def-index order. That is source order
    with `mod` files expanded in place, and derive/attribute-macro output (`Accounts`
    `try_accounts`/`exit`, `Event::data`) in a second pass after all hand-written items.
    Closures of one function are sorted by hash.
- **D block** (after `__rust_alloc_error_handler`, 410 units): dependency objects in link order.
  Inside each one the order is again by symbol hash, fixed by the dependency's own metadata.

## 2. Order census (original vs baseline)

- 291 adjacent-pair breaks: 166 main-local (def order), 62 main same-generic (hash), 31 main
  upstream, 14+13+2 dependency, 3 mixed. LIS of the paired order = 854/1035.
- Hash groups with 2 or more members whose internal order differs from the original:
  U 16/18, L 1/16 (closures), D 6/27.
- Two units sit in a different block in the original:
  - `0x2bc0` = our local `account_name::with_owned_name`. The original has it in the U block,
    between the `Error::with_account_name` instances. It is the upstream generic
    `Error::with_account_name::<&String>` (same body), not a local helper.
  - `0x17c0f0` = `migrate_v2::required_quote_account_len`. The original has it after
    `pump_token_ext`, so it was compiled in another crate or CGU, not the root's local block.
- Structural facts in the original's local order:
  1. The six unmatched v2/v3 handlers (`0x13b9b8` buy_v2, `0x13f630` buy_exact_quote_in_v2,
     `0x144508` sell_v2, `0x147ba0` buy_v3, `0x1489f8` buy_exact_quote_v3, `0x14a8a8` sell_v3)
     lie inside the `#[program]` module run, between program fns `create` (`0x138b20`) and `buy`
     (`0x14c038`), in instruction order. In the original they *are* the `#[program]` fns: the
     handler body lives in, or is inlined into, the program fn. In our build these are module
     functions (`buy_v2::buy_handler` at 0x16c88 ...) and the program wrappers are inlined into the
     dispatchers. Their closures stay at the module site (0x16bb8 ...).
  2. The original has one contiguous run of payment/transfer helpers (0x8b818..0x95610:
     `transfer_native*`, `transfer_*_tokens*`, `transfer_*_out` from user_quote_payments, migrate,
     legacy_buy, collect_v2, multi_hop_curve, buy_v2, sell_v2). Our build spreads them over 9
     modules. In the original they shared one def-order position, which points to shared, probably
     generic, helpers.
  3. Otherwise the module sequence is the same as ours, in both the hand-written pass and the
     derive pass. The original module runs are listed in `module-runs-baseline.txt`.
- 8 units exist only in our build (12,824 B): `multi_hop_curve::{add,sub,div,move_lamports}`, three
  `multi_hop_curve::route_event` instances, and `anchor_lang::Lamports::add_lamports`.
  The original inlines them. They are the 0xa10 `.text` surplus beyond the 16 size deltas
  (0x1b62e0 vs 0x1b58d0).

## 3. Data layout census

- `.data.rel.ro` has the same size (0x2870). 1328 of 1453 differing data.rel.ro pointers have the
  same offset; the rest are swapped vtable/entry pairs. `.rodata` is 40 B smaller (0x7cf7 vs 0x7d1f).
  Its base moves with `.text` size (+0xa10), so every one of 593 data-pointer windows fails today.
- `.rodata` byte alignment (`rodata-diff-baseline.txt`): 31,379 of 32,031 bytes align. The
  differences are (a) order of string literals (`programs/pump/src/*.rs` paths, account-name
  seeds, error messages) and 32-byte Pubkey constants, all of which follow first-use order in
  function order; (b) a few literals present only on one side, e.g. our second
  `called \`Result::unwrap()\` on an \`Err\` value` and 5 zero bytes.

## 4. Raw prediction (model, `predict-baseline.txt`)

| scenario | raw of 1019 |
| --- | ---: |
| S0 baseline as built (model check) | **188** (= official) |
| S2b all 16 matched in size+code, 8 extras gone, data identical, **our order** | 286 |
| ... + original order inside L only | 646 |
| ... + original order inside U+L | 965 |
| S3 full original order | 1014 (5 residual = pairing ambiguity) |
| S7c original order except U hash groups kept in our hash order | 759 |
| S7d original order except L closure groups in our hash order | 1006 |
| C1 today's sizes/data + original L order | 272 |
| C2 today + original U order | 191 |
| C4 today + full original order | 293 |

So once the 16 match, **order rather than size is the main obstacle** (733 of 1019 windows fail on
call distance). The U block's hash order alone costs about 255 windows, and only the original
crate identity can restore it.

## 5. Experiments (ledger)

| attempt | result |
| --- | --- |
| `730dc227` model census | analyzed (above) |
| `5785b0ba` Linux-host cargo metadata (`rustc -vV` host shim, experiment only) | 1019/183 (raw +2 −7). The shim reproduces the AMM metadata map's Linux values (typenum `48277d0b39ab7f75`, cfg_if `4938d2d8ea051e56`). U-order agreement unchanged (3/18 groups). |
| `8f9651c8` crate renamed `pump` (+ `#[program] mod pump`), mac metadata | U groups 2/18, pairwise 126/231 (chance) |
| crate `pump` + Linux `-vV` shim | 3/18, 123/231 |
| crate `pump` + speed-lane shim v2 (Linux `-vV` + host `--print=cfg` + cpufeatures libc) | 2/18, 133/231 |

The U-block hash order depends on the root StableCrateId and on every upstream crate's metadata
(anchor-lang features, the Cargo.lock graph, RUSTFLAGS in cargo 1.79's metadata, the workspace path).
"pump/0.1.0 on Linux" does not reproduce it. With no original Cargo inputs, this part of raw order
cannot be reached through `programs/pump` source. The other programs reached whole-ELF identity
through ordered link scripts (`programs/{mayhem,pump-fees}/build_exact.py`, AMM `ordered-native.ld`).

## 6. What a source change could still do

- Order levers that keep line numbers: (1) permute `mod` lines in lib.rs lines 1-63. Module order
  already matches, so expect no gain. (2) Put each v2/v3 handler body in its `#[program]` fn, or
  make it inline into a non-inlined program fn. That needs code-level work in the unmatched-handler
  lanes; on its own it gives +0 raw in the model (C5) until the rest of L order matches.
  (3) Use `error.with_account_name(name)` instead of `account_name::with_owned_name`. That moves 0x2bc0 into the U block,
  where the original has it.
- Raw gains before the 16 match are limited to call-only windows. The model ceiling with today's
  sizes and data is 293 (full original order), 272 with L order alone.

### Source trial: upstream generic for 0x2bc0 (`6fc0151b`, rejected)
Replacing `account_name::with_owned_name(error, &name)` with `error.with_account_name(&name)` gives
1018/188 against the main HEAD control's 1020/188. It loses 0x2bc0 and 0x6fef8 because the generic
instance gets inlined into `set_reserved_fee_recipients`. In the original the instance is outlined and
sits in the U block, so the original call site must look different (for example, a second caller keeps
it out of line).
