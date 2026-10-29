# PnL leaderboard period codes

The native `GET /v1/pnl-leaderboard` response uses `daily=3`, `weekly=1`,
`monthly=2`. The previous `daily=1`, `weekly=2`, `monthly=3` mapping was an
incorrect local assumption. Code `0` means unspecified, not all-time.

The captured first-party contract factory **154263** declares the numeric
period schema and binds it directly to `GET /pnl-leaderboard` response
`periodType`. Its description assigns `0 unspecified, 1 weekly, 2 monthly,
3 daily`. This is the same endpoint, not an enum inferred from another API.

Authenticated source:

- Raw file: `app/evidence/web/objects/2b47dd0b38a1608f.js`.
- Raw SHA-256: `e78d2f38b06f971847c18dd05457c75afc85208135f50d6e4022a5f197e8839d`.
- Factory UTF-16 range: `[303120, 316163)`.
- Factory SHA-256: `cd01bde47e65d8950932e98d4dc853a8e18e53e527de909f905b5caf1b4fc878`.
- Readable derivation: `app/recovered/modules/154263-cd01bde47e65.js`, lines 84–89
  and 202–226; provenance is in `app/recovered/modules.json`.

Raw-file and extracted-factory hashes were checked without executing captured
JavaScript. HTTP regressions cover each period independently; existing ranking,
labels, window anchors and synthetic attribution remain unchanged. The local
PnL data and broader production compatibility remain unqualified.
