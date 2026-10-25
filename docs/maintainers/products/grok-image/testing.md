# grok-image testing

Offline fixtures: deterministic contract evidence only.

Live execution: local, explicit, optional, potentially billable, and never required by CI.

## Offline

The fixture directory is `tests/products/grok-image/`.

`python3 -m unittest discover -s tests/products/grok-image -p 'test_*.py'` checks that the description is trigger-only and that the prompt order, the ask gate, and the single repair are in `SKILL.md`.

It does not call a model and does not prove that a still matches the prompt.

## Live

On 2026-10-25 the same concrete shape was generated more than once for a Greek salad, for two red mugs and one yellow mug, and for a pour-over. The one-line request and a quality-keyword stack were the comparisons. Generated files stayed outside the repository. That session is not a CI gate and does not measure host auto-routing.
