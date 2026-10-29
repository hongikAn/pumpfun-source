# Lane createv2-reconstruction

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 125 direct calls).

## Trial log

| Trial | Mechanism | Bytes | Ratio | Calls | Official | Ledger id |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main baseline (1fb76c54f) | CreateQuoteConfig enum, compact curve writes | 14,848 | 0.2467 | 126 | 1019/188 | - |
| x27port | historical `x27_current_roles` create_v2.rs + `pub(crate) global_quote` | 15,584 | 0.7411 | 125 | 1019/188, no gains/losses | c90b6cdd43604d3595ebbd93a80bc28c |

## Mechanism (x27port)

Restores the 2026-10-28 `x27_current_roles` create_v2.rs (from
`b4448f7bc^:research/goal-pump-create-recovery-20261028/trials/x27_current_roles/`):
`validate_quote_mint` returning `(Pubkey, Option<(u64,u8)>, QuoteSource)`, called before the
mayhem/whitelist check; mayhem check through `pump_quote::global_quote`; every BondingCurve
field written explicitly (including zero/false fields); `validate_metadata(&str,&str,&str)` with
`MAX_*_LENGTH` consts. That revision was never merged into main, which had moved to a compact
enum version that lost 728 B and the call count. The port keeps every baseline membership.
