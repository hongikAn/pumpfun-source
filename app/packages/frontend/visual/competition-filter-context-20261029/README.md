# Competition filter context regression

The local list searches competition title/description/slug; detail searches participant identity. Carrying `q=browser-test` from the list into detail hid the existing `synthetic-entrant` even though the response contained it. Back from a participant filter similarly hid the competition list. The existing local contract says search applies to currently loaded fields; this fix clears that old collection's filter at each explicit context switch. Browser Back/Forward still restores prior URL states. No original website search-policy or live ranking claim is added.

Base: `ef400863f4e476b2eaaab0866c0b1187d8060abc`. Only two source statements change. Existing test fixtures are an unchanged prefix; two focused regressions are appended. Source/input hashes and exact scope are in [source-contract.json](source-contract.json).

| Requested evidence | Artifact or specific N/A |
| --- | --- |
| before-screenshots | [Filtered list](before-filtered-list.png), [missing participants after opening](before.png), [actual failed assertion](baseline.log) |
| after-screenshots | [Participants visible with clear filter](after-detail.png), [competition list visible after returning](after-list.png) |
| walkthrough-video | [Open detail and browser history](walkthrough-open.webm), [Back from filtered participant detail](walkthrough-back.webm) |
| backend-logs | Specific N/A: these UI tests intercept the local `/api/leaderboard` request using the existing explicit synthetic fixture. No backend service, credential or production request is used. This does not claim backend integration. |
| frontend-logs | [Baseline Next log](frontend-before.log), [corrected Next log](frontend-after.log), [four passing focused cases](focused-after.log) |
| llm-trajectory | [Retrospective public action receipt](ACTION-RECEIPT.md); observable actions/results, not a verbatim LLM transcript or private reasoning. |
| domain-artifacts | [Local field scopes, source hashes and unchanged fixture proof](source-contract.json), plus the maintained regression tests. |

## Reproduce

Use the repository's existing Playwright dependency and `tests/leaderboard.spec.ts`. Start Next from `app/packages/frontend` with `PUMPFUN_DEVELOPER_API_KEY` empty: `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`. Use a local Playwright config with testDir pointing to that tests directory, baseURL `http://127.0.0.1:3010`, one Chromium worker, and the existing `clickwrap_accepted=true` test cookie. The focused grep is:

```text
competition title filters|participant filters|competition status and ranked|category navigation survives
```

Baseline ran only `competition title filters` and failed at the missing actual participant list. After correction, the four selected cases passed in 9.7 seconds. Both new regressions block non-loopback or mutating browser requests. Their request attachments were supplied to the line reporter in memory, not retained as standalone files; no separate backend request log is claimed. The video/screens are original Playwright outputs from these runs, not later reenactments. Published text logs normalize LF/trailing display whitespace; raw originals remain retained and both hashes are recorded.

No aggregate test suite or production parity result is claimed. Existing build/typecheck are coordinated separately at the candidate commit.
