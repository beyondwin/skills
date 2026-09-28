# korean-writing-editor compatibility

The only supported host is `codex`, as registered in the product registry
(`products.toml`). Do not claim support for any other host.

## Supported OS

The supported OS is macOS only. Windows and Linux are unsupported. CI can run
the full verification on Ubuntu, but that pass is neither Linux support nor
evidence of macOS support.

## Required host abilities

- Install into a local Agent Skills directory and read `SKILL.md`.
- Read the Korean text the user supplies and return the edit in chat.
- Handing work to another model (model delegation) is optional. Use it only
  when the host offers it; if delegation fails, continue on the current model.

## Evidence without model calls

The required evidence is `python3 scripts/verify.py --skill korean-writing-editor`.
Offline fixtures (fixed test examples run without a model) prove only the
deterministic contract. CI does not need credentials, model calls, or a live
smoke (a short check on a real host).

## Live evidence limits

Live runs are local, explicit, optional, and may cost money. Do not use an
offline pass as evidence of live quality or of support on another host. Do not
commit user Korean text, provider responses, or credentials.

Follow [Testing](testing.md) and
`tests/products/korean-writing-editor/live/README.md` for the procedure.

Run evidence comes from runner 18 (live runner version 18). Receipts from
older runners are rejected as malformed and cannot start or resume a run. A new
run needs a new run ID.

## Adding a host

To list a new host in the registry and public guides, all four smokes must
pass on the same build:

1. skill discovery
2. explicit call
3. intended implicit call, and no call on a near-miss (a similar request that
   is out of scope)
4. output contract (edited text or `diagnose` findings)

Without a record, the host is not supported. For the shared user guide, see
[Compatibility](../../../users/en/compatibility.md).
