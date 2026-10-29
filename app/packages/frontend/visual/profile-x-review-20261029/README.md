# PR #1181: review evidence

Recorded xUsername was present in the existing synthetic profile but had no link. The maintained component follows the captured trim / one-leading-@ / encoded path / omission behavior. Local placement is not original visual parity.

The source head is `ec972afcfd9623633096aa2775d49d2c9f021264`. The screenshots/video recorded at `capture.json` timestamps are **fresh review-response captures**, not retroactively claimed outputs of the earlier focused run. `before.png` is the unedited screenshot retained from that earlier baseline failure at `f634ae0aaaf719ee51507ef7c971d2a1d4f5e026`. Evidence-only follow-up commits do not change product source.

| Requested evidence | Concrete artifact or specific applicability boundary |
| --- | --- |
| before-screenshots | [Original baseline screenshot](before.png), [failing assertion log](baseline.log) |
| after-screenshots | [Recorded link](after-profile.png), [intercepted keyboard popup](after-keyboard-popup.png), [missing handle](after-missing-handle.png) |
| walkthrough-video | [Fresh Chromium recording](walkthrough.webm), [ordered observable steps](capture.json) |
| backend-logs | Specific N/A: no backend service or developer-API transport runs for this feature. The Next server reads existing hash-bound users/posts/following files. Those unchanged input hashes are in provenance.json; browser requests and the locally intercepted X target are recorded. No live X response is used. |
| frontend-logs | [Fresh Next server log](frontend-server.log), [capture log](capture.log), [browser request log](browser-requests.json), [original focused browser log](focused-browser.log) |
| llm-trajectory | [Retrospective public action receipt](ACTION-RECEIPT.md). This records observable commands, decisions and results; it is not a verbatim LLM trace. Private reasoning and unrelated session transcripts are not published. |
| domain-artifacts | [Original factory/range hashes](source-contract.json), [source diff](source-diff.patch.gz), [source and seed hashes](provenance.json), [rendering controls](focused-rendering.log). These establish the bounded link behavior, not the entire original profile. |

Original focused verification: 3 rendering controls and 8 profile browser cases passed. Fresh capture: Alice link, keyboard activation into a locally fulfilled X popup, and missing-handle omission. Build and typecheck passed on the stated source head: [receipt](build-typecheck.json), [build log](build.log), [typecheck log](typecheck.log). The review capture had zero unexpected browser requests and zero browser console/page errors. Existing CSS build warnings, if present, remain in the server log.

## Reproduce the fresh capture

Use the existing workspace dependencies and the exact source head above. In `app/packages/frontend`, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3011`. Set `PLAYWRIGHT_MODULE` to that workspace's `node_modules/@playwright/test` absolute directory and `WORKTREE` to the checkout root, then run `node capture.cjs 1181 <new-output-directory>`. The script checks the source head and blocks unexpected browser requests.

No backend server is started. The X popup is fulfilled by Playwright with explicit local test HTML; no X network request is sent. The video records the main page; the popup screenshot separately shows the intercepted target.

The SHA-256 manifest binds these retained files; it is an integrity index, not independent execution attestation. No full-suite, live service or original visual-parity pass is claimed.

Published text copies use LF and omit trailing display whitespace. Original local logs remain retained; original/published hashes and the explicit transformation are recorded in provenance.json. The source diff is compressed without changing its bytes.
