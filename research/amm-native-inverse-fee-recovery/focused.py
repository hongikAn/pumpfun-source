"""Fresh signed native inverse fee triples using the established epoch and arithmetic controls."""
from pathlib import Path
import argparse
import base64
from collections import Counter
import gzip
import hashlib
import json
import os
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
os.environ['PUMP_AMM_FRESH_VM'] = '1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_amm_liquidity_differential as h
from solders.clock import Clock
from solders.litesvm import LiteSVM
from solders.transaction_metadata import FailedTransactionMetadata


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config(older=(0, 7, 100), newer=(5, 23, 1000)):
    return bytes(72) + struct.pack('<QQH', *older) + struct.pack('<QQH', *newer)


def extension(kind, data):
    return struct.pack('<HH', kind, len(data)) + data


def cases():
    valid = extension(1, config())
    unknown = extension(65535, b'')
    other = extension(3, bytes(32))
    rows = [
        dict(label='legacy-82', size=82),
        dict(label='no-fee-envelope-167', tlv=b'\0'),
        dict(label='zero-kind-terminator', tlv=bytes(2)),
        dict(label='other-known-extension', tlv=other),
        dict(label='unknown-extension', tlv=unknown),
        dict(label='unknown-before-fee', tlv=unknown + valid),
        dict(label='unknown-after-fee', tlv=valid + unknown),
        dict(label='terminator-before-fee', tlv=bytes(2) + valid),
        dict(label='terminator-after-fee', tlv=valid + bytes(2)),
        dict(label='older-epoch', tlv=valid, epoch=4),
        dict(label='newer-epoch-at', tlv=valid, epoch=5),
        dict(label='newer-epoch-after', tlv=valid, epoch=6),
        dict(label='short-83', size=83, malformed=True),
        dict(label='short-165', size=165, malformed=True),
        dict(label='short-166', size=166, malformed=True),
        dict(label='bad-padding', tlv=bytes(2), padding=1, malformed=True),
        dict(label='bad-account-type', tlv=bytes(2), account_type=2, malformed=True),
        dict(label='partial-header-two', tlv=struct.pack('<H', 1), malformed=True),
        dict(label='partial-header-three', tlv=struct.pack('<H', 1) + b'\x6c', malformed=True),
        dict(label='value-overrun', tlv=struct.pack('<HH', 3, 32), malformed=True),
        dict(label='short-fee-config', tlv=extension(1, config()[:-1]), malformed=True),
        dict(label='duplicate-fee-config', tlv=valid + valid, malformed=True),
        dict(label='fee-before-malformed-header', tlv=valid + struct.pack('<H', 3), malformed=True),
        dict(label='terminator-before-malformed-header', tlv=bytes(2) + struct.pack('<H', 3)),
    ]
    decoder_rows = [dict(instruction=instruction, mint=mint, **case)
            for instruction in ('deposit', 'withdraw')
            for mint in ('base', 'quote') for case in rows]
    arithmetic = [dict(instruction=instruction, mint='quote', label=f'fee-{bps}-max-{cap}-amount-{amount}', tlv=extension(1, config((0,cap,bps),(0,cap,bps))), amount=amount) for instruction in ('deposit','withdraw') for bps in (0,1,100,9999,10000) for cap in (0,1,123,2**64-1) for amount in (0,1,1000000)]
    return decoder_rows + arithmetic


def mutate(case):
    key = h.base if case['mint'] == 'base' else h.quote

    def apply(vm_harness, metas):
        vm = vm_harness.vm
        mint = vm.get_account(key)
        data = bytearray(mint.data[:82])
        if 'size' in case:
            data += bytes(max(0, case['size'] - len(data)))
            data = data[:case['size']]
        else:
            data += bytes(83) + bytes([case.get('account_type', 1)]) + case['tlv']
        if case.get('padding') is not None:
            data[82] = case['padding']
        vm.set_account(key, h.Account(mint.lamports, bytes(data), h.TOKEN22))
        # Valid TransferFeeAmount state permits both fee-bearing and fee-free mints.
        for address in ([h.userbase, h.vaultbase] if key == h.base else [h.userquote, h.vaultquote]):
            account = vm.get_account(address)
            token = bytearray(account.data[:165])
            # This fixture's WSOL accounts must be ordinary non-native accounts
            # when their mint changes to Token-2022.
            token[109:121] = bytes(12)
            token += bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
            vm.set_account(address, h.Account(account.lamports, bytes(token), h.TOKEN22))
        epoch = case.get('epoch', 0)
        vm.set_clock(Clock(100, 1234567890, epoch, epoch, 1234567890))
    return apply


