# A finished Grok video

[한국어](../ko/grok-video-piece.md)

This page is how to build one piece from `grok-video` clips. It does not change the clip contract. The planner in `skills/grok-video/scripts/plan_shot.py` still owns each clip's prompt, pins, duration, ratio, resolution, and voice.

A piece is several clips cut together, then finished in an editor. The skill makes one clip. The 2026-10-25 measurements say whether a pinned scene survives the move. They do not score taste, acting, or a festival cut.

## Three layers

| Layer | What it decides | Evidence |
| --- | --- | --- |
| Still | Subject, light, material, and the frame you are willing to hold | A concrete still kept named objects in the [grok-image case](../../learning/cases/2026-10-25-grok-image-prompt.md). The mug clip followed the end still's size. |
| Clip | One change, with the ends pinned, at the filled 6 seconds and 720p | [Shot check](../../../skills/grok-video/references/shot-check.md) and the [pinned-shot case](../../learning/cases/2026-10-25-grok-video-pinned-shot.md). |
| Finish | Which frames you keep, the cut, grade, sound, and titles | Not measured. The skill joins extra beats with `ffmpeg -f concat` and `-c copy` when you ask for more than one. |

Do the still until it can stand as a frame. Then spend a clip on one change. Grade, letterbox, music, room tone, and on-screen words happen after the files exist. The video tool's filled resolutions are 480p for a draft and 720p otherwise. Duration is a whole number from 1 to 15 seconds, and the fill is 6.

## What the clips showed

Figures below are the published summaries. The shot-check note owns the boat method. The pinned-shot case owns the mug comparison. Both used one object. People, spoken lines, and fast action were not in those runs.

Pinned first and last frames, with the lock sentence, kept the paper boat's stream. Background difference was about 10, and the match to the prepared end still was about 2. The same travel sentence without those pins replaced the shot. Background difference was about 46 to 55. Saying the banks stay fixed, without an end pin, also kept the stream at about 10 and did not land on a prepared end still.

A middle still whose pose faced the camera turned the boat. A prompt that named mist and leaves and no destination left the boat near the center.

The yellow mug, planned and pinned, moved from about 0.35 to about 0.79 of the frame width. The last frame differed from the end still by 2.2. The handle stayed on the right, and the window and the table knot stayed. The same opening frame with only `The yellow mug moves across the table, cinematic.` moved the mug and replaced the room: background difference 60, a different window, different light, and no handle. The skill take's background-only difference was 27.9. A cutoff of 25, taken from the stream, did not fit the wood grain, so the case accepted the end-still match and the visible landmarks.

The end still was smaller than the opening. A second edit with the same line was smaller again, and the clip follows the still you keep. Edit position only. If the size or the pose changes, run that edit once more and keep the closer still. If that edit turns a handle, stem, or ribbon to the other side, do not pin it. A closer width does not rescue a mirrored still.

The same-day held-out travels are scored in [the travel study](../../research/2026-10-grok-video-heldout/README.md). The rule was written in [the protocol](../../research/2026-10-grok-video-heldout/protocol.md) before the clips. Apple and balloon passed. End difference was 1.8 and 2.0. The pitcher failed: both end edits put the handle on the other side, the closer width was kept, and the clip followed that still. The bare apple sentence, `The red apple moves across the counter, cinematic.`, moved the apple and missed the prepared end. End difference was 47, on a different table. The apple's middle frame turned the stem even though the last frame passed the gate. Background difference was 96 on that passing apple and 6 on the passing balloon, so the number alone does not say the room was replaced. The cactus hold produced an empty start prompt and no clip. No correction clip was generated.

## Order of work

1. Write the shots before any image or video call. One subject, one change, and one camera move per shot.
2. Make or supply the opening still. Keep the frame free of words, crowds, thin geometry, and heavy reflections. Those details warp when they move.
3. Stage the subject in the scene's light. A cut-out pasted on a backdrop animates as a separate layer.
4. For travel, make the end still from the opening by moving only the subject's position. Look at facing and size before you spend the clip. Pin the opening as `first_frame` and the end as `last_frame` only when the end still still faces the same way.
5. For a hold, pin the same still as both frames.
6. Generate that one clip. Leave the middle keyframe off the first take.
7. Open the first, middle, and last frames. Accept travel when the subject has moved toward the end and the background is still the same scene. One correction rebuilds the end still from the opening. It does not add a keyframe to hide a pose change.
8. Repeat at the same resolution and ratio. Join with `ffmpeg -f concat` and `-c copy`.
9. Finish grade, sound, and titles in an editor.

A named person needs a photograph. The planner asks for it and does not draw one from a name. Voices it already accepts are `ara`, `eve`, `leo`, and `rex`. Speech quality was not part of the pixel checks.

## Approaches set aside

A longer style sentence was the first candidate for a more finished look. On the mug it replaced the room. On the boat, atmosphere without a destination added mist and left the subject short of the end. The piece therefore spends its care on the still and on the two pinned frames.

A middle keyframe was a candidate for finer motion. The boat's middle still, posed toward the camera, turned the subject on an otherwise even path. The first take stays on the two ends.

Folding this page into `SKILL.md` was a candidate for making every video request plan a whole piece. The skill's job is one clip, and the finish layer has no measurement. The page stays here. The decision is the [finished-piece case](../../learning/cases/2026-10-25-grok-video-finished-piece.md).

## Limits

An offline planner pass does not mean a clip looks good. These notes do not show a result above 720p, a scored performance, or a finished soundtrack. A GitHub-path install of `grok-video` does not include this page. The installed clip rules remain the skill README and `SKILL.md`.
