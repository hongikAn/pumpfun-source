hashes=dict(original=sha(original),**{k:sha(images[k]['candidate']) for k in ('baseline','candidate')})
norm=lambda logs:[s for s in logs if not re.fullmatch(r'Program \S+ consumed \d+ of \d+ compute units',s)]
def audit(scope, triples, observed, expected_count, log_counts):
    assert observed['transaction_count'] == observed['signature_count'] == expected_count*3
    expected = Counter(); actual = Counter(); mismatches = Counter(); gains=losses=count=0
    for tx in observed['transactions']:
        assert tx['all_signatures_verified']
        signed = Transaction.from_bytes(base64.b64decode(tx['transaction_base64']))
        assert all(signed.verify_with_results())
        actual[(tx['amm_program_sha256'],tx['transaction_base64'],tx['logs_sha256'])] += 1
        for program in tx['loaded_programs'].values():
            if '/evidence/' in program['path']:
                name = 'evidence/' + program['path'].split('/evidence/',1)[1]
                assert manifest['repository_inputs'][name] == program['sha256']
    for triple in triples:
        o=triple['original']; count+=1
        for label,result in triple.items():
            assert {k:v for k,v in o.items() if k!='logs'} == {k:v for k,v in result.items() if k!='logs'}, (scope,count,label)
            expected[(hashes[label],result['transaction_base64'],sha(json.dumps(result['logs'],separators=(',',':')).encode()))] += 1
            mismatches[label] += norm(o['logs']) != norm(result['logs'])
        x,y=(norm(o['logs']) == norm(triple[k]['logs']) for k in ['baseline','candidate'])
        gains += not x and y; losses += x and not y
    assert count == expected_count and expected == actual and losses == 0
    assert (mismatches['baseline'],mismatches['candidate']) == log_counts
    assert gains == log_counts[0]-log_counts[1]
    print(scope,count,'case triples, non-compute log mismatches',log_counts)

for family,count,counts in [('liquidity',680,(0,0)),('buy',1011,(76,76)),('sell',575,(88,88))]:
    summary=record('runtime/'+family+'/summary.json')
    assert summary['artifact_sha256']==hashes and not any(summary['functional_mismatches'].values())
    assert summary['fresh_vm'] is False
    observed=record('runtime/'+family+'/observed.json.gz')
    assert observed['script_sha256']==sha(read('controllers/inverse_runtime.py'))
    with gzip.open(HERE/'runtime'/family/'triples.jsonl.gz','rt') as f:
        audit(family,(json.loads(line)['results'] for line in f),observed,count,counts)
focus=runpy.run_path(str(HERE/'focused_check.py'))
focus['verify'](hashes)
