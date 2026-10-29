# Public action receipt (retrospective)

This is a concise, retrospective record of observable work and outcomes. It is **not** a verbatim LLM trajectory, private chain of thought, tool-session transcript or credential log.

1. Read the existing local contract and current PR overlap before editing. Recorded xUsername was present in the existing synthetic profile but had no link. The maintained component follows the captured trim / one-leading-@ / encoded path / omission behavior. Local placement is not original visual parity.
2. Added the focused regression and ran it on unchanged baseline `f634ae0aaaf719ee51507ef7c971d2a1d4f5e026`. The actual baseline regression failed because the @alice_on_x on X link was absent. Earlier setup/no-test-match attempts were not behavioral failures and are not presented as such. The retained baseline log and screenshot are linked in README.
3. Applied the small source change shown in source-diff.patch.gz and ran focused checks. Original focused verification: 3 rendering controls and 8 profile browser cases passed. Fresh capture: Alice link, keyboard activation into a locally fulfilled X popup, and missing-handle omission.
4. The parent validation lane ran `npx --yes pnpm@10.24.0 build` and `npx --yes pnpm@10.24.0 typecheck` in `app` at `ec972afcfd9623633096aa2775d49d2c9f021264`; both exited zero. Exact original timestamps and command arrays are in build-typecheck.json. No aggregate test-suite pass was claimed.
5. Published Draft #1181. The review requested seven evidence categories; no code or line-specific defect was reported.
6. On 2026-10-29, checked out that same source head and executed the retained capture.cjs against an owned loopback Next server. Actual steps, timestamps, URLs and results are in capture.json / capture.log. All owned servers were stopped afterward. The new captures are labeled separately from the earlier qualification.
7. Added this evidence-only follow-up and explicit applicability boundaries; no product source, fixtures, SDK, captures or dependency bytes were changed.

No hidden reasoning, credentials or unrelated user conversation is part of these artifacts.
