# grok-video testing

Planner tests live in `tests/products/grok-video/test_plan_shot.py`. Contract
phrases live in `test_contract.py`. They do not call a model.

The 2026-10-25 shot check used one paper boat, a busy stream and open water,
and two repeats of pinned and locked-only travel. Numbers and limits are in
[shot-check](../../../../skills/grok-video/references/shot-check.md). A later
held-out check on an apple, a pitcher, and a balloon is in
[the travel study](../../../research/2026-10-grok-video-heldout/README.md).
Neither run is a person, a spoken line, or a fast action. Do not commit the clips.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill grok-video
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/grok-video -p 'test_*.py'
```

CI does not generate video. An offline pass does not mean a clip looks good.
