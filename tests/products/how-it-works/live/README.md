# how-it-works live smoke

This optional operator procedure records separate observations in a fresh session.
It is not CI. Calls may consume subscription/API quota. No live calls were made
for the 2.0.0 hardening work: current execution evidence is `not_measured`.

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
| `hop_ids` | `lexical` | H1/H2 IDs in Mermaid source match unique `1. **H1**` prose entries |
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

Provider-free check, then capture client versions:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
codex --version
claude --version
grok --version
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' /Applications/Cursor.app/Contents/Info.plist
```

Fresh ephemeral Codex, non-persistent Claude Code, and single-turn Grok
processes. Save output only under a `mktemp` directory:

```bash
how_it_works_smoke_tmp="$(mktemp -d)"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills '$how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' | tee "$how_it_works_smoke_tmp/codex-explicit.txt"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' | tee "$how_it_works_smoke_tmp/codex-implicit.txt"
codex exec --ephemeral --sandbox read-only --cd /Users/kws/source/private/skills 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' | tee "$how_it_works_smoke_tmp/codex-near-miss.txt"
claude --print --no-session-persistence --permission-mode plan '/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' | tee "$how_it_works_smoke_tmp/claude-explicit.txt"
claude --print --no-session-persistence --permission-mode plan 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' | tee "$how_it_works_smoke_tmp/claude-implicit.txt"
claude --print --no-session-persistence --permission-mode plan 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' | tee "$how_it_works_smoke_tmp/claude-near-miss.txt"
grok inspect --json
grok --single '/how-it-works DNS가 브라우저 요청에서 IP 주소가 되는 길을 보여줘' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-explicit.txt"
grok --single 'DNS 요청이 브라우저에서 어디를 거쳐 IP 주소가 되는지 길로 보여줘' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-implicit.txt"
grok --single 'DNS resolver 테스트 실패를 고쳐줘. 동작 설명은 하지 마.' --permission-mode plan --max-turns 1 | tee "$how_it_works_smoke_tmp/grok-near-miss.txt"
```

Cursor uses the installed desktop application. In a fresh Cursor window or
session, verify the skill through `/how-it-works` or `@how-it-works`, then run
explicit, implicit, and near-miss cases in separate new chats. Do not drive
Cursor with AppleScript, osascript, or CGEvent. Prefer Computer Use
(`node_repl` / `@oai/sky`) when that harness is available. If Computer Use is
absent in this run, record Cursor as `not_measured` and do not mark it
`supported`; that is this-run status, not a standing skip of desktop smoke.

After scoring, delete the temporary directory only when it matches a `mktemp`
path:

```bash
case "$how_it_works_smoke_tmp" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*)
    rm -rf -- "$how_it_works_smoke_tmp"
    ;;
  *)
    print -u2 -r -- "refusing unexpected temporary path: $how_it_works_smoke_tmp"
    exit 1
    ;;
esac
```

## Record and payload binding

Keep `smoke-record.json` byte-for-byte unchanged. It is schema 1, classified as
`historical-unbound`: the 2026-08-28 date, client versions, and verdicts describe
that historical run and have no payload hash or model binding. Codex `0.150.0`
and Claude Code `2.1.247` passed then; Grok `1.0.5` was `unsupported` after measured
failure; Cursor `3.17.21` was `not_measured` because Computer Use was unavailable.
None of these verdicts verifies the current 2.0.0 payload.

A future schema 2 record has exactly these top-level fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `2`, never a boolean |
| `product` | `how-it-works` |
| `product_version` | Nonempty actual release version from `load_product_release(Path).version` |
| `payload_sha256` | 64 lowercase hex digits from the existing `payload_sha256(Path)` |
| `model` | Actual nonempty observed model name, or `null` if unknown |
| `host` | `codex`, `claude-code`, `grok`, or `cursor`; acceptance is not product support |
| `client_version` | Nonempty observed client version |
| `runner_version` | Nonempty version of the procedure/runner actually used |
| `executed_on` | Actual execution date, accepted by Python `date.fromisoformat` |
| `cases` | Nonempty object keyed by case ID |

Each case has exactly `invocation` and `dimensions`. Invocation has one of the
three statuses above; dimensions has exactly `fence`, `hop_ids`, `skill_loading`,
`mermaid_syntax`, and `meaning`, each with the exact status/method shape above.
Extra fields, missing dimensions, and invalid evidence methods are rejected.
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

- `historical-unbound`: schema 1, with its historical host judgments untouched.
- `unbound`: valid schema 2 with unknown (`null`) model, even if version/hash differ.
- `different-payload`: known model, but version or hash differs from the current payload.
- `current-bounded`: known model and matching version/hash; this is metadata binding,
  not execution authentication, invocation success, or an all-dimensions quality verdict.

The pure module lives under product tests, outside the installed payload. Existing
schema 1 field/host/verdict checks remain separate from this binding function.
