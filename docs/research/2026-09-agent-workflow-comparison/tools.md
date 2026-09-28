# Tools

What we found by reading and installing each repository as fetched on 2026-09-27.
Size is the line count of installed instruction files (`.md`, `.yaml`, `.toml`),
counted the same way for every tool. Star counts were read with `gh api` on the same day.

## At a glance

| Tool | Version · commit | Kind | How it starts | Human checkpoints | Testing | Subagents | git | Instruction size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| superpowers | 6.4.1 · `5bf4e78` | Skill set + session-start hook | Automatic. The hook forces skill use on every task | Approval per path: spike/bounded/architectural | TDD iron law: failing test first | Implementer + reviewer per task when executing a plan | Worktree; asks how to integrate at the end | 15 skills, 8,856 lines |
| dryforge | 1.3.7 · `904f257` | Two phases: ready → go | Manual `/ready`, `/go` | 1 intent approval + 1 result acceptance | By risk. Test-first only for RISKY | Only for parallel work and independent checks | Feature branch in existing projects; asks before merge | 3 skills, 4,479 lines |
| workflow-orchestrator | 1.5.0 · `900d395` | Orchestrator only; delegates all work to workers | Natural language "with workflow-orchestrator" | Short interview only on unknowns that change the outcome | GATE (deterministic checks) + VERIFY (independent verification) | Required. Research, build, and verification are all delegated | Worktrees for parallel edits; strict delivery scope | 1 skill, 1,259 lines |
| mattpocock/skills | 1.2.3 · `c55ee46` | Small composable skills | Manual `/grill-with-docs` → `/to-spec` → `/implement` | Numbered question rounds, a recommendation per question | Red-green TDD only at agreed points | Used for fact finding and code review | Commits on the current branch, no PR | 38 skills, 4,222 lines |
| gstack | 1.91.2.0 · `01593aa` | Virtual team by role: CEO, engineering, QA, release | Manual `/office-hours` → `/plan-*` → `/review` → `/ship` | A decision summary once per decision | Not test-first. Test table in the plan, coverage audit in `/ship` | Specialist reviewers and an outside model in review | `/ship` pushes and opens a PR without asking | 54 skills, 37,719 lines in SKILL.md alone |
| BMAD-METHOD | npm 6.12.0 · repo `5e33d3c` | Agile personas + tracks by work size | Manual `/bmad-build`. Its broad description may also trigger it automatically | 1 batch of questions + a spec checkpoint | Test audit per edge-case table in the spec | Implementer and 3 reviewers in parallel | Stops on a dirty tree; 1 local commit, no push | 250 installed files, 13,996 lines |
| Spec Kit | `c00dc05` (after v1.0.12) | Constitution + spec-driven development | Manual `/speckit-constitution` → `specify` → `clarify` → `plan` → `tasks` → `implement` | Up to 3 spec questions, up to 5 in clarify | Test tasks optional; only on request | None | By default no branch and no commit | 43 installed files, 4,273 lines |
| OpenSpec | 1.13.2 · `79b6aa9` | Change proposals + delta specs | Manual `/opsx:propose` → `/opsx:apply` → `/opsx:archive` | Proposal review, archive menu | No TDD. Each task states how to verify it | None | No commits | 2,622 lines + `openspec` CLI |
| Ralph Wiggum | `88d488a` | bash loop; fresh context each iteration | A human starts the loop | Only the initial requirements conversation | Tests as backpressure on every iteration | The prompt recommends hundreds of parallel subagents | Commit, tag, and push every iteration (push blocked here) | 5 files, 120 lines |

Plain Claude Code (no skills) ran alongside as the control.

## superpowers — obra/superpowers 6.4.1

- What: 15 skills covering the whole development process: TDD, debugging,
  brainstorming, plan writing, subagent execution, code review, and branch wrap-up. A
  session-start hook injects the rule "if there is even a 1% chance a skill applies,
  you must use it".
- Flow: brainstorming classifies a request as spike, bounded, or architectural.
  Bounded shows a short design in chat and asks for approval. Architectural goes spec
  document → approval → writing-plans → choice of execution mode →
  subagent-driven-development.
- Strengths: it covers scenes outside the plan too, such as debugging
  (systematic-debugging), receiving and applying review, and verifying before calling
  work done. Similar skills exist in mattpocock (`diagnosing-bugs`, `code-review`), BMAD
  (`code-review`, `correct-course`), Spec Kit's bug extension, and gstack. The
  difference is that the session-start hook turns these skills on without a human
  calling them.
- Weaknesses: the hook intervenes in every task. There are several human approval steps.
- Relation to other tools: this repository's `sddx` and `pre-sdd-review` currently take
  superpowers-shaped spec and plan files as input. Whether they accept other tools'
  plan files was not tested.

## dryforge — prekuter/dryforge 1.3.7

