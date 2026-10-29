# PR #1179 retained backend evidence

These are existing local results for implementation `d268d5d803b524927aae37f263930d36f5c7c7a8`; packaging them does not rerun tests or validate a new implementation.

- `before.log`: 3 controls pass, 1 behavioral assertions fail.
- `after.log`: 38 affected tests pass, zero failures.
- `build.log`, `typecheck.log`, `build-results.json`: original exact-commit workspace command output, both exit 0.
- `source-proof.json`: first-party contract identity and bounded source evidence.
- `work-record.json`: observable actions, commit/file identities and limitations. It is not a full assistant transcript.

before-initial.log has a test-attribution setup typo; only before.log is the behavioral baseline.

Screenshots and video are N/A: this changes a backend JSON projection without a UI interaction or visual change. Frontend runtime logs are N/A; workspace build output includes its normal frontend build, not a browser run. The backend logs are the retained local HTTP regression output and related tests; no production-server logging is claimed.

`MANIFEST.json` hashes the retained bytes. `.gitattributes` keeps the original log line endings. The implementation and tests remain at their existing repository paths and commits.
