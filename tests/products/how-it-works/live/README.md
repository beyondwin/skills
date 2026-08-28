# how-it-works live smoke

This optional operator procedure scores fresh-session host behavior from
pass/fail from observable output. It is not CI. Calls may consume
subscription/API quota.

Do not use private or user prompts. Use only the three synthetic cases in
`cases.json`. Do not commit full responses, screenshots, generated media,
credentials, or billing receipts. Store temporary outputs outside the repository
and delete them after scoring.

Use a fresh session for every case. A provider-free contract pass is not live
evidence. If any host fails the required criteria on the same build after the
fix/retest loop, document it as unsupported in `products.toml` and active docs.
Do not invent a passing verdict.

## Cases

- `explicit-dns-path`
- `implicit-dns-path`
- `near-miss-debug`

## Required criteria

A host is `supported` only when all of the following pass:

1. Skill discovery
2. Explicit invocation
3. Intended implicit invocation and near-miss non-invocation
4. Complete Markdown, Mermaid source, and numbered hop list

Score only what the returned chat text shows.

| Expectation | Observable pass | Observable fail |
| --- | --- | --- |
| `discovered` | The host loads or names `how-it-works` as a skill, or emits the required chrome after an explicit invoke | The host cannot find the skill or treats the invoke as unknown text |
| `explicit` | Output follows the skill after `$how-it-works` or `/how-it-works` | The host ignores the explicit invoke |
| `implicit` | Output follows the skill without `$how-it-works` or `/how-it-works` | The host stays in a generic assistant reply and never enters the explanation flow |
| `claim` | A one-sentence claim is present (`## 한 줄` / `One sentence`, or equivalent) | No claim sentence |
| `mermaid` | A fenced `mermaid` block is present | No Mermaid source |
| `numbered_hops` | A numbered hop list is present | No numbered hops |
| `body` | A rung-specific body is present (`## 본문` / `Body`, or equivalent) | No body |
| `adjacent_slices` | Uncovered adjacent slices are present (`## 지금 다루지 않은 것` / `Adjacent slices`, or equivalent) | No adjacent-slice section |
| `next_move` | Exactly one next move is offered (`다음` / `Next`) | No next move, or a menu of many unrelated tasks |
| `not_activated` | The host does not enter the explanation gate, does not emit the required chrome, and tries to debug or refuse explanation | The host emits Mermaid/hop explanation chrome anyway |

`explicit-dns-path` must show `discovered`, `explicit`, `claim`, `mermaid`,
`numbered_hops`, `body`, `adjacent_slices`, and `next_move`.
`implicit-dns-path` must show `implicit`, `claim`, `mermaid`, and
`numbered_hops`. `near-miss-debug` must show `not_activated`.

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

## Record

`smoke-record.json` stores only `schema_version`, `executed_on`, and per-host
`host`, `client_version`, `cases`, and `verdict`. A host verdict is
`supported` only when every required case is `pass`.
