#!/usr/bin/env python3
"""Restore this lane's observed records without overwriting other lanes."""
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import uuid

LANE = Path(__file__).resolve().parent
SWARM = LANE.parents[1]
LOG = SWARM / "ATTEMPTS.jsonl"
LOCK = SWARM / ".attempts.lock"

records = [
    {
        "schema": "main-pump-attempt-v1",
        "attempt_id": "b24538ab694745e2b65c26bac6a5b8c2",
        "timestamp_utc": "2026-10-29T10:03:50.226943+00:00",
        "lane": "migrate-sweep-reconstruction",
        "approach": "semantic-callee-rebinding",
        "target": "0x77940",
        "dedupe_key": "0x77940-e38a8b97a-callee-semantic-rebinding-v1",
        "hypothesis": "Direct callee roles identify the unmatched window as cashback claim_v2; actual migrate_v2 execute is already normalized-matched at original 0x49888",
        "status": "analyzed",
        "data": {
            "actual_migrate_diff": "lanes/migrate-sweep-reconstruction/evidence/actual-migrate-v2-original-vs-canonical.diff",
            "cashback_evidence": "lanes/migrate-sweep-reconstruction/evidence/cashback-call-targets.json",
            "evidence": "lanes/migrate-sweep-reconstruction/evidence/call-targets.json",
            "missing_constraint": "The requested pairing migrate_v2::execute at 0x77940 is contradicted by pinned bytes; no semantic migration candidate can be justified for this window.",
            "next_probe": "Use actual cashback semantics and token-first physical branch layout for 0x77940.",
            "observations": {
                "window_0x49888": "pump_recovered::migrate_v2::execute; baseline normalized=true raw=false",
                "window_0x77940": "Clock::get, record_cashback_claim, ClaimCashbackEvent::data, no pool-creation helper calls"
            }
        }
    },
    {
        "schema": "main-pump-attempt-v1",
        "attempt_id": "5d9e32581e1d4e109328b9a4754f93dc",
        "timestamp_utc": "2026-10-29T10:20:18.909398+00:00",
        "lane": "migrate-sweep-reconstruction",
        "approach": "claim-mint-hold-token-first-branches",
        "target": "0x77940",
        "dedupe_key": "0x77940-claim-mint-hold-token-first-branches-v1",
        "hypothesis": "Token-first amount and payout layout on the claim-mint-hold base will better reproduce the original cashback control-flow order.",
        "status": "partial",
        "data": {
            "binding_correction": "Original 0x77940 is probed as cashback::claim_v2, not migrate_v2::execute; actual migrate_v2 is original 0x49888 and already normalized-matched.",
            "build": {
                "recipe": "identity",
                "runtime_valid": True,
                "stripped_sha256": "901feb38cde706f68a08b5d27bc08bffce36d9da38ead5eba6e02d00a28dc651",
                "unstripped_sha256": "f486fec79cae71b4053e9e4d4ae46bdc872ea16fb3c1daeec97ead8292fc0a4d"
            },
            "source": {
                "canonical_sha256": "ab6db0255d5efa8c586cef12af00320eb660a43d82a664a0c1f30e2ff9ffe4e5",
                "candidate_sha256": "bc7d2a553ac84da49ddaac385b39726bba3917dab208e2a08d4c0e1e1be7ec91",
                "diff": "lanes/migrate-sweep-reconstruction/outputs/cashback-token-first/source.patch"
            },
            "official_score": {
                "normalized": 1019,
                "raw": 188,
                "total": 1035,
                "matched_text_bytes": 1611088,
                "gains": [],
                "losses": [],
                "raw_gains": [],
                "raw_losses": [],
                "path": "lanes/migrate-sweep-reconstruction/outputs/cashback-token-first/score.json"
            },
            "diagnostics": {
                "symbol": "pump_recovered::token_incentives::claim_token_incentives::cashback::claim_v2",
                "original_bytes": 8832,
                "candidate_bytes": 9408,
                "ratio": 0.2343,
                "original_direct_calls": 70,
                "candidate_direct_calls": 68,
                "prior_claim_mint_hold_ratio": 0.26581118240146656,
                "diff": "lanes/migrate-sweep-reconstruction/outputs/cashback-token-first/target.diff",
                "calls": "lanes/migrate-sweep-reconstruction/outputs/cashback-token-first/call-targets.json"
            },
            "result": "No strict normalized or raw gain and no baseline loss; token-first inversion reduced the diagnostic ratio and is rejected as an acceptance candidate.",
            "attribution_limit": "Final diff audit found additional AccountInfo ownership differences from the pinned claim-mint-hold patch; the result does not isolate branch inversion alone."
        }
    },
    {
        "schema": "main-pump-attempt-v1",
        "attempt_id": "6ed0f5b4ee7e42b3a0123a2a954e3a21",
        "timestamp_utc": "2026-10-29T10:24:14.757422+00:00",
        "lane": "migrate-sweep-reconstruction",
        "approach": "native-recipient-temporary-clock-map-err",
        "target": "0x72810",
        "dedupe_key": "0x72810-native-recipient-temporary-clock-map-err-v1",
        "hypothesis": "An explicit Clock::get map_err Result boundary will preserve distinct event-error and success return blocks in the native-recipient-temporary sweep base.",
        "status": "partial",
        "data": {
            "build": {
                "recipe": "identity",
                "runtime_executed": False,
                "runtime_valid": True,
                "stripped_sha256": "2c284661345c354caf9484b55e3dd5510dd4ef96de2b1268ae04d700ff7a0a05",
                "unstripped_sha256": "c8e09e384b13b95a6cab3fd534d9800362a3749ae7904078b956733247d53ef5"
            },
            "source": {
                "canonical_sha256": "8735adba8b670c3b4ee63a6fd716d1d639be6efa56269a15365c15ff2f44ba0c",
                "candidate_sha256": "d332b07d4ea25a1d0f16bbd1fb5c1ea1f0ce0bf41012bfa80442d1066a409a96",
                "diff": "lanes/migrate-sweep-reconstruction/outputs/sweep-clock-map-err/source.patch",
                "cashback_source_restored_canonical": True
            },
            "official_score": {
                "normalized": 1019,
                "raw": 188,
                "total": 1035,
                "matched_text_bytes": 1611088,
                "gains": [],
                "losses": [],
                "raw_gains": [],
                "raw_losses": [],
                "path": "lanes/migrate-sweep-reconstruction/outputs/sweep-clock-map-err/score.json"
            },
            "diagnostics": {
                "symbol": "pump_recovered::sweep::execute",
                "original_bytes": 7832,
                "candidate_bytes": 8000,
                "ratio": 0.3981,
                "prior_native_recipient_temporary_bytes": 8048,
                "prior_native_recipient_temporary_ratio": 0.3969151670951157,
                "original_direct_calls": 39,
                "candidate_direct_calls": 40,
                "candidate_memcmp_calls": 4,
                "candidate_outlined_account_info_clone_calls": 2,
                "diff": "lanes/migrate-sweep-reconstruction/outputs/sweep-clock-map-err/target.diff",
                "calls": "lanes/migrate-sweep-reconstruction/outputs/sweep-clock-map-err/call-targets.json",
                "structure": "lanes/migrate-sweep-reconstruction/outputs/sweep-clock-map-err/structure.json",
                "topology": {
                    "original_reduced_blocks": 96,
                    "candidate_reduced_blocks": 95,
                    "verified": False,
                    "reason": "two original blocks reach one candidate block",
                    "at_original": "0x1838",
                    "at_candidate": "0x1f28",
                    "mapped_blocks_before_failure": 56
                }
            },
            "result": "No strict normalized or raw gain and no baseline loss. The map_err probe is not output-equivalent to its base, but it leaves the same collapsed return join and 56-block topology failure; the mechanism is rejected for this residual."
        }
    },
    {
        "schema": "main-pump-attempt-v1",
        "attempt_id": uuid.uuid4().hex,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "lane": "migrate-sweep-reconstruction",
        "approach": "claim-mint-hold-token-first-exact-base-preparation",
        "target": "0x77940",
        "dedupe_key": "0x77940-claim-mint-hold-token-first-branches-exact-base-v1",
        "hypothesis": "Removing the composite candidate's extra AccountInfo ownership changes will isolate token-first branch inversion on the exact pinned claim-mint-hold base.",
        "status": "analyzed",
        "data": {
            "preparation_interrupted": True,
            "built": False,
            "scored": False,
            "reason": "The research tree disappeared after the first corrective source edit. No complete corrected candidate, binary, or score was produced; the trial was not rerun during handoff recovery.",
            "next_action": "Recreate from canonical with the exact prior patch plus only token-first amount and payout inversion, then check this dedupe key before building."
        }
    }
]

LOCK.touch(exist_ok=True)
with LOCK.open("r+") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    existing = []
    if LOG.exists():
        existing = [json.loads(line) for line in LOG.read_text().splitlines() if line.strip()]
    keys = {row.get("dedupe_key") for row in existing}
    restored = []
    with LOG.open("a") as output:
        for record in records:
            if record["dedupe_key"] in keys:
                continue
            output.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            output.flush()
            restored.append({"dedupe_key": record["dedupe_key"], "attempt_id": record["attempt_id"]})
    total = len(existing) + len(restored)
    digest = hashlib.sha256(LOG.read_bytes()).hexdigest()
print(json.dumps({"restored": restored, "attempts_in_ledger": total, "ledger_sha256": digest}, indent=2))
