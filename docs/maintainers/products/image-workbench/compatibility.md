# image-workbench compatibility

Supported hosts are `codex` and `grok`, as listed in the registry. Another
host with a similar image tool is not supported by that fact alone.

## Supported OS

macOS is the only supported OS. Windows and Linux are unsupported. CI may run
full verification on Ubuntu. That pass is not Linux support and is not macOS
support evidence.

## Required host abilities

- The skill is installed in a local skill folder and the host can read
  `SKILL.md`.
- `brief` and `audit` only need to read.
- `generate` and `edit` need the host's image tool and a way to open the
  result: Codex `image_gen` (generate and edit), or Grok
  `image_gen`/`image_edit`. If either is missing, do not claim to make or edit
  an image.

## Evidence without provider calls

The required evidence is `python3 scripts/verify.py --skill image-workbench`.
Offline fixtures prove only the routing, authorization, ImageSpec, handoff,
and inspector contracts. They do not prove image quality, permission for
commercial use, or an advantage over other providers.

## Limits of live evidence

Live image calls are local, explicit, and optional. They may cost money, and
CI does not require them. Do not describe an offline pass as a live image
result. Do not commit user images, private references, generated media,
credentials, or provider receipts.

The four-item Grok smoke record is
`tests/products/image-workbench/live/smoke-record.json`. It names the Grok
`session_id` and `run_at` of the run and is bound to `SKILL.md` without its
`metadata:` block, so only a version bump leaves it valid. Follow
[Testing](testing.md) and `tests/products/image-workbench/live/README.md` for
the steps.

## Adding a host

To claim support for a new host, run and pass all four checks on the same
build:

1. The host finds the skill.
2. It can be called with `$image-workbench` or `/image-workbench`.
3. A request for a project image turns it on, and a casual one-off picture
   does not.
4. brief/audit create no files, and an authorized generate/edit saves a
   project file.

Without that record, the host is not supported. The shared user guide is
[Compatibility](../../../users/en/compatibility.md).
