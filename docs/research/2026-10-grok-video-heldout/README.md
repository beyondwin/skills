# grok-video held-out travel check

Historical study. `grok-video` was retired on 2026-10-28. The commands and
support observations below describe the original study, not a currently
installable product. See the [retirement decision](../../learning/cases/2026-10-28-retire-image-workbench-and-simplify-repository.md).

Date: 2026-10-25. Environment: macOS, this Grok session, `reference_to_video`.
The skill bytes are the hashes in [protocol.md](protocol.md). They were not
edited after those hashes were written. Clips stay in the session folder and
are not committed.

## How a skill like this should be scored

Three layers, scored apart:

1. Trigger. Does a fresh host load the skill on a video request and stay quiet
   on a still? This session followed the skill on purpose, so it does not
   measure that.
2. Procedure. Does `plan_shot.py` return a plan that can be executed as
   written? The 13 unit tests passed before any clip. A plan with an empty
   prompt is a fail, and no clip is spent on a prompt the plan did not write.
3. Outcome. On subjects that were not used to write the skill, does the first
   take hit a gate written down before the calls? Here that is displacement,
   last-frame difference against the pinned end still, and two landmarks named
   from the opening still before the clip existed.

The development shots, the paper boat and the yellow mug, were not reused.
One bare sentence on the same apple opening still is the contrast. One take
per cell. The thresholds sit in the gap already seen on the mug: end-still
difference about 2 versus about 50. Background difference is reported and is
not a gate. The rule, the masks, and the keep-the-closer-width rule are in
[protocol.md](protocol.md).

## Decision

The pre-registered rule was: at least 2 of 3 skill travels pass, and the bare
apple does not pass the same gate. That happened. Apple and balloon passed.
The pitcher failed. The bare apple missed the prepared end.

That pass is not a clean-slide result. The apple's middle frame turned the
stem sideways, and the end still is a smaller apple than the cropped opening.
The gate looked at the last frame, so it passed. The pitcher's end still was
mirrored on both edits; the width rule kept the closer one; the clip followed
it and the handle was on the left at the end.

| Clip | File | dx | End difference | Background difference | Gate |
| --- | --- | ---: | ---: | ---: | --- |
| Apple, pinned | `videos/22.mp4` | +0.438 | 1.804 | 95.680 | pass |
| Pitcher, pinned | `videos/21.mp4` | -0.361 | 2.097 | 56.057 | fail |
| Balloon, 9:16, pinned | `videos/24.mp4` | +0.513 | 1.987 | 5.713 | pass |
| Apple, bare sentence | `videos/23.mp4` | +0.472 | 47.030 | 85.487 | miss |

The cactus hold was a procedure fail before any image call. Action `stays still`
plans as hold, leaves `start_prompt` empty, and appends the raw action:
`stays still.` Actions `stay` and `제자리` produce a clean sentence and still
an empty start prompt. No hold clip was generated.

No correction clip was generated. The skill text would rebuild the end still
once after a turned subject. The pitcher is that case. The apple middle frame
is that case too, and the written gate had already passed it. Repair is
unmeasured.

## What the still step did

Each travel got one opening still and two end edits from that opening, using
the planner line unchanged. The second edit was required by the width or pose
rule. The closer width was kept.

- Apple width fraction 0.450, then 0.233 and 0.248. Kept `images/15.jpg`. Stem direction stayed. The kept still shows the whole apple; the opening is cropped.
- Pitcher width fraction 0.280, then 0.295 and 0.275. Kept `images/17.jpg`. Both edits put the handle on the left. The opening has it on the right.
- Balloon width fraction 0.603, then 0.503 and 0.464. Kept `images/12.jpg`. Ribbon and the beige edge stayed.

Numbers are in [results.json](results.json). Landmarks named before the clips
are in [landmarks.md](landmarks.md).

## Limits

Four clips, one each. No standard error. People, spoken lines, and fast action
were not generated. Host routing of the installed skill was not measured.
`ffmpeg -sseof` returned an empty packet on these files; the last sample is
the first non-empty frame from 0.05s before the end, as the protocol erratum
says. The scorer was fixed before any score was accepted.

Background difference was 96 on the passing apple and 6 on the passing balloon.
The same room can sit near 56 when the subject and its shadow move. That number
does not, by itself, say the scene was replaced.

The skill files were not changed.
