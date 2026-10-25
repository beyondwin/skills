# grok-video held-out shot check

Written 2026-10-25, before any still or clip in this study. The skill bytes stay
pinned. This file is the decision rule. Later numbers do not change it.

## What this measures

Three layers stay separate.

- Trigger: whether a fresh host loads the skill on a video request. Not measured
  here. This session follows the skill on purpose.
- Procedure: `plan_shot.py` on briefs that are not the paper boat or the yellow
  mug. The 13 planner tests passed before this file was finished. A plan that
  cannot be executed as written is a procedure fail, and no clip is spent on an
  invented prompt.
- Outcome: first-take pixels for the plans that are complete. The boat and the
  mug are the development shots. They are not cases here.

People, spoken lines, and fast action stay out. One clip per cell. There is no
standard error. A pass is a large gap, using the same end-still cutoff that
separated the mug skill take (about 2) from the bare mug take (about 50).

## Pinned bytes

| File | SHA-256 |
| --- | --- |
| `skills/grok-video/SKILL.md` | `b257dd21c27e883423cdc653be00dc1190b15786f240494386950a2abd83e7af` |
| `skills/grok-video/scripts/plan_shot.py` | `800cce1df6038a9f99f545446de761c5fee3850a523fab3a15a60a6105025bbc` |
| `skills/grok-video/references/shot-check.md` | `f899b0623c0a3392cb83c08aa1b42c9f9c42ccc4bed5d345bbad7d8bfc749401` |

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/grok-video -p 'test_*.py' -b` reported 13 tests, OK, before any generation.

## Briefs and plans

The planner output below is copied from the brief files in `briefs/`. Calls use
these strings unchanged.

Apple, travel right, 16:9, 6s, 720p. Pins: first and last.

- Start: `A red apple with a brown stem, large in frame, in the left third. Uncluttered background, soft daylight, photoreal. No text.`
- End edit: `Same scene, same light, same pose, same size. Move only a red apple with a brown stem to the right third. Do not turn it or change its size.`
- Video: `Locked camera. A red apple with a brown stem slides from where it sits in the opening frame to where it sits in the closing frame. The background stays fixed.`

Pitcher, travel left, 16:9, 6s, 720p. Pins: first and last.

- Start: `A blue ceramic pitcher, large in frame, in the right third. Uncluttered background, soft daylight, photoreal. No text.`
- End edit: `Same scene, same light, same pose, same size. Move only a blue ceramic pitcher to the left third. Do not turn it or change its size.`
- Video: `Locked camera. A blue ceramic pitcher slides from where it sits in the opening frame to where it sits in the closing frame. The background stays fixed.`

Balloon, travel right, 9:16, 6s, 720p. Pins: first and last.

- Start: `A purple balloon, large in frame, in the left third. Uncluttered background, soft daylight, photoreal. No text.`
- End edit: `Same scene, same light, same pose, same size. Move only a purple balloon to the right third. Do not turn it or change its size.`
- Video: `Locked camera. A purple balloon slides from where it sits in the opening frame to where it sits in the closing frame. The background stays fixed.`

Cactus is a procedure case, not a pixel case. Brief: subject `a green cactus in a terracotta pot`, action `stays still`. The plan status is `plan`, mode `hold`, pins `same_image`, and `start_prompt` is empty. The video line is `Slow push-in. A green cactus in a terracotta pot stays where it is. stays still. The background stays fixed.` An empty start prompt cannot be sent to `image_gen`. This study does not invent a still prompt and does not generate that clip.

Offline probes of the same subject, not video calls: action `stay`, action `제자리`, and mode `hold` with no action produce a clean hold sentence and still an empty `start_prompt`. Action `push-in` appends the raw action, same as `stays still`.

## Still check before a travel clip

Measure the subject width on the opening still and the end still with
`score_clip.py --image` and the mask below. If the end width differs from the start width by more than 15% of the
start width, or the stem, handle, or balloon knot faces the other way, run the
same end edit once more and keep the still whose width is closer to the start.
Do not spend that retry to chase a prettier picture. Record both widths.

After the opening still exists, and before `reference_to_video`, name two
landmarks in that still in `landmarks.md`. A last frame that lacks a named
landmark fails even if the numeric gate passes.

## Bare contrast

One clip, not a skill plan. Same apple opening still as `first_frame` only.
Prompt, unchanged: `The red apple moves across the counter, cinematic.`
Duration 6, 720p, 16:9. No last frame, no voice, no style rewrite.

## Pixel gate

Sample the first frame at 0s, the middle at 3s, and the last 0.04s before the
end. If a sample's mean channel value is below 8, take one frame 0.1s earlier
and record the shift.

Erratum, same day, before any accepted score: `ffmpeg -sseof -0.04` returned
an empty packet and exit 0. Seeking to the container duration minus 0.04s
(6.002s on these 6.042s files) was also empty. The reader then steps back by
0.05s at a time, up to 0.20s, and keeps the first non-empty frame. The gates
do not change. Resize a still to the video frame with ffmpeg bilinear before
comparing. Difference is the mean of `|dr|+|dg|+|db|` over 3, on a 0–255 scale.

Mask, largest 4-connected component:

- Apple: `r > 150`, `g < 110`, `b < 110`, `r > g + 50`, `r > b + 50`.
- Pitcher: `b > 130`, `b > r + 30`, `b > g + 15`, `r < 160`, `g < 190`.
- Balloon: `r > 70`, `b > 70`, `g < 140`, `r > g + 20`, `b > g + 20`, `abs(r - b) < 90`.

If that component is under 0.5% of the frame or over 40% of the frame, the
automatic score is missing, not a pass and not a fail.

Travel pass, all three:

1. Centroid shift on x is at least 0.20 of the frame width, positive for the apple and the balloon, negative for the pitcher.
2. Last-frame difference against the kept end still is under 15.
3. Both named landmarks from `landmarks.md` are still visible in the last frame.

Background difference, on pixels outside both subject masks, is reported and is
not a gate. The earlier cutoff of 25 failed on wood grain while the scene held.

The bare clip passes this travel gate only with the apple rules against the
skill's kept end still. Between 15 and 40 on that difference is inconclusive,
not a pass. At or above 40 is a miss against the prepared end.

## Decision

The pinned travel method generalizes to these held-out shots if at least 2 of
the 3 first takes pass, and the bare apple does not pass the same gate. If the
bare apple also passes, this subject shows no measured need for the end pin.
If fewer than 2 first takes pass, the method did not generalize here.

A first take that fails may be corrected once, by the skill rule: rebuild the
end still from the opening with the same edit line and generate again. The
correction is a separate result. It does not change the first-take count.

No skill file changes in this study. Clips and stills stay out of git.
