# Plan

Write `plan.md` from `brief.md` and `research/ledger.md`. The plan is what the writers follow
and what the gate checks against, so every chapter row must be concrete.

## Sections of plan.md

1. **Promise map.** Each promise in `brief.md` and the chapter that delivers it. Every promise
   has at least one chapter; a chapter with no promise needs a reason or is cut.
2. **Chapters.** For each chapter:
   - title and one-sentence reader promise
   - the reader's question when the chapter opens
   - three to six sections, each with the ledger IDs it rests on
   - opening technique and closing technique (see below)
   - figures: what the figure shows and why prose alone is weaker; mermaid for structure and flow
   - target length in Korean characters
3. **Term table.** One row per term whose spelling could drift:

   ```markdown
   | 표기 | 피할 표기 | 첫 등장 설명 |
   | --- | --- | --- |
   | 웹훅 | 웹 훅, webhook | 웹훅(webhook): 이벤트가 생기면 서버가 다른 서버로 보내는 요청 |
   ```

   `book_check.py` reads the first two columns. Keep that header exactly.
4. **Gaps.** Facts the plan needs but the ledger lacks. Fill them now or drop the section.

## Openings and closings

Pick per chapter from these, and do not give two adjacent chapters the same one:

- Openings: a concrete scene or incident from the sources, a question the reader would ask,
  a surprising number from the ledger, a before/after contrast, a short failure story.
- Closings: a one-paragraph summary of what the reader can now do, a checklist, a question the
  next chapter answers (no "다음 장에서는" phrasing), a callback to the opening scene.

## Showing the plan

When you stop for approval, show: the chapter list with promises, the opening and closing per
chapter, the term table, the gaps, and the defaults you chose in the brief. Keep it scannable.
