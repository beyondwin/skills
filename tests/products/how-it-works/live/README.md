# how-it-works live smoke

This optional operator procedure records separate observations in a fresh session.
It is not CI. Calls may consume subscription/API quota. No live run of the current
payload is recorded: current execution evidence is `not_measured`.

Do not use private or user prompts. Use only the three synthetic cases in
`cases.json`. Do not commit full responses, screenshots, generated media,
credentials, or billing receipts. Store temporary outputs outside the repository
and delete them after scoring.

Use a fresh session for every case. A provider-free contract pass is not live
evidence. Product support remains Codex and Claude Code, independently of the
current measurement state. Do not calculate `supported` from a binding result or
rewrite the support registry because this run has no measurement.

## Cases and dimensions

`expect` describes the intended invocation and observation methods, not results.
The three synthetic prompts are unchanged:

- `explicit-dns-path`: judge explicit invocation; observe fence/hop IDs lexically
  and skill loading only from a host event.
- `implicit-dns-path`: judge intended implicit invocation with the same separate
  observations.
- `near-miss-debug`: judge only non-invocation. All five output dimensions stay
  `not_measured/not_run`; an explanation is not requested.

For invocation, record `pass`, `fail`, or `not_measured` against the case's intended
activation or non-activation. If activation cannot be observed, leave it unmeasured.
Mentioning the skill name or matching output chrome does not prove skill loading.

Every dimension has exactly `status` and `method` fields. Status is `pass`, `fail`,
or `not_measured`. A missing observation must be `not_measured/not_run`.

| Dimension | Method allowed for pass/fail | What it can establish |
| --- | --- | --- |
| `fence` | `lexical` | A nonempty, closed canonical Mermaid fence is present |
| `hop_ids` | `lexical` | H1/H2 IDs in Mermaid source match unique `1. **H1**` prose entries; a branch id such as `H3a` counts as `H3` |
| `skill_loading` | `host_event` | A separately observed host loading event |
| `mermaid_syntax` | `parser` or `renderer` | The result of an actually executed Mermaid parser/renderer |
| `meaning` | `semantic_review` | A separate review of causal and explanatory correctness |

`observe_text(text)` performs only the first two lexical checks. It never promotes
regex matches to loading, syntax, or meaning evidence. If the fence check fails,
hop IDs remain unmeasured. Broken Mermaid can pass these lexical checks.

Use an already executable parser/renderer only if it is actually run. This procedure
does not require installation. Causality, depth transitions, accessibility, and
syntax are not established by document markers or regex. Without the corresponding
observation, leave those claims unmeasured. Method labels supplied by an operator
are declarations: `record_binding` does not authenticate execution.

## Commands

Run every command from the repository root. Provider-free check, then capture
client versions:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
codex --version
claude --version
```

Fresh ephemeral Codex and non-persistent Claude Code processes, with JSON event
output. Save output only under a `mktemp` directory:

```bash
how_it_works_smoke_tmp="$(mktemp -d)"
codex exec --json --ephemeral --sandbox read-only --cd "$PWD" -o "$how_it_works_smoke_tmp/codex-explicit.md" '$how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' > "$how_it_works_smoke_tmp/codex-explicit.jsonl"
codex exec --json --ephemeral --sandbox read-only --cd "$PWD" -o "$how_it_works_smoke_tmp/codex-implicit.md" 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' > "$how_it_works_smoke_tmp/codex-implicit.jsonl"
codex exec --json --ephemeral --sandbox read-only --cd "$PWD" -o "$how_it_works_smoke_tmp/codex-near-miss.md" 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' > "$how_it_works_smoke_tmp/codex-near-miss.jsonl"
```

Claude Code runs isolated with `--setting-sources project --strict-mcp-config`, so it
loads only the skill copy inside each case's fresh fixture repository, not the user's
installed skills, settings, or MCP servers. Do not isolate with a fake `HOME`; that
logs `claude` out on macOS. Unset `CLAUDECODE` and `CLAUDE_CODE_*` first, and record
the SHA-256 of the `SKILL.md` the runs used:

```bash
unset CLAUDECODE $(env | sed -n 's/^\(CLAUDE_CODE_[A-Za-z0-9_]*\)=.*/\1/p')
shasum -a 256 skills/how-it-works/SKILL.md > "$how_it_works_smoke_tmp/skill.sha256"
for case_name in explicit implicit near-miss; do
  fixture="$how_it_works_smoke_tmp/fixture-$case_name"
  git init -q "$fixture"
  mkdir -p "$fixture/.claude/skills"
  ditto skills/how-it-works "$fixture/.claude/skills/how-it-works"
