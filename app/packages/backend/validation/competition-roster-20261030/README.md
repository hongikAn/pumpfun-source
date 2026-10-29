# Person competition roster before start

A registration-phase person entry returned `memberCount: 1` and a synthesized member with today's profile wallet before the roster snapshot at `startsAt`. The captured client contract requires `0` and `[]`. The supplied local lifecycle now gates that automatic member: `upcoming`/`registration` have no person roster, while `live`/`ended` retain it.

The start boundary is separate from the first board build: live but unbuilt entries keep their roster. Built live/final, walletless, struck, and supplied group-member controls pass. Registered entry and participant counts stay unchanged. The deterministic local model takes phase from operator input; it does not derive production time, create snapshots, or establish historical wallet correctness. No feature-coverage/API-parity milestone is claimed.

| Evidence item | Artifact or applicability |
| --- | --- |
| Before screenshots | N/A: backend JSON projection only. Actual HTTP-injection response assertion/diff is in `before.log`; no UI was changed or visually tested. |
| After screenshots | N/A for the same scope; `after.log` checks corrected HTTP responses and schema. |
| Walkthrough video | N/A: no interactive/browser change or recording; focused commands below reproduce the flow. |
| Backend logs | `before.log`:7 tests,5 pass,2 fail on base source. `after.log`:7/7 pass. `focused.log`:47/47 pass, including the7 new cases. |
| Frontend logs | N/A: no frontend code/server/test was run for this backend projection. |
| LLM trajectory | `action-receipt.json` records actual commands, brief decisions and outcomes retrospectively. Full model transcript/private reasoning was not retained; this is not a complete model trajectory. |
| Domain artifacts | `source-proof.json` pins the inert raw factory, original contract declarations and source hashes; regression test, `COMPETITIONS.md` assumption51, and `MANIFEST.json` provide implementation evidence. |

Run from `app/packages/backend`:

```sh
node --import tsx --test --test-reporter=tap test/competition-roster.test.ts
node --import tsx --test --test-reporter=tap test/competitions.test.ts test/competition-roster.test.ts
```

Before used Node's default reporter; after uses TAP. Logs are byte-for-byte command output. Shared build/typecheck is recorded separately for the final commit; no full-suite or hosted-CI success is implied.
