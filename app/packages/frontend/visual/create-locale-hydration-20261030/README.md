# Create counter hydration across browser locales

The initial Create description hint used the runtime default locale. With this English UI served by Node using en-US and Chromium using de-DE, the same limit rendered as `2,000` on the server and `2.000` in the browser. React reported a hydration mismatch and regenerated the affected tree.

The one-line source fix formats that static limit with `en-US`, matching the maintained English UI. The limit remains 2,000; validation, captured inputs and draft behavior are unchanged. File-size labels in the same flow render only after client selection and are outside this SSR failure. This is local reconstruction behavior, not a claim about original visual or locale parity.

## Results

- Baseline: one German-locale case failed on the real React hydration pageerror. The retained response and DOM observations show the different separators.
- Candidate: both German and English cases passed in 10.0s. Response HTML and interactive DOM both contain `2,000`, without pageerrors. Editing the description updates the count, retains the coin-name draft and resets to `0/2,000`.
- The original baseline test had later, unreached `1,000` expectations. Those were corrected to the actual existing limit `2,000` in the final regression; the baseline failure occurs earlier at the hydration-error assertion. Its exact test is retained for transparency.
- Only localhost GET/HEAD requests were observed. No standalone backend, production service, wallet or developer API was used.
- Production build/typecheck are recorded separately at the submitted commit. No aggregate-suite result is claimed here.

## Review evidence

| Requested item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | [German counter before fix](before-de-DE.png), [actual failing log](baseline.log) |
| after-screenshots | [German browser](after-de-DE.png), [English control](after-en-US.png) |
| walkthrough-video | [Actual German load, draft edit and reset](walkthrough.webm) |
| backend-logs | N/A: no standalone backend or developer API. Next SSR logs are below; requests are retained in the observations. |
| frontend-logs | [Before Next](frontend-before.log), [after Next](frontend-after.log), [focused results](focused.log) |
| llm-trajectory | [Public action receipt](ACTION-RECEIPT.md): observable commands/results, not private reasoning or a verbatim session transcript. |
| domain-artifacts | [Before HTML/DOM/error](before-observations.json), [German after](after-de-DE-observations.json), [English after](after-en-US-observations.json), [source patch](source.patch), [provenance](provenance.json), [manifest](MANIFEST.json) |

## Reproduction

From `app/packages/frontend`, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010` with the developer API disabled. Then run:

```sh
node node_modules/@playwright/test/cli.js test --config visual/create-locale-hydration-20261030/playwright.config.cjs
```

The config supplies only the existing clickwrap-accepted cookie. The baseline command used `--grep de-DE` on the unchanged source. No captured JavaScript was executed. PNG/video bytes are unchanged. Published logs use LF and omit ANSI sequences and trailing whitespace; raw logs, baseline video and failure trace remain in the local run directory. This is a finite Windows Chromium/Node locale result, not coverage of every locale or runtime.
