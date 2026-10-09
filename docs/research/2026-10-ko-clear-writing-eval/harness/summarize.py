#!/usr/bin/env python3
"""Join local receipts with blinded grades; publish only aggregate/provenance data."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('live', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    grades = {}
    for count in (48, 23):
        mapping = json.loads((args.live / ('blind-map-%s.json' % count)).read_text())
        grade_path = args.live / ('final-grades-%s.json' % count)
        if not grade_path.exists():
            grade_path = args.live / ('grades-%s.json' % count)
        for grade in json.loads(grade_path.read_text()):
            label = mapping[grade['id']]
            grades[(label['host'], label['job_id'])] = grade
    jobs = {r['id']: r for r in json.loads((args.live / 'jobs.json').read_text())}
    runs = []
    for host in ('codex', 'opus', 'grok'):
        rows = json.loads((args.live / host / 'summary.json').read_text())
        assert len(rows) == 24 and len({r['job_id'] for r in rows}) == 24
        for raw in rows:
            job_id = raw['job_id']
            case, variant = job_id.split('--')
            complete = raw['status'] in ('ok', 'completed')
            row = {'host': host, 'case': case, 'condition': variant,
                   'status': 'completed' if complete else 'transport_failed',
                   'prompt_sha256': jobs[job_id]['prompt_sha256'],
                   'wall_seconds': raw['wall_seconds']}
            if not complete:
                row['reason'] = 'Authentication unavailable in the initial isolated Grok home; no generation. Counted as one dispatch; not retried.'
                runs.append(row)
                continue
            # Resolve inside the evidence bundle so archived raw paths remain portable.
            answer = (args.live / host / job_id / 'response.txt').read_text()
            grade = grades[(host, job_id)]
            row.update(response_sha256=hashlib.sha256(answer.encode()).hexdigest(),
                       output_characters=len(answer), grade_id=grade['id'],
                       semantic_pass=grade['semantic_pass'], format_pass=grade['format_pass'],
                       clarity=grade['clarity'], overhead=grade['overhead'],
                       grading_reason=grade['reason'])
            # Preserve the stricter preregistered scope rule as the primary result.
            row['primary_pass'] = grade['semantic_pass'] and grade['format_pass'] and grade['id'] != 'R020'
            if grade['id'] == 'R020':
                row['primary_failure'] = 'Frozen commit invariant prohibited interval claims; the output mentioned the unchanged interval. Supported fact, but outside the registered scope.'
            if case == 'json':
                parsed = json.loads(answer)
                assert set(parsed) == {'status', 'count', 'note'}
                assert parsed['status'] == 'not_run' and parsed['count'] is None
                assert isinstance(parsed['note'], str)
                row['json_shape_check'] = 'passed'
            if host == 'codex':
                identities = raw['actual_identity']
                row['actual_models'] = sorted({x['model'] for x in identities})
                row['actual_effort'] = sorted({x['effort'] for x in identities})
                row['identity_source'] = 'rollout turn_context'
                row['input_tokens_reported'] = sum(x['input_tokens'] for x in raw['usage'])
                row['output_tokens_reported'] = sum(x['output_tokens'] for x in raw['usage'])
                row['cached_tokens_reported'] = sum(x['cached_input_tokens'] for x in raw['usage'])
                row['tool_events'] = raw['tool_event_count']
            elif host == 'opus':
                row['actual_models'] = raw['actual_model']
                row['actual_effort'] = raw['actual_effort'] or ['not_exposed']
                row['identity_source'] = 'assistant message.model'
                usage = raw['usage']
                row['input_tokens_reported'] = sum(usage.get(k, 0) for k in
                    ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
                row['output_tokens_reported'] = usage['output_tokens']
                row['cached_tokens_reported'] = usage['cache_read_input_tokens']
                row['cli_cost_estimate_usd'] = raw['cost_usd']
                row['tool_events'] = raw['tool_calls']
            else:
                row['actual_models'] = sorted({x['model'] for x in raw['actual_model_identity_evidence']})
                row['actual_effort'] = ['High in runtime display name; no separate effort field']
                row['identity_source'] = 'Cursor system.init model'
                usage = raw['usage']
                row['input_tokens_reported'] = usage['inputTokens']
                row['output_tokens_reported'] = usage['outputTokens']
                row['cached_tokens_reported'] = usage['cacheReadTokens']
                row['tool_events'] = raw['tool_event_count']
            assert row['tool_events'] == 0
            runs.append(row)
    groups = []
    for host in ('codex', 'opus', 'grok'):
        completed = [r for r in runs if r['host'] == host and r['status'] == 'completed']
        common = set.intersection(*[{r['case'] for r in completed if r['condition'] == v}
                                    for v in ('baseline', 'core', 'full')])
        for variant in ('baseline', 'core', 'full'):
            all_rows = [r for r in completed if r['condition'] == variant]
            matched = [r for r in all_rows if r['case'] in common]
            group = {'host': host, 'condition': variant, 'completed': len(all_rows),
                     'semantic_pass': sum(r['semantic_pass'] for r in all_rows),
                     'primary_pass': sum(r['primary_pass'] for r in all_rows),
                     'format_pass': sum(r['format_pass'] for r in all_rows),
                     'overhead_cases': sum(r['overhead'] > 0 for r in all_rows),
                     'matched_cases': sorted(common), 'matched_n': len(matched),
                     'matched_output_characters': sum(r['output_characters'] for r in matched),
                     'input_tokens_reported': sum(r['input_tokens_reported'] for r in all_rows),
                     'output_tokens_reported': sum(r['output_tokens_reported'] for r in all_rows),
                     'matched_median_wall_seconds': round(statistics.median(r['wall_seconds'] for r in matched), 3)}
            if host == 'opus':
                group['cli_cost_estimate_usd'] = round(sum(r['cli_cost_estimate_usd'] for r in all_rows), 6)
            groups.append(group)
    result = {'schema_version': 1, 'experiment': 'E3', 'dispatches': len(runs),
              'completed': sum(r['status'] == 'completed' for r in runs),
              'grading': 'Separate blinded model reviewer plus source-based parent adjudication; not a reader study.',
              'adjudication': [{'grade_id': 'R020', 'original_semantic_pass': False,
                  'final_semantic_pass': True, 'primary_pass': False,
                  'reason': 'The unchanged interval is present in staged diff context, so the parent judged no factual drift before unmasking. Independent audit then identified conflict with frozen no interval/OAuth claim wording. Strict primary failure is retained; the alternative factual interpretation is secondary only.'}],
              'usage_limit': 'Provider-reported units are not normalized across hosts. Opus input includes cache creation/read; Codex and Cursor input use native reported totals. Cost is a CLI estimate, not billing.',
              'groups': groups, 'runs': sorted(runs, key=lambda r: (r['host'], r['case'], r['condition']))}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'dispatches': result['dispatches'], 'completed': result['completed'], 'groups': groups}, indent=2))


if __name__ == '__main__':
    main()
