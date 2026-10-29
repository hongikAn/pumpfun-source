# Portfolio clipboard failure feedback

When Chromium denies clipboard writes, the portfolio's shared CopyButton caught the failure but returned to the same Copy label with no error feedback. The local profile copy control already distinguishes failure; this fixes the separate portfolio control used for mint and token-account addresses.

The shared button now shows a short failure message and Retry copy, with a polite status region. A successful retry removes the error and announces the copied address kind. The existing button is the containing block for its visually hidden status, preventing that absolute element from escaping a horizontally scrolled table. No original clipboard UX or live-balance parity is claimed.

## Results and limitations

- Actual unchanged-source baseline: Chromium clipboard-write permission was denied and an independent write rejected with NotAllowedError. The real mint Copy click produced no failure status; the focused assertion failed.
- Final: two focused cases passed in 4.5s. Desktop mint and 375px token-account controls show denial feedback, then successfully write the exact existing fixture address after permissions are granted. Failure text disappears and the success status changes. Browser pageerrors are absent; requests remain local GET/HEAD.
- The existing portfolio test fixture is intercepted in the browser. These are synthetic test balances, not observed chain balances. No RPC, backend process, developer API, wallet or production service was contacted.
- The first command was rejected because config.grep was a string; no test ran. Two initial feedback implementations then introduced mobile overflow. Original source measured360/375, first candidate378/375, second413/446/375. The final positioned button measures360/375 before and after denial; desktop1265/1280. Failed runs are preserved and are not presented as passes.
- Production build/typecheck are recorded separately at the submitted commit. No aggregate suite or real screen-reader execution is claimed; the tests check the actual browser flow and status markup.

## Review evidence

| Requested item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | [Denied without feedback](before-denied.png), [actual baseline failure](baseline.log) |
| after-screenshots | [Desktop failure](after-mint-denied.png), [mobile failure](after-account-denied.png), [mobile retry success](after-account-retried.png) |
| walkthrough-video | [Actual mobile denied permission and granted retry](walkthrough.webm) |
| backend-logs | N/A: portfolio reads use the existing browser-intercepted fixture; no backend/RPC request. [Observed local requests](after-account-retry-observations.json). |
| frontend-logs | [Before Next](frontend-before.log), [final Next](frontend-final.log), [final focused result](focused-qualified.log) |
| llm-trajectory | [Public action receipt](ACTION-RECEIPT.md), observable actions/results rather than private reasoning or a verbatim session transcript. |
| domain-artifacts | [Real permission baseline](before-observations.json), [after denial](after-account-denied-observations.json), [actual copied value](after-account-retry-observations.json), [source patch](source.patch), [provenance](provenance.json), [manifest](MANIFEST.json) |

Initial qualification records: [configuration error](baseline-config-error.log), [first candidate](focused-first.log), [before/after width diagnostic](diagnostic.log), [original-source mobile comparison](overflow-baseline.log), [second candidate](focused-final.log). These document a regression found and fixed within this contribution.

## Reproduction

From `app/packages/frontend`, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010` with developer API/RPC configuration disabled. Then run:

```sh
node node_modules/@playwright/test/cli.js test --config visual/portfolio-copy-feedback-20261030/playwright.config.cjs
```

The focused tests reuse the existing portfolio() fixture, set Chromium permission through CDP, verify the real rejected write, grant permissions, and read back the real clipboard value. The config supplies the existing clickwrap-accepted cookie. PNG/video bytes are unchanged. Logs use LF without ANSI sequences/trailing whitespace; raw logs, failed traces, exact baseline test and earlier candidate source remain in the local run directory. No captured JavaScript was executed.
