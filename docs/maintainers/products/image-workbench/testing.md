# image-workbench testing

Fixtures live in `tests/products/image-workbench/`. To change the fixture
format or a judging rule, first change the evaluator self-test and the
fixtures (positive and near-miss cases). See the test fail, then implement.

## Deterministic fixtures

Deterministic fixtures are offline cases that always give the same result
without a real image call.

- `tests/products/image-workbench/cases.json` and
  `tests/products/image-workbench/run.py` define the expected routing,
  authorization, ImageSpec, handoff, and inspector results.
- The runtime inspector is `skills/image-workbench/scripts/inspect_asset.py`.
  Its tests live in `tests/products/image-workbench/test_inspect_asset.py`.
  Do not put a unittest suite in the runtime script.
- When inspector output changes, update
  `tests/products/image-workbench/test_inspect_asset.py`, the evaluator
  full-scope expectations, and the public docs together. Bump SemVer when
  behavior changes.
- Call the inspector by its path under the real skill root
  (`python3 <skill-root>/scripts/inspect_asset.py <absolute-asset-path>`),
  not through a repo-relative `skills/` path. Keep any `--output` report
  outside the skill folder.
- When an evaluator or inspector command or package path changes, align
  `tests/products/image-workbench/run.py` and `python3 scripts/verify.py`.
- `test_payload_docs.py` checks, in a temporary standalone copy, that README
  relative links resolve inside the payload. Public docs URLs are checked only
  against the matching file in this repo; this does not prove a remote HTTP
  response.
- The evaluator checks the read-only boundary with the original 8 mutations
  plus 9 that corrupt expected and candidate together. It runs without a real
  image call.

There are 32 offline cases. They do not prove an image looks good. The live
Grok check steps are in `tests/products/image-workbench/live/README.md`; CI
does not run them. Record offline passes and live image results separately.

`test_live_record.py` binds the Grok claim to `live/smoke-record.json`: four
`pass` values, a `session_id`, an ISO `run_at` with a time zone, an
`inspector` object, and the SHA-256 of `SKILL.md` without its frontmatter
`metadata:` block. A version-only bump keeps a valid smoke; any other
`SKILL.md` change needs a new Grok smoke before the test passes again.

## Codex trigger eval, 2026-10-02

Recorded in full in the [skill trigger eval](../../../research/2026-10-skill-trigger-eval/README.md). Codex gpt-6-astra/high with every installed skill and plugin,
in a synthetic project with brand notes and PNG assets. SKILL.md was `95c1a397`, which is not
edited, so the Grok smoke binding holds.

- **Positives.** The skill loaded for 24 of 24 project raster requests: replacing the hero
  image, a transparent logo, an App Store size, a thumbnail, comparing two heroes, auditing a
  banner, onboarding art, colour correction, an OG plan, an asset audit, an app icon, and
  masking personal data. `imagegen` loaded with it on the generation requests.
- **Near-misses.** It loaded for 0 of 24: a casual cat picture, an SVG logo, a data chart, a
  React section, a prompt gallery, icon swaps, lazy loading, a PNG/WebP question, a Mermaid
  diagram, badges, slides, and an app recommendation.
- **Design.** 12 prompts per kind with 4 held out, two repeats each.

The description stays as it is. Grok was not part of this eval.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
IMAGE_WORKBENCH_EXTRACTED_ROOT=/path/to/extracted/image-workbench
IMAGE_WORKBENCH_INSPECTOR="$IMAGE_WORKBENCH_EXTRACTED_ROOT/scripts/inspect_asset.py" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full --skill-root "$IMAGE_WORKBENCH_EXTRACTED_ROOT"
git diff --check
```

The last two commands show the scope of the product smoke that the shared
`verify-download` runs on the extracted payload. Do not unpack the same
archive again by hand to repeat that check.

CI does not require real image generation. It may need a login and may cost
money. Do not describe an offline pass as "the image is good".
