# Public action receipt

This is a retrospective summary of observable actions/commands and results. It is not a verbatim LLM trace or private reasoning transcript.

1. Read current guidance, the shell's local modal contract and installed Next client-component documentation. Existing PR heads had no new actionable review or CI failure. The fresh271open actual-patch snapshot contained Search hydration/history work and an independent shared-helper correction, but no Search scroll ownership patch.
2. Added a real-wheel regression on unchanged product source at b08fd908. With Search and its existing local alice result open over /docs/fees, a backdrop wheel moved the document0->500. Preserved the actual failing assertion, screenshot, video, request/scroll JSON and Next log.
3. Moved the independent branch to verified current2c8a7900; the source and app tree were unchanged across those bases. Added the shared-lock import and a separate effect driven by observed native open state. Existing shortcut/query logic and lock helper were left intact.
4. Ran five focused browser cases once on the candidate:5passed22.5s. Verified desktop/mobile close, shortcut close, actual Explore submission and ownership when Settings remains open underneath. Ran the original-search-shortcuts verifier separately; it passed without executing captured JavaScript.
5. Stopped only owned server sessions, restored generated next-env.d.ts and prepared actual evidence. No production call, dependency install or shared-worktree write.

From app/packages/frontend, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`, then run `node node_modules/@playwright/test/cli.js test --config visual/search-scroll-lock-20261030/playwright.config.cjs`. From app, run `node scripts/verify-search-shortcuts.mjs --check`.