- What: three skills: `ready` (understand and approve the intent), `go` (build and
  verify), and `migration` (one-time conversion of an existing repository). The skill
  descriptions set `disable-model-invocation: true`, so they run only when a human
  calls them.
- Principle: "whose decision is this?" It does not ask what the code can answer, and
  it does not guess what the user should decide. When sources disagree it must ask. It
  does not trust its own scoring; checks that actually ran decide whether work is done.
- Output: `.dryforge/` (handoff, spec, plan; local), and after the first cycle a
  "harness" written into the repository: `CLAUDE.md`/`AGENTS.md` + `docs/`
  (architecture, business-rules, security, standards, and so on).
- Prerequisites: git, a clean working tree, and a pushed main. A single-author project
  whose v1.1.1 came out on 2026-06-12. 282 stars.

## workflow-orchestrator — jha0313/skills_repo 1.5.0

- What: the orchestrator never reads or edits code itself. It hands research,
  planning, building, verification, and review to worker subagents and manages only
  dependencies and evidence. Inspired by Firstmate.
- Verification: split into GATE (deterministic checks such as build and tests) and
  VERIFY (a verifier who did not build it checks real behavior). If a check could not
  run, it reports unverified rather than PASS.
- The same repository's other skills, `eval-writer` and `skill-evaluator`, are
  evaluation tools and were left out of this development-flow comparison.

## mattpocock/skills 1.2.3

- What: billed as "skills for real engineers". It criticizes GSD, BMAD, and Spec-Kit
  for letting the tool own the process, and instead composes small skills that leave the
  user in control at each step.
- Flow: `grill-with-docs` (question rounds + `CONTEXT.md` and ADR records) → `to-spec`
  → (`to-tickets` if needed) → `implement` (TDD → type check → tests → code review → commit).
- Traits: every question gets a number and a recommended answer. Fact finding is done
  by subagents instead of asking the user.
- Install prerequisite: a one-time per-repository setup skill must run first. For the
  probe, a script created the same files that skill writes.

## gstack — garrytan/gstack 1.91.2.0

- What: 54 skills in the roles of CEO, engineering manager, designer, staff reviewer,
  QA, security, and release engineer. It runs a Think → Plan → Build → Review → Test →
  Ship → Reflect sprint.
- Traits: a single skill can reach 40,000–50,000 tokens. It includes a browser-QA
  binary (bun build).
- git: `/ship` merges the base, commits, and then pushes and opens a PR without asking.
  The probe did not use `/ship` and set a local bare repository as origin.
- Found in the probe: the plan review (S1) and `/review` (S3) called the installed Codex
  CLI as an "outside opinion". That is a call to another provider from outside the
  isolated Claude session. In S2 it asked first whether sending data out was OK.

## BMAD-METHOD — npm bmad-method 6.12.0

- What: an agile method with analyst, PM, architect, developer, and UX personas, and
  tracks by work size (single-session build / epic / whole project).
- `bmad-build`: clarify → plan (write the spec) → approval checkpoint → subagent build →
  3 reviewers in parallel (blind-hunter, edge-case-hunter, verification-gap) → report.
  Small work with no open questions takes the oneshot path, which skips the checkpoint.
- Version note: the repository HEAD (6.13.0-next) is mid-change in how it installs. The
  probe used 6.12.0, the npm `latest`.

## Spec Kit — github/spec-kit

- What: the spec is the source of truth, and plans, tasks, and code derive from it.
  Project principles live in `.specify/memory/constitution.md` (the constitution).
- Flow: constitution → specify → clarify → plan → tasks → (analyze) → implement →
  converge. converge adds remaining work to `tasks.md` until the implementation matches
  the spec.
- Traits: commands are now `/speckit-*` skills (hyphenated). Test tasks appear only
  when the spec or constitution asks for them. The bug extension (`bug-assess`,
  `bug-fix`, `bug-test`) is optional.

## OpenSpec — @fission-ai/openspec 1.13.2

- What: each change gets a proposal, a delta spec (ADDED/MODIFIED), a design, and tasks
  under `openspec/changes/<name>/`. Archiving merges the delta into `openspec/specs/`.
- Traits: propose is blocked from implementing in the same turn. Every command calls
  the `openspec` CLI. It makes no git commits.

## Ralph Wiggum — ghuntley/how-to-ralph-wiggum

- What: a `while :; do cat PROMPT.md | claude -p; done` loop. Each iteration is a fresh
  context, and only `IMPLEMENTATION_PLAN.md` on disk carries state forward. The actual
  content is the "Ralph Playbook" written up by Clayton Farr, and there is no license file.
- Flow: requirements conversation with a human → `specs/*.md` → 1–2 planning loops →
  build loop (the single most important item → tests → commit → tag).
- Changed for the probe: the push line was removed and `git push` tool calls were
  blocked. Iterations were capped, and the loop stops when nothing changes. The prompt
  body is otherwise the original text.
