# PR #1212 retained backend evidence

These are existing local results for implementation `5a94cd48ecc8ca9dcba19698cec9c6e46c967faa`; packaging them does not rerun tests or validate a new implementation.

- `before.log`: 13 controls pass, 4 behavioral assertions fail.
- `after.log`: 36 affected tests pass, zero failures.
- `build.log`, `typecheck.log`, `build-results.json`: original exact-commit workspace command output, both exit 0.
- `source-proof.json`: first-party contract identity and bounded source evidence.
- `work-record.json`: observable actions, commit/file identities and limitations. It is not a full assistant transcript.

after-intermediate.log retains the one stale daily=1 test assumption before its correction; only after.log is the final passing run.

Screenshots and video are N/A: this changes a backend JSON projection without a UI interaction or visual change. Frontend runtime logs are N/A; workspace build output includes its normal frontend build, not a browser run. The backend logs are the retained local HTTP regression output and related tests; no production-server logging is claimed.

`MANIFEST.json` hashes the retained bytes. `.gitattributes` keeps the original log line endings. The implementation and tests remain at their existing repository paths and commits.
