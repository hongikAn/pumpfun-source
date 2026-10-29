# PR #1219: review evidence

The local newest feed offered a ranked first-page link after a cursor error. Recovery now retains valid newest ordering; unknown/repeated views still fall back to ranked. This is the local integration contract, not production cursor or original error-policy recovery.

The source head is `b5190a6e88b07e18ffe6bd8b8a92fcf00b12790d`. The screenshots/video recorded at `capture.json` timestamps are **fresh review-response captures**, not retroactively claimed outputs of the earlier focused run. `before.png` is the unedited screenshot retained from that earlier baseline failure at `f45853cffebd5449266551667793201c822f641b`. Evidence-only follow-up commits do not change product source.

| Requested evidence | Concrete artifact or specific applicability boundary |
| --- | --- |
| before-screenshots | [Original baseline screenshot](before.png), [failing assertion log](baseline.log) |
| after-screenshots | [Rejected cursor](after-backend-rejected.png), [recovered newest page](after-backend-rejected-recovered.png), [malformed cursor](after-malformed.png), [malformed recovery](after-malformed-recovered.png) |
| walkthrough-video | [Fresh Chromium recording](walkthrough.webm), [ordered observable steps](capture.json) |
| backend-logs | [Existing fixture-server output](backend-server.log) and [actual request record](backend-requests.json). This is the unchanged loopback fixture server, not production backend traffic or a newly implemented backend. |
| frontend-logs | [Fresh Next server log](frontend-server.log), [capture log](capture.log), [browser request log](browser-requests.json), [original focused browser log](focused-browser.log) |
| llm-trajectory | [Retrospective public action receipt](ACTION-RECEIPT.md). This records observable commands, decisions and results; it is not a verbatim LLM trace. Private reasoning and unrelated session transcripts are not published. |
| domain-artifacts | [Exact recovery URLs and states](capture.json), [backend requests](backend-requests.json), [source diff](source-diff.patch.gz), [source and unchanged fixture hashes](provenance.json). No production compatibility claim is added. |

Original focused verification: all 12 native-feed browser cases passed. Fresh capture: backend-rejected and malformed newest cursor errors, keyboard recovery to the first newest page, and exact local newest/count requests. Build and typecheck passed on the stated source head: [receipt](build-typecheck.json), [build log](build.log), [typecheck log](typecheck.log). The review capture had zero unexpected browser requests and zero browser console/page errors. Existing CSS build warnings, if present, remain in the server log.

## Reproduce the fresh capture

Use the existing workspace dependencies and the exact source head above. In `app/packages/frontend`, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3011`. Set `PLAYWRIGHT_MODULE` to that workspace's `node_modules/@playwright/test` absolute directory and `WORKTREE` to the checkout root, then run `node capture.cjs 1219 <new-output-directory>`. The script checks the source head and blocks unexpected browser requests.

Enable `PUMP_LOCAL_HOME_FEED=enabled` for Next and start `node tests/support/native-feed-server.mjs` on 127.0.0.1:3001. The capture uses only its existing local __control / __requests test endpoints.

The SHA-256 manifest binds these retained files; it is an integrity index, not independent execution attestation. No full-suite, live service or original visual-parity pass is claimed.

Published text copies use LF and omit trailing display whitespace. Original local logs remain retained; original/published hashes and the explicit transformation are recorded in provenance.json. The source diff is compressed without changing its bytes.
