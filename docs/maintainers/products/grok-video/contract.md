# grok-video contract

The planner in `skills/grok-video/scripts/plan_shot.py` is the source for the
prompt, pins, duration, ratio, resolution, and voice. `SKILL.md` tells the
host to run that script and follow the JSON. Do not restate a second prompt
recipe in the README.

## Trigger

Turn on for a request to generate, animate, or extend a Grok video, and for
`$grok-video` or `/grok-video`. Do not turn on for a still, a sprite sheet, a
diagram, hand-editing a video file, or image-workbench.

## Ask and fill

Ask only when the planner returns `ask`: missing subject, missing change,
style words with no motion, a spoken line, an unknown voice, a duration
outside 1–15 seconds, or a named person without a photo. Ask in the user's
language, then stop.

Otherwise fill 6 seconds, 720p, and 16:9. A phone, story, vertical, or shorts
request uses 9:16. A draft request uses 480p. Speech without travel holds on
one frame and uses voice `eve` unless the user named `ara`, `leo`, or `rex`.
An `exact_prompt` is the video prompt unchanged. Pins still follow travel or hold.

## Shot

Travel pins a generated or supplied opening still and an end still edited from
it. The edit may change position only. Hold pins the same still at both ends.
Do not `image_gen` a named person. Do not pin a middle keyframe on the first take.

The only video call is `reference_to_video`. An upgrade notice, a
zero-data-retention storage error, or a moderation block stops the job. Do not
reword a blocked prompt.

## Check

Look at the first, middle, and last frames. Accept travel when the subject
moved toward the end and the background is the same scene. One correction
rebuilds the end still. It does not add a keyframe to hide a pose change.

The measured reason is [shot-check](../../../../skills/grok-video/references/shot-check.md).
Offline planner tests do not prove a clip looks good.

A piece of several clips is [A finished Grok video](../../../users/en/grok-video-piece.md).
That page is not a second prompt recipe. Each clip still comes from the planner.

## Files to change together

- `skills/grok-video/SKILL.md`
- `skills/grok-video/scripts/plan_shot.py`
- `tests/products/grok-video/`
- the product READMEs when the user-visible ask or default changes
