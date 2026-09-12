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
   `python3 scripts/inspect_asset.py` from the skill folder, then delete
   the files. Do not git-add them.

Four checks (after the SKILL.md host table exists):

1. Find the skill: same `grok inspect` path check.
2. Call `/image-workbench` for a brief only. Do not make an image.
3. Ask for a project hero image without the slash command: the skill
   should start. Then `kws-image-workbench …` should do nothing.
4. Make or edit one image: save a new project file, inspector pass, open
   it. Do not treat the chat preview path as the final file.

Write results only in `smoke-record.json`. Fields: `date`,
`grok_identity`, `skill_version`, `skill_md_sha256`, `probe`,
`discovery`, `explicit_brief`, `implicit_and_near_miss`,
`output_contract`, optional inspector `format`/`width`/`height`.
The four checks are `pass`, `fail`, or `not_run`.
