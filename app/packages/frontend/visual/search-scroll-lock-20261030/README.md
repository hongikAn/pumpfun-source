# Search modal scroll ownership

On the unchanged source, a 500px wheel action on the search modal backdrop moves the underlying reference document from scrollY0 to500 while the modal remains open. Native showModal makes the background inert but does not prevent this scrolling. The Search dialog now acquires the existing shared body lock while its observed native open state is true and releases its own reference on close or cleanup. The five-line source addition does not change query navigation, the source-bound shortcut effect or the shared lock implementation.

This is a local modal behavior correction. It does not claim original search-dialog visual parity, live search compatibility or a complete feature milestone. Captured documents, seeds, dependencies and SDK bytes remain unchanged. Tests use the existing hash-bound local alice profile; no account, wallet or backend service is added.

Actual validation: one desktop baseline test fails on scrollY500 versus expected0. Its product source is byte-identical across the recorded baseline/current bases. Five candidate browser tests pass in22.5s: desktop/mobile Escape, shortcut toggle, actual Enter submission to Explore, and Search opened over Settings. The three recorded wheel flows stay at0 while Search is open and reach500 after close; Settings retains its own lock after Search closes and releases after Settings closes. The unchanged original-search-shortcut verifier also passes. This is focused validation, not an aggregate suite or an original visual-equivalence claim. Production build/typecheck are coordinated separately against the actual commit.

| Requested review item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | before-desktop-open.png and baseline.log show the actual background displacement. |
| after-screenshots | Desktop/mobile open and closed PNGs, after-submit.png and after-settings-still-locked.png. |
| walkthrough-video | walkthrough-desktop.webm records actual Search open, wheel action, Escape and resumed background scrolling. |
| backend-logs | N/A: no separate backend service or developer API is used. The Next server renders retained documents and serves the local user-search route. browser-requests.json and Next logs record that boundary. |
| frontend-logs | frontend-before.log, frontend-after.log, baseline.log and focused-after.log; source-shortcuts.log records the separate existing source check. |
| llm-trajectory | ACTION-RECEIPT.md is a public observable-action summary, not a verbatim LLM/private reasoning transcript. |
| domain-artifacts | before-scroll.json, after-scroll.json, source.patch and provenance.json bind actual scroll observations, finite scope and source/test hashes. |

Published log copies normalize LF/trailing whitespace and strip ANSI presentation sequences; raw originals and the failed trace/video remain external. Published PNG/video bytes are unchanged. Request JSON covers the recorded wheel-case interval before modal close; the Next log also records the submit and nested-modal routes. No production requests or dependency installs were made.
