# Acceptance gate

Run `book_check.py check <ws>` first. Fix hard failures before the gate; the gate does not
rule on them. Then dispatch one fresh general-purpose subagent with the brief below.

## Gate brief

A plain review instruction with the workspace as input. A longer brief with eight named
criteria showed no measured difference from a plain review on seeded defects (24/24 versus
22/24), and this shorter brief also found 24/24, so the criteria list was dropped; see
`docs/research/2026-11-kws-book-writer-eval/` in the source repository.

```text
{ws}/manuscript.md는 출판을 앞둔 한국어 기술서 원고입니다. 당신은 이 원고를 쓰지 않았습니다.
출판 전에 반드시 고쳐야 할 오류를 찾아 주세요. 하나라도 있으면 판정은 BLOCK, 없으면 ACCEPT입니다.
각 문제마다 위치와 이유를 적어 주세요.

참고 자료: 독자와 약속은 {ws}/brief.md, 장 계획은 {ws}/plan.md, 사실과 출처는
{ws}/research/ledger.md, 기계 검사 결과는 {ws}/checks/check-report.md, 사실 수정 내역은
{ws}/checks/factcheck.md, 출처 주석이 달린 장 파일은 {ws}/chapters/에 있습니다.

결과를 {ws}/checks/acceptance.md에 덧붙여 쓰세요(없으면 만드세요). 다른 파일은 고치지 마세요.

## Round {r}
판정: ACCEPT | BLOCK
### 고쳐야 할 것
- {file}:{line} | "{quote}" | {why} | {fix}
### 메모
- {non-blocking notes}

마지막에 판정과 고쳐야 할 것의 개수를 답하세요.
```

## After the verdict

- Record it: `book_check.py accept <ws> --verdict ACCEPT|BLOCK --note "round {r}: {n} findings"`.
- ACCEPT: run `check <ws> --final`; done when it exits 0.
- BLOCK in round 1: fix each blocking finding in the chapter files, assemble, check. Dispatch
  one fresh gate subagent for round 2 that reads the round-1 findings and judges only those
  findings and the sentences you changed (list them with file:line), plus any new hard failure.
- BLOCK in round 2: stop and show the user the remaining findings. If the user accepts the
  book as is, record `--verdict USER_APPROVED --note "<the user's words>"`. If the user asks
  for fixes, apply them and run one more round-2-style judgment.
