# Observable action receipt

This is a retrospective commands/results summary, not private reasoning or a verbatim LLM trajectory.

1. Read current repository guidance, installed Next useRouter documentation, the maintained 42-card Live adapter and its local-design boundary. Reviewed actual overlapping patches: #1449 changes selection readiness, #1534 handles IME Escape, #1328 composes section keyboard actions; #1617/#1570 add other archived sections. None reveals the current metadata panel after an Inspect click.
2. Created `codex/app-live-inspect-focus` from main `094a06f18df738d41e77070c1a009e135671ac1a`. Added focused cases to existing `tests/live.spec.ts`; no fixture or captured evidence bytes changed.
3. Started this worktree's frontend with `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3010`, explicitly from `app/packages/frontend`, without a production API key. Existing clickwrap acknowledgement avoids altering that unrelated flow.
4. Baseline command: `node node_modules/@playwright/test/cli.js test --config <evidence>/baseline.config.cjs`. The real 375x812 browser clicked the seventh existing archived card. URL selected `$RAT - Exfil Rat`, but the metadata heading was at -3117px and not in the viewport; focus remained on the button. The case failed at `toBeInViewport`, before the later focus assertion. Retained raw baseline code/test as gzip-compressed inert text, screenshot, geometry, log, local trace and video.
5. Added an action-specific inspection request, canceled on other navigation/popstate. After the selected URL commits, focus moves to its metadata heading without automatic focus scrolling; a heading outside the viewport is centered. Same-record re-inspection requests focus too. No request is created by a direct URL.
6. Candidate command: `node node_modules/@playwright/test/cli.js test --config <evidence>/focused.config.cjs`. Three cases passed in 7.0s: mobile and desktop selection/re-inspection/Escape/Close return, plus direct URL no-focus/no-scroll. Mobile heading top became 391px; desktop was visible at 116px. Local browser request/console controls passed. No production media, WebSocket, mutation or captured JavaScript execution occurred.
7. Stopped the owned server and restored generated next-env.d.ts. Reviewed actual before/after screenshots. Public logs remove ANSI/trailing whitespace and use LF; images/video are unchanged. Baseline gzip bytes preserve the originals. Source-only JSX formatting and documentation were finalized without another browser run; root performs build/typecheck on the committed candidate.

No aggregate suite, real screen-reader run, current Live service or original mobile visual parity is claimed.

8. Root build and typecheck both passed on `ea4b0030f23e40f04f306fd0c0463fc77510dc2c`. Preserved complete logs/results as deterministic gzip files. Only evidence is added afterward; executable source/tests are unchanged.
