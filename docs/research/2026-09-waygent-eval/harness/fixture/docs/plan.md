# 문체 입히기 구현 계획

설계서: `docs/design.md`. 동작은 설계서를 따릅니다. 이 계획은 순서와 이름만 정합니다.

## 공통

- 작업 브랜치 `work`에서 합니다. `main`에는 커밋하지 않습니다. Task마다 커밋합니다.
- 시험: `python3 -m unittest discover -s tests -t .` 가 끝날 때 모두 통과해야 합니다.
- 표준 라이브러리만 씁니다.
- 이름과 시그니처는 아래 그대로 둡니다. 다른 팀이 이 이름으로 UI를 붙입니다.

## Task 1. 저장소 버전

파일: `promptops/store.py` · 설계 4, 6, 8장

- `Prompt.version: int`. `create`는 버전 1.
- `VersionConflict` 예외, 속성 `current_version: int`.
- `PromptStore.save(pid, body, expected_version) -> Prompt`. 없으면 `PromptMissing`.
- `put`은 없앱니다.

## Task 2. 편집 세션

파일: `promptops/session.py` · 설계 4장

`EditSession(store, pid)`

- 속성 `body`, `base_version`, `dirty`, `conflict`, `missing`.
- `edit(body)`, `save() -> Prompt`, `reload()`, `discard()`.
- 사라진 대상의 `save()`는 `PromptMissing`.

## Task 3. 일괄 문체 입히기

파일: `promptops/batch.py` · 설계 3, 4, 5장

`BatchRun(store, model, pids, *, style, model_name, limit=3)`

- `await run.run() -> dict[str, str]`. pid마다 결과 하나: `"applied"`, `"rejected"`,
  `"failed:conflict"`, `"failed:missing"`, `"failed:error"`, `"cancelled"`.
- `run.outcomes`(끝난 항목), `run.counts`(`applied`, `rejected`, `failed`, `cancelled`, `total`),
  `run.state`(`"idle"`, `"running"`, `"done"`, `"cancelled"`).

## Task 4. 멈춤과 잠금

파일: `promptops/batch.py` · 설계 3장

- `run.cancel()`: 동기 메서드. 시작 전, 도는 중, 끝난 뒤 언제 불러도 됩니다.
- `run.locked: bool`.

## Task 5. 작업 공간

파일: `promptops/workspace.py` · 설계 3장

`Workspace(store, model)`

- `selected_model`(처음 `"base"`), `selected_style`(처음 `"plain"`), `busy`.
- `await ws.run_batch(pids, limit=3) -> dict[str, str]`, `ws.cancel()`.
- 이미 도는 중이면 `Busy`(이 모듈에 정의).

## Task 6. 후보 만들고 고르기

파일: `promptops/candidates.py` · 설계 4, 5장

`await generate_candidates(store, model, pid, styles, *, model_name, limit=3) -> CandidateSet`

- `candidates: dict[str, str]`, `errors: dict[str, str]`, `base_version`, `all_failed`.
- `choose(style) -> Prompt`: 한 세트에서 한 번만(두 번째는 `RuntimeError`). 없는 문체나
  실패한 문체는 `KeyError`.

## Task 7. 일시적 실패 재시도

설계 5장. 모델을 부르는 모든 곳에 적용합니다.

## Task 8. 일괄 작업 이벤트

파일: `promptops/batch.py` · 설계 6장

- `batch.progress`: `applied`, `rejected`, `failed`, `cancelled`, `total`.
- `batch.finished`: `state`와 같은 숫자들.
- 이벤트는 `store.events`에 냅니다.

## Task 9. 일괄 작업 되돌리기

파일: `promptops/batch.py` · 설계 7장

- `run.undo() -> dict[str, str]`: 되돌린 pid는 `"restored"`, 건너뛴 pid는 `"skipped:changed"`
  또는 `"skipped:missing"`. 두 번째 호출은 `RuntimeError`. 끝나지 않은 작업이면 `RuntimeError`.

## Task 10. 작업 공간 되돌리기

파일: `promptops/workspace.py` · 설계 3, 7장

- `ws.undo_last() -> dict[str, str]`: 마지막으로 끝난 일괄 작업을 되돌립니다. 없으면 `{}`.
  도는 중이면 `Busy`.
