# Public action receipt

This is a retrospective record of observable actions and outcomes. It is not a verbatim LLM trace or private reasoning transcript.

1. Read current repository guidance, the reference-page evidence contract and local Next Link anchor documentation. Checked actual open PR patches; no open patch in the 211-PR snapshot touched the reference stylesheet/renderer or global stylesheet.
2. Created an isolated branch at 9f9d94c56f7bbedb6c3e45a9e95c287321313621. No dependency install, captured JavaScript execution or production requests.
3. Added a real-browser regression and ran the 375px TOC case on unchanged product source. It failed because heading y=23.515625 is behind the actual header bottom49. Saved screenshot, video, geometry, requests and test/server logs.
4. Added a mobile-only 4rem scroll margin to reference h2/h3 headings. Left the global shell variable and desktop layout untouched.
5. Ran the four focused cases once. All passed in 11.7s, covering mobile TOC/direct fragment and desktop controls. Saved actual geometry and images, local request lists and a walkthrough video.
6. Stopped only the owned before/after Next dev-server sessions, restored generated next-env.d.ts and preserved the raw logs externally. Published normalized log copies are hash-bound in provenance.json.

From app/packages/frontend, start `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`, then run `node node_modules/@playwright/test/cli.js test --config visual/reference-mobile-anchor-20261030/playwright.config.cjs`.
