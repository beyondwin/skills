# image-workbench live smoke

CI does not run these steps. Do not commit generated images, receipts,
prompts, or absolute home paths.

Probe (before a support claim):

1. From the repository root, link
   `skills/image-workbench` to `$HOME/.agents/skills/image-workbench`
   with the documented Python installer.
2. `grok inspect` (and `grok inspect --json` if available) must list
   skill name `image-workbench` and a path ending in
   `.agents/skills/image-workbench`.
3. The running Grok session must expose `image_gen` and `image_edit`.
4. One synthetic non-personal `image_gen` result may land under a
   session `images/` path. Copy it to a throwaway project file and run
   `python3 scripts/inspect_asset.py` from the skill root. Delete the
   files. Do not git-add them.

Four-item smoke (after SKILL.md host table exists):

1. Discovery: same `grok inspect` path check.
2. Explicit `/image-workbench` brief: no image tool call.
3. Implicit project-raster activate; `kws-image-workbench` no-op.
4. One generate or edit: project `new_file`, inspector pass, open the
   candidate. Do not treat the session preview path as the final file.

Record results in `smoke-record.json` only. Fields: `date`,
`grok_identity`, `skill_version`, `skill_md_sha256`, `probe`,
`discovery`, `explicit_brief`, `implicit_and_near_miss`,
`output_contract`, optional inspector `format`/`width`/`height`.
Values for the four smokes are `pass`, `fail`, or `not_run`.
