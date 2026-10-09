# Korean Technical Writing — personal pilot

[한국어](README.ko.md)

Write technical explanations that help a reader understand causes, conditions and
next actions from actual evidence. Draft documents, runbooks, commits, PRs and handoffs. Version 0.2.1 is a personal Codex pilot, not a fourth supported
product in the parent repository. It uses the active model and has no required CLI,
model service, hook or linter. Git is needed when inspecting Git changes.

Copy this folder to `~/.codex/skills/ko-technical-writing/` without replacing an
existing installation. Start a new session so the skill catalog is refreshed.
Automatic selection remains enabled. Explicit use: `$ko-technical-writing`.

Examples:

- `Use $ko-technical-writing to draft a Korean handoff from docs/status.md.`
- `Write a Korean commit message describing only the staged changes.`
- `Draft a runbook from these operational notes, preserving failure branches.`

Ask for the output language, audience and file destination when they matter. Without
a request to save, the skill returns a draft. It does not authorize a Git commit,
PR submission, publication, test execution or deployment merely by drafting text.

Supplied-prose proofreading belongs to `korean-writing-editor`; this skill does not
require that editor to be installed. It also excludes translation-only tasks,
casual answers, code review itself and teacher-facing product prose.

This is an application of clarity principles, not ASD-STE100 certification or a
Korean meaning validator. Model review is fallible. See the parent study for the
tested environment and limitations. No global AGENTS or project policy is needed.

To uninstall, remove only the newly installed `ko-technical-writing` folder. No
other settings need reverting.

Version 0.2.1 adds reader-centered ordering, connected explanations, concrete Korean
verbs and an editing pass for repetition and unclear references. The companion study
compares model judgments; it does not establish human reading speed or comprehension.

The 0.2.1 correction addresses observed repetition, backward references in procedures
and overinterpretation of percentile metrics. Its separate repair tests are not the
0.2.0 masked comparison and must not inherit that comparison's scores.
