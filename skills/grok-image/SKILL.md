---
name: grok-image
description: Use when the user asks to generate or edit a still image with Grok. Do not use for an image-workbench project file, a video, an SVG, a chart, interface code, or a prompt gallery.
license: Apache-2.0
metadata:
  version: "1.0.0"
---

# Grok Image

Turn a still-image request into one concrete prompt, then call the host image tool.

## Gate

Activate when the user asks for a new still or an edit of one. A project file that must be saved and inspected belongs to image-workbench, and only when that skill is invoked. Video is out of scope.

## Fill or ask

Ask one question and do not generate when any of these is missing:

- a depictable subject
- a number, a wording, or an identity that is the point of the request
- a reference image for a named real person

Fill everything else from the named subject. Add one setting, the materials and counts that belong to that subject, one camera angle, light that makes the subject readable, the colors, and the crop. A photograph uses `3:2` unless the use names another ratio the current tool accepts.

## Prompt

Write one scene in this order:

1. Subject: what it is, its form, what holds it, and the setting.
2. The parts you can point at, with counts and materials.
3. One camera angle.
4. Light: where it comes from, how hard it is, and that the subject is bright enough to read.
5. The colors of the subject and the setting.
6. The crop, and that there is one frame.

State what is in the picture. Do not add a quality stack, a film-stock lead, or a list of things to leave out. If the user already wrote this shape, keep their sentences and add only a missing count, material, or light.

For an edit, name the change first, then one sentence that keeps the subject, angle, and crop. Call `image_edit` with the source. A new subject uses `image_gen`.

Set `aspect_ratio` to a value the current tool lists. Use `3:2` for a still photograph, `1:1` for a mark, `16:9` for a wide frame, and `9:16` for a tall frame.

## Check

Open the image. Locate each named object once. Compare the count, the material, and the crop with the prompt. If one named item failed, call the tool once more with the full original prompt plus that one fix. Then stop. Report the path and whether the named items matched.

A moderation block ends the attempt.

## References

- [Sources](references/sources.md)
