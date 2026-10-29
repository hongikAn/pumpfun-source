# Mobile reference-document anchors

At the recorded unchanged base, activating the Platform Fee table-of-contents link at 375px places the heading at y=23.52px behind the actual 49px sticky header. The mobile shell variable is `auto`, so the existing heading `calc(var(--shell-header) + 1rem)` computes to a zero scroll margin. The fix sets a finite 4rem scroll margin only for mobile reference-document h2/h3 headings. The global shell variable and desktop styling remain unchanged.

This is a local wrapper behavior fix, consistent with REFERENCE-PAGES-EVIDENCE.md. The captured document text, archive metadata and original evidence are unchanged. No original live-layout parity or current fee-policy claim is made.

Validation: the representative unchanged-source test fails on the heading/header geometry assertion. The fixed source passes four tests in 11.7s: keyboard activation of the 375px TOC, a direct 320px fragment URL, and desktop TOC/direct-fragment controls. Every observed request is a local GET/HEAD. The measured mobile heading is y=87.52px or y=88.33px, below the same 49px header; desktop y=183.98px remains below its actual 77px header. Tests observe native anchor behavior without forcing a test-only scroll. This is a focused result, not an aggregate suite claim. Production build/typecheck are coordinated separately against the actual commit.

| Requested review item | Evidence or specific N/A |
| --- | --- |
| before-screenshots | before-375.png and baseline.log show the real unchanged-source failure. |
| after-screenshots | after-375-contents.png, after-320-fragment.png and both after-1440 images. |
| walkthrough-video | walkthrough-375.webm records actual Chromium navigation and keyboard activation of the local TOC. |
| backend-logs | N/A: no backend service/developer API is involved. The Next server reads retained reference documents; browser-requests.json and both Next logs show the local boundary. |
| frontend-logs | frontend-before.log, frontend-after.log, baseline.log and focused-after.log. |
| llm-trajectory | ACTION-RECEIPT.md is a public observable action summary, not a verbatim LLM/private reasoning transcript. |
| domain-artifacts | Before/after geometry JSON, source.patch and provenance.json bind the finite behavior, source and test hashes. |

Published logs use disclosed LF/trailing-whitespace normalization with ANSI presentation sequences removed. Raw originals, failure trace and baseline video are retained externally. Published PNG/video bytes are unchanged. The same installed Node/Next/Chromium dependencies were used without a package install.
