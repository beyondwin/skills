# Chapter writers and the fact pass

## Writer brief

Dispatch one fresh general-purpose subagent per chapter. Send this, filled in:

```text
Write chapter {N} of a Korean book into {ws}/chapters/{NN}.md. Write no other file.

Read: {ws}/brief.md, {ws}/voice.md, the chapter {N} entry and the term table in {ws}/plan.md,
and the ledger entries {ids} in {ws}/research/ledger.md. The previous chapter ends like this:
{last 40 lines of the previous chapter, or "this is the first chapter"}.

Rules:
- Start the file with one heading line: "# {N}장. {title}". Sections use "##".
- Follow the planned opening ({opening}) and closing ({closing}). Target {length} Korean characters.
- Every fact comes from the listed ledger entries or the sources they cite. After a paragraph
  that states a fact, add a comment naming its entries: <!-- src: RA01, RB04 -->. Comments are
  removed from the reader's copy.
- If a needed fact is missing, do not invent it or pad around it. Leave one of these markers
  in the text and keep writing: {output of book_check.py markers}
- Figures: a mermaid code block followed by a caption line "그림 {N}-{k}. ...". Only where
  the plan asks for one.
- Refer to other chapters by number ("3장에서 본 것처럼") only for content the plan puts there.
- Never mention the writing process, agents, ledgers, or plans in the text.

Return: the file path, the character count, the ledger IDs you used, and every marker you
left with its reason.
```

## Fact pass

After every batch of up to three chapters, dispatch one fresh subagent:

```text
Check the facts in {ws}/chapters/{list}. For each sentence that states a number, name, date,
version, behavior of a system, or a claim about a source: compare it with the ledger entry in
its src comment and, when the entry cites a file or URL you can read, with that source.

Fix only facts. Do not change wording that is not wrong. For every fix, append to
{ws}/checks/factcheck.md:

### {file}:{line}
- before: {sentence}
- after: {sentence}
- basis: {ledger id and source}

List claims with no src comment that need one, and claims you could not verify, under
"## 미해결" in the same file. Return the number of fixes and the unresolved list.
```

Resolve unresolved items yourself from the sources, or replace them with a marker and tell
the user in the final report. Only questions the sources cannot answer go to the user.
