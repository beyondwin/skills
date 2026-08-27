# graspic change protocol

Keep trigger, rung defaults, output chrome, visuals, Korean voice, stakes, fixtures, and version in lockstep. A prompt-only edit that leaves fixtures or the public guides stale is a contract break. Public install guidance lives in `docs/ko/` and `docs/en/`, not in the installed payload.

## Contract changes

Synchronize these files together. Do not ship a behavior change in only one of them.

- Trigger or near-miss change (`/graspic`, 원리부터, `/eli5` no-op): update `skills/graspic/SKILL.md` activation text, `tests/graspic/cases.json`, `tests/contract/test_graspic.py`, and the paired public guides.
- Rung default or alias change (길 default, jargon to 뼈대, 쉽게 is not 그림): update `SKILL.md` dump gate, fixtures, and the paired public guides.
- Output chrome, type recipe, or metaphor test: update `skills/graspic/references/output.md` and the relevant fixture ids.
- Visual channel: update `skills/graspic/references/visuals.md`. Do not add HTML artifacts or `image_gen` for structure.
- Korean voice: update `skills/graspic/references/korean.md`. Do not invoke `korean-writing-editor`.
- High-stakes banner: update `skills/graspic/references/stakes.md` with the exact banner bytes.

## Evidence changes

- Source or citation-policy change: update `skills/graspic/references/sources.md`. Do not invent paper IDs.
- Do not commit user topics, pressure transcripts, or private logs as Git fixtures.

## Fixture changes

Keep the five shape cases honest in `tests/graspic/cases.json` and `tests/contract/test_graspic.py`.

- `gate-dump-01` needs a question and no mermaid on the first turn.
- `html-01` needs mermaid and forbids HTML tags.
- `type-cmp-01` needs a table and a recommendation, not a tie.
- `scope-01` needs slice options, not an OSI dump.
- `ko-gloss-01` needs a `rebase` gloss and forbids `여러분` / `답니다`.
- Passing payload contracts proves file identity and forbidden strings. It does not prove live model quality.

## Versioning

- Behavior change: bump SemVer in `SKILL.md` `metadata.version`.
- Documentation-only wording change: do not bump the version unless behavior also changes.

## Required verification

```bash
python3 scripts/verify.py
python3 -m unittest tests.contract.test_graspic
git diff --check
```

Do not describe payload contracts as live invocation evidence. Keep `/eli5` out of this skill's invocation.
