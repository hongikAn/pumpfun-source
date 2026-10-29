# Public action receipt (retrospective)

This is a concise, retrospective record of observable work and outcomes. It is **not** a verbatim LLM trajectory, private chain of thought, tool-session transcript or credential log.

1. Read the existing local contract and current PR overlap before editing. The local newest feed offered a ranked first-page link after a cursor error. Recovery now retains valid newest ordering; unknown/repeated views still fall back to ranked. This is the local integration contract, not production cursor or original error-policy recovery.
2. Added the focused regression and ran it on unchanged baseline `f45853cffebd5449266551667793201c822f641b`. The actual baseline regression failed because the recovery href was ranked, not newest. A later source-edit attempt failed on Windows text encoding, then an unintended unchanged-source test run was interrupted. That interrupted run is not claimed as a passing after result. The retained baseline log and screenshot are linked in README.
3. Applied the small source change shown in source-diff.patch.gz and ran focused checks. Original focused verification: all 12 native-feed browser cases passed. Fresh capture: backend-rejected and malformed newest cursor errors, keyboard recovery to the first newest page, and exact local newest/count requests.
4. The parent validation lane ran `npx --yes pnpm@10.24.0 build` and `npx --yes pnpm@10.24.0 typecheck` in `app` at `b5190a6e88b07e18ffe6bd8b8a92fcf00b12790d`; both exited zero. Exact original timestamps and command arrays are in build-typecheck.json. No aggregate test-suite pass was claimed.
5. Published Draft #1219. The review requested seven evidence categories; no code or line-specific defect was reported.
6. On 2026-10-29, checked out that same source head and executed the retained capture.cjs against an owned loopback Next server. Actual steps, timestamps, URLs and results are in capture.json / capture.log. All owned servers were stopped afterward. The new captures are labeled separately from the earlier qualification.
7. Added this evidence-only follow-up and explicit applicability boundaries; no product source, fixtures, SDK, captures or dependency bytes were changed.

No hidden reasoning, credentials or unrelated user conversation is part of these artifacts.