def observed(result):
    return {**result, 'logs': [line for line in result['logs'] if not re.fullmatch(
        r'Program \S+ consumed \d+ of \d+ compute units', line)]}


def classify(result):
    logs = result['logs']
    if result['error'] is None:
        return 'success'
    if any('Error Number: 6007' in line and 'UnsupportedQuoteMint' in line for line in logs):
        return 'target-UnsupportedQuoteMint-6007'
    if any('invoke [2]' in line for line in logs):
        return 'dependency-CPI-or-later-rejection'
    if any(('AnchorError caused by account:' in line or 'ProgramError caused by account:' in line)
           for line in logs):
        return 'account-validation-before-helper'
    return 'other-rejection-review-logs'


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    receipts = args.output.parent / 'raw-transactions.jsonl.gz'
    images = dict(original=ROOT / 'evidence/original/pump_amm/deployed.so',
                  control=args.control.resolve(), candidate=args.candidate.resolve())
    inputs = [Path(__file__), ROOT / 'scripts/pump_amm_liquidity_differential.py',
              ROOT / 'scripts/pump_amm_admin_differential.py',
              ROOT / 'scripts/pump_amm_reusable_harness.py',
              ROOT / 'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
              ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json',
              ROOT / 'evidence/upstream/pump_amm.json',
              ROOT / 'evidence/dependencies/spl_token/deployed.so',
              ROOT / 'evidence/dependencies/spl_token_2022/deployed.so']
    input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    image_hashes = {name: sha(path) for name, path in images.items()}
    native_acquire = h.acquire_harness
    prior_load = LiteSVM.add_program_from_file
    loaded = {}

    def load(vm, key, path):
        digest = sha(path)
        result = prior_load(vm, key, path)
        assert digest == sha(path)
        loaded.setdefault(id(vm), {})[str(key)] = dict(path=str(Path(path).resolve()), sha256=digest)
        return result

    LiteSVM.add_program_from_file = load
    prior_send = LiteSVM.send_transaction  # Includes the unchanged canonical observer.
    current = {}
    counters = dict(vms=0, transactions=0, signature_fields=0)

    def acquire(program):
        instance = native_acquire(program)
        assert not getattr(instance.vm, '_focused_used', False), 'VM reused'
        instance.vm._focused_used = True
        instance.vm._focused_serial = counters['vms']
        counters['vms'] += 1
        return instance

    h.acquire_harness = acquire
    with receipts.open('wb') as target:
        with gzip.GzipFile(filename='', mode='wb', fileobj=target, mtime=0) as stream:
            def send(vm, tx):
                checks = tx.verify_with_results()
                assert checks and all(checks)
                raw = bytes(tx)
                def snapshot():
                    output = {}
                    for key in sorted(set(tx.message.account_keys), key=str):
                        a = vm.get_account(key)
                        if a is not None and a.executable:
                            continue
                        output[str(key)] = None if a is None else dict(
                            owner=str(a.owner), lamports=a.lamports,
                            executable=a.executable, data_hex=bytes(a.data).hex())
                    return output
                before = snapshot()
                result = prior_send(vm, tx)
                assert bytes(tx) == raw
                failed = isinstance(result, FailedTransactionMetadata)
                meta = result.meta() if failed else result
                after = snapshot()
                payer = str(tx.message.account_keys[0])
                rollback = None
                payer_fee = None
                if failed:
                    unchanged = all(before[key] == after[key] for key in before if key != payer)
                    prior_payer, next_payer = dict(before[payer]), dict(after[payer])
                    payer_fee = prior_payer.pop('lamports') - next_payer.pop('lamports')
                    rollback = unchanged and prior_payer == next_payer and payer_fee >= 0
                    assert rollback, 'Failed transaction changed program account state'
                record = dict(sequence=counters['transactions'], vm=vm._focused_serial,
                              loaded_programs=loaded[id(vm)],
                              context=dict(current), clock=json.loads(vm.get_clock().to_json()),
                              transaction_base64=base64.b64encode(raw).decode(),
                              transaction_sha256=hashlib.sha256(raw).hexdigest(),
                              signatures=[str(s) for s in tx.signatures],
                              all_signatures_verified=True, signature_fields=len(checks),
                              before=before, after=after, metadata=json.loads(meta.to_json()),
                              rollback_except_payer_fee=rollback, payer_fee_lamports=payer_fee,
                              error=str(result.err()) if failed else None)
                stream.write((json.dumps(record, separators=(',', ':')) + '\n').encode())
                counters['transactions'] += 1
                counters['signature_fields'] += len(checks)
                return result
            LiteSVM.send_transaction = send
            rows = []
            for index, case in enumerate(cases()):
                values = {}
                for name, image in images.items():
                    current.update(index=index, image=name, instruction=case['instruction'],
                                   mint=case['mint'], label=case['label'])
                    values[name] = h.run(case['instruction'], amount=case.get('amount',1000000),
                                         maxbase=0 if case['instruction'] == 'withdraw' else 2**64-1,
                                         maxquote=0 if case['instruction'] == 'withdraw' else 2**64-1,
                                         overrides=mutate(case), candidate=image)
                row = dict(case={**case, **({'tlv': case['tlv'].hex()} if 'tlv' in case else {})},
                           **values, classification=classify(values['original']),
                           original_candidate_equal=observed(values['original']) == observed(values['candidate']),
                           control_candidate_equal=observed(values['control']) == observed(values['candidate']),
                           control_candidate_raw_logs_equal=values['control']['logs'] == values['candidate']['logs'],
                           original_candidate_raw_logs_equal=values['original']['logs'] == values['candidate']['logs'])
                rows.append(row)
                if (index + 1) % 12 == 0:
                    print('completed', index + 1, 'triples', flush=True)
    assert counters['vms'] == counters['transactions'] == 3 * len(rows)
    assert not native_acquire.__globals__['_cached']
    epoch_evidence = []
    for instruction in ('deposit', 'withdraw'):
        selected = {row['case']['label']: row for row in rows
                    if row['case']['instruction'] == instruction and row['case']['mint'] == 'quote'}
        for image in images:
            old = selected['older-epoch'][image]['amounts'][str(h.userquote)]
            at = selected['newer-epoch-at'][image]['amounts'][str(h.userquote)]
            after = selected['newer-epoch-after'][image]['amounts'][str(h.userquote)]
            assert old - at == 16 and at == after
            epoch_evidence.append(dict(instruction=instruction, image=image,
                                       older_user_quote=old, newer_at_user_quote=at,
                                       newer_after_user_quote=after, expected_cap_difference=16))
    assert all(sha(ROOT / path) == digest for path, digest in input_hashes.items())
    assert all(sha(images[name]) == digest for name, digest in image_hashes.items())
    mismatches = [i for i, row in enumerate(rows)
                  if not row['original_candidate_equal'] or not row['control_candidate_equal']]
    report = dict(scope='Fresh normally signed original/control/proposal liquidity triples. Full message account snapshots, raw metadata/logs and signed transactions retained. Base-mint cases are dependency controls; quote-mint UnsupportedQuoteMint6007 cases demonstrate decoder rejection. No Clock failure injection or whole-program identity claim.',
                  fresh_vm_environment=os.environ['PUMP_AMM_FRESH_VM'], image_sha256=image_hashes,
                  input_sha256=input_hashes, counts=counters, case_count=len(rows),
                  classifications=dict(Counter(row['classification'] for row in rows)),
                  epoch_selection_evidence=epoch_evidence,
                  mismatches=mismatches, cases=rows,
                  transaction_receipts=dict(path=receipts.name, sha256=sha(receipts)))
    args.output.write_text(json.dumps(report, separators=(',', ':')) + '\n')
    print(json.dumps({key: report[key] for key in ('case_count', 'counts', 'classifications', 'mismatches')}), flush=True)
    raise SystemExit(bool(mismatches))


if __name__ == '__main__':
    main()
