# grok-image contract

Rules grok-image must keep. Change these together: `skills/grok-image/SKILL.md`, this contract, and `tests/products/grok-image/test_contract.py`.

## Trigger

Turn on when the user asks Grok to generate or edit a still. `$grok-image` and `/grok-image` also turn it on. The description is trigger-only.

Do not turn on for an image-workbench project file, a video, an SVG, a chart, interface code, or a prompt gallery.

## Before the call

Ask one question and do not generate when a depictable subject is missing, when a number, wording, or identity is the point and was not given, or when a named real person has no reference image.

Fill light, one camera angle, one setting, materials and counts that belong to the named subject, colors, and the crop. A photograph uses `3:2` unless the request names another ratio the current tool accepts.

## Prompt

One scene, in this order: subject and what holds it, pointable parts with counts and materials, one camera angle, light, colors, crop. State what is in the picture. Do not add a quality stack, a film-stock lead, or a list of things to leave out.

A new subject uses `image_gen`. An edit names the change first, then one keep sentence, and uses `image_edit`.

## After the call

Open the image. Locate each named object once. One failed named item allows one more call that keeps the full original prompt and adds that fix. Then stop. A moderation block ends the attempt.

Do not commit generated images, private references, or provider receipts.

## Host

Grok only. The prompt procedure was checked with Grok stills on 2026-10-25. Automatic routing of the installed skill is `not_measured`.
