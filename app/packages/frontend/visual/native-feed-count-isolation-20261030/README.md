# Optional local count failure isolation

The first local newest page can be valid while its later count request fails. Before this change, that count failure discarded the entire list. The adapter now retains the already validated page and omits the failed count. It never substitutes zero. Page transport/provenance/shape rejection remains unchanged.

The original `735821.x` consumer catches its separate count request. `source-witness.json` pins that callback, blob/factory hashes and half-open UTF-16/UTF-8 ranges. The local transport and UI remain authored, synthetic and unqualified; this is not a production/visual parity claim, realtime implementation or production outage experiment.

## Results

- Unchanged base: the new count-only HTTP 503 case failed (expected 3 cards, got 0) and displayed Local callouts unavailable.
- Candidate: 5 focused Chromium tests passed (17.4s). HTTP, malformed JSON and wrong count provenance retain all 3 validated cards, omit the count, and allow Next to the existing 1-card continuation. Normal count remains tied to the exact page head. The existing page-failure test still rejects unavailable, wrong source, wrong compatibility, wrong cache, wrong content type, malformed and duplicate pages.
- The browser stayed on the local Next origin; no browser-side backend request, production call or mutation was made. The existing synthetic fixture records are reused unchanged. Page/count faults are test controls, not captured backend responses.
- The first root build/typecheck of `341939a38f5fd68ef68847e2393f12bd747321b6` failed because archived baseline `.ts` files were picked up by TypeScript. The evidence copies are now `.ts.txt` with identical bytes; source and browser tests were not changed. The failed results/logs are preserved below.
- An incorrect root-relative edit path caused an extra unchanged-source run; it was interrupted and preserved in `interrupted-pre-fix.log`. It is not a candidate result.
- The public browser configuration retains its actual local absolute paths for reproducibility; adjust them to a local checkout. No captured JavaScript was evaluated.

## Review evidence

| Requested evidence | Artifact or specific boundary |
| --- | --- |
| Before screenshot | [before-count-http.png](before-count-http.png), actual baseline |
| After screenshot | [after-count-http.png](after-count-http.png), same HTTP fault |
| Walkthrough video | [walkthrough.webm](walkthrough.webm), actual Chromium list and Next navigation |
| Backend logs | [backend.log](backend.log), isolated test-server stdout; actual server request lists are in before/after observation JSON. A production backend log is not applicable to this local synthetic integration. |
| Frontend logs | [frontend.log](frontend.log), [baseline.log](baseline.log), [focused.log](focused.log) |
| LLM trajectory | [ACTION-RECEIPT.md](ACTION-RECEIPT.md), observable action summary, not private reasoning or a verbatim trace |
| Domain artifacts | [source-witness.json](source-witness.json), before/after observations, [source.patch](source.patch), [file-hashes.json](file-hashes.json), [MANIFEST.json](MANIFEST.json) |

Build/typecheck results belong to the exact candidate validation recorded in the PR; this packet does not claim an aggregate suite or original-service qualification.
