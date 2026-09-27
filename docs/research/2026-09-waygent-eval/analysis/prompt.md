You are one of four independent analysts designing a lightweight coding-agent workflow skill named "waygent". Work read-only; do not modify files.

Inputs:
- Evidence pack: <evidence-pack>/evidence.md (user requirements, the user's own v26-vs-v27 measured report, and our 30-run probe of 9 harnesses: method, tools, results). Read it fully.
- Harness sources you may inspect for concrete mechanisms (read-only):
  superpowers: ~/.agents/plugins/superpowers/skills (esp. subagent-driven-development, test-driven-development, systematic-debugging, executing-plans)
  dryforge: <work>/dryforge ; workflow-orchestrator: <work>/plugins/wo ; mattpocock: <work>/tools/mattpocock ; gstack: <work>/tools/gstack ; BMAD: <work>/tools/bmad ; Spec Kit: <work>/tools/speckit ; OpenSpec: <work>/tools/openspec ; Ralph: <work>/tools/ralph

Task: produce an evidence-based design for waygent. The user wants: TDD; the main agent keeps its context small by giving each implementer subagent only its task; one review after each task's implementation; one full review when all tasks are done; NO re-review loops or ceremony; resume after interruption and error analysis are welcome; a thin wrapper around a strong model, not a framework.

Answer in English, max ~900 words, with these sections:
1. KEEP: mechanisms worth keeping, each tied to a specific piece of evidence (cite the report section / run / file path). Say what the mechanism costs.
2. DROP: mechanisms to leave out, each with the evidence that they cost more than they return.
3. OPEN QUESTIONS the evidence does NOT settle, and what measurement would settle each (be concrete: a benchmark task shape and metric).
4. DRAFT: a SKILL.md draft of at most 120 lines (frontmatter + body) for Claude Code, including: invocation gate, input (plan file or none), per-task dispatch brief shape, TDD expectation, review once per task (and when to skip), fixes without re-review, final full review once, progress/resume file and how resume reconciles with git, error-analysis step when a task fails, git discipline, model pinning.
5. RISKS of your own draft: where it could fail on a real run.
Be blunt; disagree with the user's premise where the evidence does.
