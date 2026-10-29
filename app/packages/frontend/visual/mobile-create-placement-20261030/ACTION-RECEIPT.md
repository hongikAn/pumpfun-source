# Public action receipt

This is a retrospective summary of observable actions, commands and outcomes. It is not a verbatim LLM trace or private reasoning transcript.

1. Read current rules, the shell contract and the actual open PR patches. Excluded #1398 (child-menu Escape) and #1300 (opening keyboard focus); neither changes the mobile placement selected in AppSidebar.
2. Created an isolated branch at 665499915f9caedcd38921d415a90f0606686398. No dependency installation or captured JavaScript execution.
3. Added the 320px menu bounds regression, ran it on unchanged product code, and retained the real screenshot, video, geometry and failing log. The menu extended to x454 in a 320px viewport.
4. Changed two source statements to select bottom-start for the existing mobile drawer while keeping desktop right-start.
5. Ran four focused tests. Geometry passed; the first cold /create navigation exceeded the test's five-second URL wait. Kept that failure and changed only that wait to fifteen seconds. The unchanged product code then passed all four tests, including actual Create navigation at 320, 375 and 767px and both desktop sidebar states.
6. Stopped only the two owned dev-server sessions and restored generated next-env.d.ts. Preserved raw logs externally; normalized published text copies as recorded in provenance.json.

Reproduction from app/packages/frontend: start the local Next server on 127.0.0.1:3010 with `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`, then run `node node_modules/@playwright/test/cli.js test --config visual/mobile-create-placement-20261030/playwright.config.cjs`. No production traffic is needed.
