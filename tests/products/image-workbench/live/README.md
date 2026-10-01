# image-workbench live smoke

CI does not run these steps. Do not commit generated pictures, receipts,
prompts, or home paths like `/Users/...`.

Host check (do this before saying Grok is supported):

1. From the repository root, install the documented Python shortcut from
   `skills/image-workbench` to `$HOME/.agents/skills/image-workbench`.
2. `grok inspect` (and `grok inspect --json` if available) must show the
   skill name `image-workbench` and a path under
   `.agents/skills/image-workbench`.
3. This Grok session must have `image_gen` and `image_edit`.
4. Make one fake still-life (no real person). If the file lands in the
   session `images/` folder, copy it to a throwaway project file, run
   `python3 <skill-root>/scripts/inspect_asset.py <absolute-path>` with no
   `--output` (or one outside the skill folder), then delete the files. Do
   not git-add them.

Four checks (after the SKILL.md host table exists):

1. Find the skill: same `grok inspect` path check.
2. Call `/image-workbench` for a brief only. Do not make an image.
3. Ask for a project hero image without the slash command: the skill
   should start. Then a casual one-off picture request should not start it.
4. Make or edit one image: save a new project file, inspector pass, open
   it. Do not treat the chat preview path as the final file.

Write results only in `smoke-record.json`. Fields:

- `session_id`: the Grok session id of the run (required).
- `run_at`: ISO 8601 timestamp with a time zone, for example
  `2026-10-01T09:30:00+09:00` (required).
- `grok_identity`, `skill_version`, `probe`.
- `skill_md_sha256`: SHA-256 of `SKILL.md` with the frontmatter `metadata:`
  line and its indented lines removed (required). A version-only bump keeps
  it; any other change to `SKILL.md` needs a new smoke. From the repository
  root, print it with
  `python3 -c 'import sys; sys.path.insert(0, "tests/products/image-workbench"); import test_live_record as t; print(t.skill_binding_sha256(t.SKILL.read_bytes()))'`.
- `discovery`, `explicit_brief`, `implicit_and_near_miss`, `output_contract`:
  `pass`, `fail`, or `not_run`. The offline test requires all four `pass`.
- `inspector`: an object with the inspected `format`, `width`, and `height`
  (required).

Edit the record only after a real run. Do not refresh the hash, time, or
session without running the four checks on the current text.
