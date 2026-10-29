# Info-bar modified keyboard navigation

A focused Positions radio consumed Ctrl+End as plain End: it selected Recently viewed and prevented document scrolling. This packet records the actual Windows Chromium control and fix. A Sign in button without this handler first established native Ctrl+End/Ctrl+Home scrolling on the same page.

The source change is one guard for Alt/Ctrl/Meta before the existing local radio-key handler. Plain Home/End, four arrows, wraparound, focus and the single roving tab stop retain their behavior. The existing ticker is still a local view switch with captured loading content; no original keyboard policy or visual parity is claimed. The shell evidence explicitly distinguishes maintained accessibility choices from captured facts.

## Results

- Baseline: one focused case failed at the actual info-bar scroll assertion. Sign in Ctrl+End moved scrollY to 6659; Positions Ctrl+End stayed at 0 and selected Recently viewed.
- Candidate: two focused browser cases passed in 10.3s. Sign in Ctrl+End moved to 6331; Positions Ctrl+End moved to 6959 without changing Positions, and Ctrl+Home returned to 0 with focus and selection retained. Document offsets vary with layout; the test checks the actual browser default and positive scrolling, not cross-run equality.
- Ctrl/Alt/Meta arrow controls preserve selection; plain Home/End and all four arrows still navigate with wraparound and correct focus/tabindex.
- Only localhost GET/HEAD requests were observed in the recorded flow. No separate backend, developer API, wallet or production request was used.
- Production build/typecheck are recorded separately at the submitted commit. No full-suite result is claimed by this packet.

## Review evidence

| Requested item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | [Actual failing Ctrl+End state](before-control-end.png), [baseline log](baseline.log) |
| after-screenshots | [Ctrl+End document end](after-control-end.png), [Ctrl+Home document start](after-control-home.png) |
| walkthrough-video | [Actual native control, info-bar End/Home flow](walkthrough.webm) |
| backend-logs | N/A: no standalone backend or developer API. Next serves the retained document; [browser requests](after-requests.json). |
| frontend-logs | [Before Next](frontend-before.log), [after Next](frontend-after.log), [focused result](focused.log) |
| llm-trajectory | [Public action receipt](ACTION-RECEIPT.md), observable actions/results rather than private reasoning or a verbatim session transcript. |
| domain-artifacts | [Before values](before-observations.json), [after values](after-observations.json), [source patch](source.patch), [source/test hashes](provenance.json), [artifact manifest](MANIFEST.json) |

## Reproduction

From `app/packages/frontend`, start the local app with `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`. Then run:

```sh
node node_modules/@playwright/test/cli.js test --config visual/token-info-keyboard-20261030/playwright.config.cjs
```

The config supplies only the existing clickwrap-accepted cookie. The baseline command filtered to `--grep 'Control End'` before the guard existed. The final test additionally checks modified-arrow nonselection and plain radio navigation. No captured JavaScript was executed. PNG/video bytes are unchanged; published logs use LF, omit terminal ANSI sequences and trailing whitespace. Raw logs, baseline video and failure trace are retained separately. This is a finite Windows Chromium result, not a claim about every platform's Ctrl+End mapping.
