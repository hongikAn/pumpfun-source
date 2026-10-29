# Restore the original claim-v2 empty-account boundary

The original `claim_cashback_v2` checks whether the associated accumulator token account is empty before borrowing and deserializing its data. The maintained source borrows first and checks the resulting slice. This one-line change at `token_incentives/claim_token_incentives.rs:311` restores the original `AccountInfo::data_is_empty` call and the empty branch's early exit. All 350 physical source lines, native arithmetic, validation order and nonempty deserialization remain in place.

This is a small partial fidelity improvement. The aligned diagnostic decreases by only one slot; the missing original call is the concrete recovery. No whole function or ELF becomes equal, and the size gap worsens.

| Measurement | Selected parent | Candidate |
|---|---:|---:|
| Function bytes (original 8,832) | 8,464 | 8,448 |
| Absolute size difference | 368 | 384 |
| Aligned differing 8-byte slots | 1,583 | 1,582 |
| Normalized / raw original windows | 1,019 / 183 | 1,019 / 183 |
| Lost or gained complete memberships | 0 | 0 |
| Target `data_is_empty` calls | 0 | 1 |

The 1,035-window denominator is the historical selected Pump inventory pinned at SHA256 `fb2c0a47514567d65eb45c1e268dacd5291e4659bb7dceb575a767dc20bcaff8`. Current main no longer tracks that file, so its exact bytes are retained at `tools/functions.tsv.gz`; verification supplies those bytes and the pinned original ELF to the unchanged census in a temporary read root.

The normalizer and SequenceMatcher alignment are unchanged. Moved blocks can count as deletions and insertions, so the slot metric is diagnostic rather than a semantic-distance measure.

## Original branch and receiver

Original function `0x77940` loads the account handle from `[context.accounts + 0x18]` at offset `+0x560`, calls `data_is_empty` at `+0x568`, and sends an empty result from `+0x578` to `+0x1420`: the existing `No cashback to claim` notice and `Ok` return. The nonempty path reloads that same handle at `+0x580`, calls `try_borrow_data` at `+0x598`, then deserializes the token account at `+0x618`.

The selected parent loads the same field at `+0x9c0`, borrows at `+0x9d8`, and then checks the slice length at `+0xa20`. The 5,992-byte `ClaimCashbackV2::try_accounts` body matches the original after narrow normalization, supporting the account-layout correspondence. The candidate restores `data_is_empty` at `+0x9c8` before the borrow at `+0x9f0`.

The 104-byte accessor, its 152-byte immediate panic callee, and the 5,992-byte account constructor have identical complete narrow normalized bodies across the three images. Internal direct calls increase from 62 to 63 (raw CALL opcodes 64 to 65); the only added call identity is `data_is_empty`. All 28 common callees and their 257 references remain mapped consistently. Among 1,069 named functions, only this claim handler changes its narrow normalized body. Parent/candidate `.rodata`, 27 target LDDW references and all 590 data relocation words remain consistent, with no unresolved references.

`data_is_empty` uses the original infallible borrow API. A conflicting outstanding mutable RefCell borrow could therefore fail differently from the parent's fallible-first form; no equivalence claim is made for that artificial condition. The eight retained handler fixtures cover ordinary parsed accounts without such a conflicting borrow. There are no new unsafe operations or account mutations.

## Explicit selected compiler cohort

The parent is the previously qualified B13 candidate, symbols SHA256 `b79428215bac7c4cb487681ea3a5cdad84197fcaa04142a0e68f4a4706008898`, from pending PR #1164 head `8e54625df475761af3f34ca046fd27694c5bca69`. Eight parent source/build members are included byte for byte. Verification is self-contained and does not require that PR's research folder to exist on main.

Of the selected 66 compiler inputs, 61 equal main `f634ae0aaaf719ee51507ef7c971d2a1d4f5e026`. Three Cargo files retain the selected D037 recipe. Two Rust files contain the pending token/sell helper recovery from #1164. This independent PR changes neither of those files; it changes only the claim source line. This is not a checkout-wide main build, and the Linux 183 raw matches are not the separate native macOS 188 cohort.

One new normal root compilation used the unchanged v1.44 offline/locked recipe and physical-source wrapper, with all inputs unchanged. Parent compilation is reused, not rerun. No repeat build, IR edit, assembly edit or ELF patch is claimed.

Candidate symbols SHA256: `de53785cbf8a02ff962eebd6c365db7a85b7755d5c09d1d531c650f6ca4f2975`.
Candidate stripped SHA256: `10252ecd3dd7054efb12ef905ad40d972a477be85bcb320d46052371a80a302d`.

## Eight unchanged runtime fixtures

Exactly eight existing cases from `scripts/pump_cashback_differential.py` were selected without changing their definitions. The captured upgradeable loader ran original, selected parent and candidate images: 24 signed transaction records, all successful.

- Native, Token and Token-2022 paid claims: three cases.
- Native rent-minimum balance and nonempty Token/Token-2022 accounts with zero token balance: three cases.
- Token and Token-2022 associated accumulator accounts with zero-length data: two cases.

Each image produces three paid claims and five `No cashback to claim` exits. Account state, error, event/CPI bytes, return data, signed wire and ordered logs agree, excluding only complete runtime compute-meter lines. Both empty and nonempty token branches are exercised. No runtime behavior improvement is claimed.

The executed loader is the previously qualified version pinned at `8d51ba5feab9e74f67fb80f5827222308d45a36022151bc77ad076c401f65067`. Current main adds a cache for the same captured image construction; the exact reviewed diff is retained in `provenance/executed-loader-version.json`. Execution is not relabeled as using the newer script. The finite verifier reconstructs the actual loader image rather than trusting that equivalence summary.

The producer reuses the existing fixture and captured loader; observation hooks record actual image hashes, signed transactions, prestates, loader allocations and raw metadata without changing accounts. The execution receipt binds 29 input records (27 byte joins and two pinned host-file fingerprints), three output files and one actual command. These checks establish finite retained consistency, not independent execution attestation or independent post-state observation.

## Verification

With Python 3.12 and solders 0.27.1, from the repository root:

```sh
python -B research/pump-claim-cashback-v2-20261029/verify.py --repo-root .
python -B research/pump-claim-cashback-v2-20261029/test_verify.py --repo-root .
python -B research/pump-claim-cashback-v2-20261029/audit_refs.py --repo-root .
```

The finite verifier checks source/build/runtime correspondence, the one maintained source line and the complete membership census. The independent audit resolves the original helper and account boundary. Resealed controls exercise evidence bindings. Verification rejects optimized Python and launches no compiler or VM. Remaining function mismatches, original whole-data identity and recursive transitive identity remain outside this claim.
