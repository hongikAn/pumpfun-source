# Observable action receipt

This is a retrospective summary of observable commands, decisions and results.
It is not a verbatim LLM trajectory, private reasoning, or credential/session transcript.

1. Read current root/frontend instructions, installed Next fetch documentation, the local feed contract and exact open-PR patches. Main was `094a06f18df738d41e77070c1a009e135671ac1a`. #1738 changes pre-dispatch input validation; #1219 changes the cursor recovery link. Neither isolates count failures.
2. Read the captured count consumer as inert text. `source-witness.json` records the full blob hash, enclosing factory, exact UTF-16 and UTF-8 ranges and caught callback. No captured JavaScript ran.
3. Created `codex/app-native-feed-count-isolation` from that main. Added three fault modes to the existing local fixture and focused browser checks. No fixture records, production connections, dependencies or shared validation checkout changed.
4. Started `node tests/support/native-feed-server.mjs` at loopback port 3001 and `node node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3011` from this worktree's frontend directory, with `PUMP_LOCAL_HOME_FEED=enabled` and no developer API key.
5. Ran `node node_modules/@playwright/test/cli.js test --config <evidence>/baseline.config.cjs` against unchanged source. It failed: expected 3 validated rows, received 0 after count-only HTTP 503. Retained actual screenshot, observations, test/source bytes and log.
6. One edit command incorrectly resolved a root-relative path from the frontend directory and failed before changing source. Its subsequent test command ran on unchanged source and was interrupted. `interrupted-pre-fix.log` is preserved, not presented as a candidate result.
7. Applied a nested catch around only count fetching/validation and updated the local boundary documentation. Ran the separate `focused-qualified.config.cjs`: 5 passed (17.4s). The three new cases cover HTTP 503, malformed JSON and provenance rejection; each retains list and pagination without a false zero count. Existing cases cover healthy count/head-token pagination and seven page failures.
8. Viewed before/after screenshots, stopped both owned servers and restored generated next-env.d.ts. Public text logs normalize newlines, remove ANSI and trailing whitespace; screenshots/video are unchanged. Raw originals remain in the external evidence directory. Source, fixture and test hashes are recorded.

No aggregate test suite was run for this change. Root separately owns build/typecheck validation before submission.
