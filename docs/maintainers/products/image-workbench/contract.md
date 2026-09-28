# image-workbench contract

This document lists the rules image-workbench must keep. Keep these parts in
step with each other:

- route: which path a result takes (image generation, code, or vector)
- authorization: when the skill may make an image
- ImageSpec: the work spec written before any image call
- rubric: the scoring sheet that judges a result
- inspector: the checker for file format and size
- test fixtures and the version

Public install guidance lives in the product `README.md`/`README.ko.md` and in
`docs/users/`.

To make or edit an image, use only the Codex built-in image tool or Grok
`image_gen`/`image_edit`. A preview path that exists only in the chat is not a
final project file. In offline fixtures, `builtin_imagegen` means "call the
current host's image tool".

## Trigger and defaults

Turn on when the project needs a bitmap. Explicit calls are `$image-workbench`
or `/image-workbench`. The old `kws-` name is a mistyped call and does nothing.
A casual one-off picture is left to the host's own image feature.

Pick exactly one mode before acting: `brief`, `generate`, `edit`, or `audit`.

- `brief`, `audit`, comparison, and diagnosis are read-only and never
  authorize generation.
- Only a clear `generate` or `edit` request authorizes an image call.

## Output and routing

Not sent to image generation:

- Icons, screen UI, exact layouts, and SVG go to the code/vector path.
- Exact text, logos, and charts are not drawn whole; use a deterministic or
  mixed path.
- Diagrams go to SVG, Mermaid, HTML, or canvas.

Write an `ImageSpec` before running. Give each input image exactly one role:
`edit_target`, `subject_reference`, `style_reference`, or
`compositing_input`.

For a final project file, run `python3 scripts/inspect_asset.py <path>` from
the skill folder to check format and size. These numbers do not replace
looking at the image.

Inspector rules:

- Never write the result to the same file as the input image, including
  through a symlink or hard link.
- Leave input images untouched. An existing separate JSON report may be
  updated.
- It reads only basic PNG, JPEG, and WebP structure. It does not prove the
  image is good or that you hold rights to it. Always open final candidates.

The offline evaluator rejects making an image, saving a new file, or
overwriting on the brief, audit, and no-op paths. Allowing replacement does
not widen authorization for read-only modes.

## Safety and rights

- A reference image does not grant the right to copy a person, a trademark,
  or protected work.
- A license that covers code use does not automatically grant rights to
  prompts, galleries, or sample images.
- Stop when consent is unclear for people, trademarks, or sample images. This
  state is `hold`.
- Do not commit user images, private references, generated media,
  credentials, or provider receipts as test fixtures.

## Files to change together

When trigger, mode, or authorization changes, update these in the same change:

- `skills/image-workbench/SKILL.md`
- the positive fixtures and the mistyped-name fixtures
- the product READMEs and shared public guides

Recheck with fixtures that `brief`/`audit` stay read-only and that
generate/edit need explicit authorization.

Other changes:

- ImageSpec, input role, or route: align the skill, the
  [ImageSpec reference](../../../../skills/image-workbench/references/image-spec.md),
  and the fixtures.
- Acceptance criteria: update the
  [quality rubric](../../../../skills/image-workbench/references/quality-rubric.md)
  in the same change.
- State or handoff: update the rubric, evaluator, fixtures, and public guides
  together.

A claim about a provider or source needs a direct locator in the authoritative
original, the date checked, the idea adopted, and the rejected boundary. Such a
claim never changes runtime behavior by itself. To use a new external
repository, record in
[sources.md](../../../../skills/image-workbench/references/sources.md) the
immutable commit of that revision, the license file read at that revision, and
the reuse boundary.
