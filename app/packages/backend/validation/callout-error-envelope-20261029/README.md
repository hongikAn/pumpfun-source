# Native callout error envelopes

The first-party OpenAPI Error schema says every refused request carries an integer `statusCode`. Its 400/default responses bind all five affected callout operations to that schema. The opt-in handlers returned only `error`/`reason`, even when the HTTP status was 400 or 501. The fix adds the matching status field to all eight error-send paths, without changing HTTP decisions, reason codes, successful responses, or API-key handling.

The local regression uses five real Fastify routes and synthetic stores, not mocked handlers. Before: 13 missing-field failures and four passing success/auth controls. After: 17/17 pass; the affected callout read suites pass 254/254. Those totals overlap and must not be added together.

| Review evidence item | Artifact or specific N/A |
| --- | --- |
| before-screenshots | N/A: JSON-only backend change; `before.log` contains the actual failing response-field assertions. |
| after-screenshots | N/A: no visual behavior changed; `after.log` and the committed HTTP assertions establish the after behavior. |
| walkthrough-video | N/A: no browser workflow; `action-receipt.json` records the public actions and results. |
| backend-logs | `before.log`, `after.log`, `focused.log`: actual local HTTP/test output. No production-server log claim. |
| frontend-logs | N/A: no frontend source or browser runtime changed or exercised. |
| llm-trajectory | `action-receipt.json` is the retained observable action/result record. It is not private reasoning or a complete assistant transcript; none is fabricated. |
| domain-artifacts | `source-proof.json` binds each operation to the original schema; `test/callout-error-envelope.test.ts` asserts body status equals HTTP status and validates that schema. |

`MANIFEST.json` records artifact hashes. The original OpenAPI bytes, status/reason policies and synthetic attribution remain unchanged. This is an error-envelope contract correction, not full native API compatibility. The existing single-callout null response and unsupported-operation boundaries are preserved.
