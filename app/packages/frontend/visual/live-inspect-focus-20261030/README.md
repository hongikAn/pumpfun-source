# Reveal inspected archived metadata

On a narrow viewport, Live places the nonmodal metadata panel above the card grid. Inspect used `scroll:false` and left focus on a distant card, so a successful selection could show no detail in the viewport. The unchanged-source 375px browser reproduced this on the seventh existing archived card: heading top -3117px and viewport intersection zero.

Explicit Inspect now requests focus on that record's metadata heading after the URL commits. It scrolls only when the heading is outside the viewport. Other navigation and popstate cancel the request, and direct URL loading does not create one. Escape and Close retain the existing card-focus return. This is a local accessibility/interaction correction; the original mobile detail behavior remains unknown. All 42 captured records and the existing archive provenance stay unchanged.

Validation: baseline **1 failed** at the viewport assertion. Candidate **3 passed (7.0s)**: 375px/1280px select and reselect, both dismissal methods returning to the card, plus direct URL focus/scroll control. Mobile heading top is 391px after the fix; desktop heading is visible at 116px. No backend, current stream, media or production calls were introduced.

| Review evidence | Actual artifact or specific N/A |
| --- | --- |
| Before screenshot | [before-mobile.png](before-mobile.png) |
| After screenshot | [after-mobile.png](after-mobile.png), [desktop](after-desktop.png) |
| Walkthrough video | [walkthrough.webm](walkthrough.webm), actual local browser actions |
| Backend logs | N/A: the mounted page reads existing hash-validated local capture data; this correction makes no backend request. Browser request observations are in before/after JSON. |
| Frontend logs | [frontend.log](frontend.log), [baseline.log](baseline.log), [focused.log](focused.log) |
| LLM trajectory | [ACTION-RECEIPT.md](ACTION-RECEIPT.md), observable summary, not private reasoning or a verbatim transcript |
| Domain artifacts | Before/after geometry JSON, inert baseline gzip files, [source.patch](source.patch), [file-hashes.json](file-hashes.json), [MANIFEST.json](MANIFEST.json) |

Root build and typecheck both passed on `ea4b0030f23e40f04f306fd0c0463fc77510dc2c`: [qualification](root-qualification.json), [build log](root-build.log.gz), [typecheck log](root-typecheck.log.gz). The later evidence-only head preserves identical executable source/tests. No original playback, visual parity, real screen-reader behavior or full-suite result is claimed.
