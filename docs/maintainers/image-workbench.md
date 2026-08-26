# image-workbench change protocol

Keep route, authorization, ImageSpec, rubric, inspector, fixtures, and version in lockstep. Public install guidance lives in `docs/ko/` and `docs/en/`, not in the installed payload. This skill is Codex-only.

## Contract changes

If trigger, mode, or authorization changes, update `skills/image-workbench/SKILL.md`, positive fixtures, near-miss fixtures, and the paired public guides in the same change. Reconfirm the read-only boundary of `brief`/`audit` and the explicit authorization of generate/edit with fixtures.

## ImageSpec and rubric changes

ImageSpec, input role, and route changes synchronize the skill, [ImageSpec reference](../../skills/image-workbench/references/image-spec.md), and fixtures. If acceptance changes, update [quality rubric](../../skills/image-workbench/references/quality-rubric.md) in the same change. Status or handoff changes update the rubric, evaluator, fixtures, and public guides together.

## Evidence changes

A provider or source claim needs a direct authoritative locator, checked date, adopted idea, and rejected boundary, and it does not automatically change runtime behavior. To use a new external repository, record the immutable revision, the license file read at that revision, and the reuse boundary in [sources.md](../../skills/image-workbench/references/sources.md). A license can be a condition on code and still not grant rights in a prompt, gallery, or example image.

## Fixture and inspector changes

Change fixture schema or judgment rules by updating evaluator self-tests and positive/near-miss fixtures first, confirming RED, then implementing. Inspector output changes update `tests/image-workbench/test_inspect_asset.py`, evaluator full-scope expectation, and public docs together; bump SemVer when behavior changes.

The runtime inspector is `skills/image-workbench/scripts/inspect_asset.py`. Tests for it live in `tests/image-workbench/test_inspect_asset.py`; the runtime script must not contain a unittest suite. Invoke the inspector from the actual skill root.

Offline fixtures are not proof of image quality. Live image canaries are opt-in and reported separately. Evaluator or inspector command or package path changes stay synchronized with `tests/image-workbench/run.py` and `python3 scripts/verify.py`.

## Versioning

A behavior change bumps SemVer in `SKILL.md` `metadata.version`. Wording-only documentation changes do not require a version bump unless behavior also changes. A provider source refresh that keeps adopted/rejected boundaries and behavior does not by itself require a version bump.

## Required verification

```bash
python3 scripts/verify.py
python3 tests/image-workbench/run.py --self-test
python3 tests/image-workbench/run.py --scope full
python3 -m unittest discover -s tests/image-workbench -p 'test_*.py'
git diff --check
```

Live image canaries remain opt-in and are reported separately from this offline acceptance, with status, cost/consent boundary, and output evidence kept distinct.
