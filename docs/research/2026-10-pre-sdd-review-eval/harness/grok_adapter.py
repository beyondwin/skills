"""Isolated Grok Build study adapter; raw provider artifacts stay under run/."""
import json
import os
import shutil
from pathlib import Path

EXECUTABLE = shutil.which('grok') or str(Path.home() / '.grok/bin/grok')
AUTH_SOURCE = Path.home() / '.grok/auth.json'
CONFIG = '''[cli]
auto_update = false
use_leader = false
[memory]
enabled = false
[memory_v2]
enabled = false
capture_enabled = false
automatic_dream_enabled = false
[compat.claude]
agents = false
hooks = false
mcps = false
rules = false
skills = false
[compat.cursor]
agents = false
hooks = false
mcps = false
rules = false
skills = false
[compat.codex]
hooks = false
skills = false
'''

def prepare(run, repo, prompt, arm):
    run, repo = Path(run).resolve(), Path(repo).resolve()
    home = run / 'home'
    gh = home / '.grok'
    gh.mkdir(parents=True, exist_ok=False)
    shutil.copy2(AUTH_SOURCE, gh / 'auth.json')
    (gh / 'auth.json').chmod(0o600)
    (gh / 'config.toml').write_text(CONFIG, encoding='utf-8')
    (run / 'prompt.txt').write_text(prompt, encoding='utf-8')
    env = os.environ.copy()
    # Credential values never appear in argv or adapter output.
    env.update(HOME=str(home), GROK_HOME=str(gh), GROK_MEMORY='0',
               GROK_DISABLE_AUTOUPDATER='1', GROK_CURSOR_MCPS_ENABLED='0',
               GROK_CLAUDE_MCPS_ENABLED='0', CMUX_GROK_HOOKS_DISABLED='1')
    skill = arm in ('skill', 'full_skill', 'full', 'native')
    argv = [EXECUTABLE, '--cwd', str(repo), '--model', 'grok-4.7',
            '--reasoning-effort', 'high', '--no-plan', '--disable-web-search',
            '--disallowed-tools', 'search_tool,use_tool', '--deny', 'MCPTool(*)',
            '--sandbox', 'read-only', '--always-approve', '--max-turns', '45',
            '--output-format', 'streaming-messages-json',
            '--prompt-file', str(run / 'prompt.txt')]
    if not skill:
        argv.append('--no-subagents')
    (run / 'adapter-request.json').write_text(json.dumps({
        'model': 'grok-4.7', 'effort': 'high', 'arm': arm,
        'native_subagents': skill, 'argv': argv,
        'isolation': {'fresh_home': True, 'memory': False,
                      'compat_discovery': False, 'sandbox': 'read-only'}
    }, indent=2), encoding='utf-8')
    return argv, env


def _json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _lines(path):
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return []
    result = []
    for line in lines:
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def parse(run):
    run = Path(run).resolve()
    frames = _lines(run / 'stdout.jsonl')
    init = next((x for x in frames if x.get('type') == 'system'
                 and x.get('subtype') == 'init'), {})
    results = [x for x in frames if x.get('type') == 'result']
    result = results[-1] if results else {}
    root_id = result.get('session_id') or init.get('session_id')
    sessions = []
    histories = []
    root_usage = None
    for path in (run / 'home' / '.grok' / 'sessions').rglob('summary.json'):
        value = _json(path)
        if not isinstance(value, dict):
            continue
        sid = value.get('info', {}).get('id')
        context = _json(path.parent / 'prompt_context.json') or {}
        samples = _lines(path.parent / 'chat_history.jsonl')
        observed = sorted(set((str(x.get('model_id')), str(x.get('reasoning_effort')))
                              for x in samples if x.get('model_id')))
        first_assistant = next((i for i, x in enumerate(samples) if x.get('type') == 'assistant'), len(samples))
        initial_types = [x.get('type') for x in samples[:first_assistant] if x.get('type') != 'reasoning']
        sessions.append({'session_id': sid, 'is_primary': sid == root_id,
                         'session_kind': value.get('session_kind'),
                         'initial_history_types': initial_types,
                         'requested_model': value.get('current_model_id'),
                         'configured_effort': value.get('reasoning_effort'),
                         'observed_model_effort': [list(x) for x in observed],
                         'memory_enabled': context.get('memory_enabled'),
                         'memory_v2_enabled': context.get('memory_v2_enabled')})
        histories.extend(samples)
        if sid == root_id:
            root_usage = _json(path.parent / 'usage.json')
    tool_calls = []
    for frame in frames:
        if frame.get('type') == 'assistant':
            for block in frame.get('message', {}).get('content', []):
                if block.get('type') == 'tool_use':
                    call = {'tool': block.get('name'), 'id': block.get('id')}
                    if block.get('name') == 'spawn_subagent':
                        inp = block.get('input', {})
                        call.update({'resume_from': inp.get('resume_from'),
                                     'background': inp.get('background', True),
                                     'prompt_characters': len(inp.get('prompt', ''))})
                    if block.get('name') == 'workflow':
                        inp = block.get('input', {})
                        call.update({'validate_only': inp.get('validate_only', False),
                                     'agent_budget': inp.get('agent_budget')})
                    tool_calls.append(call)
    usage = result.get('usage')
    ledger = (root_usage or {}).get('session', {})
    observed = sorted(set((str(x.get('model_id')), str(x.get('reasoning_effort')))
                          for x in histories if x.get('model_id')))
    return {'requested_model': 'grok-4.7', 'requested_effort': 'high',
            'reported_model': init.get('model'),
            'observed_model_effort': [list(x) for x in observed],
            'session_id': root_id, 'result_type': result.get('subtype'),
            'is_error': result.get('is_error'), 'stop_reason': result.get('stop_reason'),
            'duration_ms': result.get('duration_ms'),
            'duration_api_ms': result.get('duration_api_ms'),
            'model_rounds': result.get('num_turns'), 'usage': usage,
            'input_total_including_cache': ledger.get('inputTokens'),
            'reasoning_tokens': ledger.get('reasoningTokens'),
            'total_cost_usd': result.get('total_cost_usd'),
            'usage_scope': 'root result and root ledger include completed native child usage; do not add child ledgers',
            'ledger_model_calls_including_children': ledger.get('modelCalls'),
            'usage_model_ids': sorted((result.get('modelUsage') or {}).keys()),
            'usage_available': isinstance(usage, dict) and any(
                isinstance(v, (int,float)) and v > 0 for v in usage.values()),
            'sessions': sessions,
            'subagent_spawn_count': sum(c['tool'] == 'spawn_subagent' for c in tool_calls),
            'tool_counts': {name: sum(c['tool'] == name for c in tool_calls)
                            for name in sorted(set(c['tool'] for c in tool_calls))},
            'subagent_calls': [c for c in tool_calls if c['tool'] == 'spawn_subagent'],
            'workflow_calls': [c for c in tool_calls if c['tool'] == 'workflow'],
            'init_tools': init.get('tools'),
            'init_skills': init.get('skills'), 'init_mcp_servers': init.get('mcp_servers')}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps(parse(args.run), indent=2))
