# Mobile drawer Create menu placement

At the unchanged base in provenance.json, the drawer reused the desktop right-side popup placement. At 320px the menu spanned x278..454, clipping most of the Create coin label. The fix selects the existing bottom-start placement for the existing mobile context only. Desktop collapsed and expanded menus keep right-start.

This is a local navigation fix grounded in SHELL-EVIDENCE.md and the maintained accessible dropdown. Captured closed-shell markup does not establish an original open-popup layout; no original visual parity or milestone completion is claimed. Captures, seeds, SDK and dependencies are unchanged.

Validation: one representative baseline test fails on viewport bounds. On the fixed source, the first four-test run passed three tests and timed out on the first 320px /create transition after its bounds passed. The first RSC response took 4.50 seconds; the initial five-second URL wait was increased to fifteen seconds. Product code did not change between those runs. The final four tests pass (9.4s), covering 320/375/767px menu bounds and actual pointer navigation, drawer dismissal after navigation, plus collapsed/expanded desktop placement and Escape focus restoration. This is a focused suite, not an aggregate suite result. Root production build/typecheck are coordinated separately and will be reported against their actual commit.

| Requested review item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | before-320.png and baseline.log; unchanged product source at the recorded base. |
| after-screenshots | after-320.png, after-create-320.png, after-375.png, after-767.png and both after-desktop images. |
| walkthrough-video | walkthrough-320.webm records the final real Chromium 320px flow from Home through drawer/Create to the offline draft. |
| backend-logs | N/A: no backend service or developer API is used. Home reads the existing local seed on the Next server; Create is an offline draft. browser-requests.json and both Next logs show the local boundary. |
| frontend-logs | frontend-before.log, frontend-after.log, baseline.log, focused-after.log and focused-final.log. The initial candidate timeout is retained. |
| llm-trajectory | ACTION-RECEIPT.md records public observable actions and outcomes; explicitly not a verbatim LLM/private reasoning transcript. |
| domain-artifacts | before/after geometry JSON, source.patch and provenance.json with exact source/test hashes and finite scope. |

Published log copies use disclosed LF/trailing-whitespace normalization; raw originals and the first failed candidate trace/video remain retained locally. The final video and PNG bytes are unchanged. The after capture is a local authored interface, not a live upstream capture. The failure and success were observed on the same Node/Next/Chromium dependency installation; no package install was performed.