done
(cd "$how_it_works_smoke_tmp/fixture-explicit" && claude --print --output-format stream-json --verbose --setting-sources project --strict-mcp-config --no-session-persistence --permission-mode plan '/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘') > "$how_it_works_smoke_tmp/claude-explicit.jsonl"
(cd "$how_it_works_smoke_tmp/fixture-implicit" && claude --print --output-format stream-json --verbose --setting-sources project --strict-mcp-config --no-session-persistence --permission-mode plan 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘') > "$how_it_works_smoke_tmp/claude-implicit.jsonl"
(cd "$how_it_works_smoke_tmp/fixture-near-miss" && claude --print --output-format stream-json --verbose --setting-sources project --strict-mcp-config --no-session-persistence --permission-mode plan 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.') > "$how_it_works_smoke_tmp/claude-near-miss.jsonl"
```

`--setting-sources project` also skips the user's `effortLevel`, so these runs use the
session default effort. Take the model and effort that actually ran from the stream
(`message.model` and the top-level `effort`).

Reading the event streams:

- Reply text for `observe_text`: Codex writes the final message to the `-o` file.
  For Claude Code, take the `result` field of the final `"type":"result"` line:
  `jq -r 'select(.type=="result") | .result' claude-implicit.jsonl`.
- Claude Code `skill_loading`: a `tool_use` block named `Skill` whose input names
  `how-it-works`, inside an `assistant` event:
  `jq -c 'select(.type=="assistant") | .message.content[]? | select(.type=="tool_use" and .name=="Skill") | .input' claude-implicit.jsonl`.
  An explicit `/how-it-works` may be expanded by the client before the model runs;
  then the evidence is a `user` event that carries the skill body (it starts with
  `Base directory for this skill:` and names `how-it-works`).
- Codex `skill_loading`: an event for a command or file read that opens
  `how-it-works/SKILL.md`. A mention of the path in the reply text is not a loading
  event.
- If the stream shows none of these, record `skill_loading` as `not_measured/not_run`.
  For a near-miss case, the same events showing the skill was not loaded support an
  invocation `pass`.

After scoring, delete the temporary directory only when it matches a `mktemp`
path:

```bash
case "$how_it_works_smoke_tmp" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*)
    rm -rf -- "$how_it_works_smoke_tmp"
    ;;
  *)
    printf 'refusing unexpected temporary path: %s\n' "$how_it_works_smoke_tmp" >&2
    exit 1
    ;;
esac
```

## Record and payload binding

No live record is committed. A schema 2 record has exactly these top-level fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `2`, never a boolean |
| `product` | `how-it-works` |
| `product_version` | Nonempty actual release version from `load_product_release(Path).version` |
| `payload_sha256` | 64 lowercase hex digits from the existing `payload_sha256(Path)` |
| `model` | Actual nonempty observed model name, or `null` if unknown |
| `host` | `codex` or `claude-code`; acceptance is not product support |
| `client_version` | Nonempty observed client version |
| `runner_version` | Nonempty version of the procedure/runner actually used |
| `executed_on` | Actual execution date, accepted by Python `date.fromisoformat` |
| `cases` | Nonempty object keyed by case IDs from `cases.json` |

Each case has exactly `invocation` and `dimensions`. Invocation has one of the
three statuses above; dimensions has exactly `fence`, `hop_ids`, `skill_loading`,
`mermaid_syntax`, and `meaning`, each with the exact status/method shape above.
Extra fields, missing dimensions, invalid evidence methods, case IDs not in
`cases.json`, and a near-miss case (`not_activated`) with any output dimension other
than `not_measured` are rejected.
Do not invent dates, models, client/runner versions, or successful observations.
No new actual record is created by this implementation; synthetic unit fixtures
are not execution records.

Calculate the hash only after all payload changes are finished, using the shared
helper without another sorting or hashing algorithm:

```python
from pathlib import Path
from scripts.lib.product_contract import load_product_release, payload_sha256

skill_root = Path("skills/how-it-works")
current_version = load_product_release(skill_root).version
current_hash = payload_sha256(skill_root)
```

`record_binding(record, current_version=..., current_hash=...)` validates declared
metadata and returns:

- `unbound`: valid schema 2 with unknown (`null`) model, even if version/hash differ.
- `different-payload`: known model, but version or hash differs from the current payload.
- `current-bounded`: known model and matching version/hash; this is metadata binding,
  not execution authentication, invocation success, or an all-dimensions quality verdict.

The pure module lives under product tests, outside the installed payload.
