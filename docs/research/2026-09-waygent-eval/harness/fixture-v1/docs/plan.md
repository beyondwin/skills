# 문체 입히기 기능 구현 계획

운영자가 여러 프롬프트에 모델로 새 문체를 입히고, 편집기에서 고치고, 후보 중 하나를 고르는
기능의 도메인 계층을 만듭니다. UI는 이 계획 밖입니다.

## 공통

- 작업 브랜치 `work`에서 합니다. `main`에는 커밋하지 않습니다. Task마다 커밋합니다.
- 시험: `python3 -m unittest discover -s tests -t .` 가 끝날 때 모두 통과해야 합니다.
- 표준 라이브러리만 씁니다. 동시 실행은 `promptops.concurrency.gather_limited`로 합니다.
- 모델 호출은 `await model.restyle(body, style, model_name)`입니다. `ModelRefused`(거절),
  `ModelError`(실패)를 낼 수 있습니다(`promptops.fake_model`).
- 이름과 시그니처는 아래에 적힌 그대로 둡니다. 다른 팀이 이 이름으로 UI를 붙입니다.

## 설계 원칙

1. 저장은 낙관적 잠금입니다. 읽을 때 본 버전이 아니면 저장하지 않습니다. 다른 사람의 변경을 조용히 덮어쓰는 일은 없어야 합니다.
2. 저장소는 내부 객체를 밖으로 내주지 않습니다. 받은 값을 고쳐도 저장소는 바뀌지 않습니다.
3. 오래 도는 작업은 어떻게 끝나든(완료, 취소, 예상 못 한 오류) 잠금을 풉니다. 화면이 영영 잠기면 안 됩니다.
4. 진행 중에 보이는 숫자는 끝난 항목만 셉니다. 끝난 뒤 숫자의 합은 전체 수와 같습니다.
5. 한 항목의 실패가 다른 항목을 멈추지 않습니다. 일부만 실패하면 성공한 것만 남습니다.
6. 작업은 시작할 때의 대상(모델, 문체)으로 끝까지 갑니다. 도중에 운영자가 선택을 바꿔도 이미 시작한 작업은 영향받지 않습니다.
7. 취소하면 그 뒤로는 아무것도 저장되지 않습니다.

## Task 1. 저장소 버전과 낙관적 잠금

파일: `promptops/store.py`

- `Prompt`에 `version: int`를 더합니다. `create`는 버전 1로 만듭니다.
- `VersionConflict(Exception)`을 더합니다. 속성 `current_version: int`.
- `PromptStore.save(pid, body, expected_version) -> Prompt`: 저장된 버전이 `expected_version`과 같을 때만 저장하고 버전을 1 올립니다. 다르면 `VersionConflict`, 없으면 `PromptMissing`.
- `put`은 없앱니다. 모든 쓰기는 `save`로 합니다.
- `get`, `create`, `save`가 돌려주는 `Prompt`는 복사본입니다.

## Task 2. 편집 세션

파일: `promptops/session.py`

`EditSession(store, pid)`: 편집기 폼 하나의 상태입니다. 만들 때 저장소에서 읽습니다.

- 속성: `body`(폼에 보이는 본문), `base_version`(폼이 기준으로 삼은 버전), `dirty`(저장 안 한 편집이 있음), `conflict`(편집 중에 저장소가 바뀜), `missing`(대상이 사라짐).
- `edit(body)`: 폼 본문을 바꿉니다.
- `save() -> Prompt`: `base_version` 기준으로 저장합니다. 성공하면 폼이 새 버전을 기준으로 삼습니다.
- `reload()`: 저장소를 다시 읽습니다. 폼은 저장소의 최신 상태를 반영해야 하지만, 저장하지 않은 편집은 잃지 않습니다. 편집 중인데 저장소가 바뀌었으면 `conflict`를 켭니다. 대상이 사라졌으면 `missing`을 켭니다(예외를 내지 않음).
- `discard()`: 편집을 버리고 저장소의 최신 상태로 돌아갑니다.
- 대상이 사라진 세션의 `save()`는 `PromptMissing`을 냅니다.

## Task 3. 일괄 문체 입히기

파일: `promptops/batch.py`

`BatchRun(store, model, pids, *, style, model_name, limit=3)`

- `await run.run() -> dict[str, str]`: 프롬프트마다 본문을 읽고, 모델로 문체를 입히고, 읽을 때의 버전으로 저장합니다. 동시에 최대 `limit`개.
- 결과는 pid마다 하나: `"applied"`, `"rejected"`(모델 거절, 저장 안 함), `"failed:conflict"`, `"failed:missing"`, `"failed:error"`(그 밖의 모든 오류), `"cancelled"`.
- `run.outcomes`: 지금까지 끝난 항목의 결과(dict).
- `run.counts`: `{"applied", "rejected", "failed", "cancelled", "total"}`. 원칙 4를 따릅니다.
- `run.state`: `"idle"` → `"running"` → `"done"` 또는 `"cancelled"`.

## Task 4. 취소와 잠금

파일: `promptops/batch.py`

- `run.cancel()`: 동기 메서드. 도는 중이면 남은 항목과 진행 중인 모델 호출을 멈춥니다. 끝나지 않은 항목은 `"cancelled"`, 상태는 `"cancelled"`. 끝난 뒤나 시작 전에 불러도 오류가 아닙니다. 시작 전에 불렀으면 `run()`은 아무 모델도 부르지 않고 모두 `"cancelled"`로 끝납니다.
- `run.locked`: 도는 동안에만 `True`. 원칙 3.
- 원칙 7.

## Task 5. 작업 공간과 대상 고정

파일: `promptops/workspace.py`

`Workspace(store, model)`: 운영자 화면 하나의 상태입니다.

- 속성 `selected_model: str`(처음 `"base"`), `selected_style: str`(처음 `"plain"`), `busy: bool`.
- `await ws.run_batch(pids, limit=3) -> dict[str, str]`: 지금 선택으로 `BatchRun`을 만들어 끝까지 돌리고 결과를 돌려줍니다. 도는 동안 `busy`. 이미 도는 중이면 `Busy`(이 모듈에 정의)를 냅니다.
- `ws.cancel()`: 도는 일괄 작업을 취소합니다. 없으면 아무 일도 하지 않습니다.
- 원칙 3, 6.

## Task 6. 후보 여러 개 만들고 고르기

파일: `promptops/candidates.py`

`await generate_candidates(store, model, pid, styles, *, model_name, limit=3) -> CandidateSet`

- 문체마다 후보 하나를 만듭니다(동시에 최대 `limit`개). 아직 저장하지 않습니다.
- `CandidateSet.candidates: dict[str, str]`(문체 → 후보 본문), `.errors: dict[str, str]`(실패한 문체 → 까닭), `.base_version`, `.all_failed: bool`.
- `CandidateSet.choose(style) -> Prompt`: 고른 후보 하나만 `base_version` 기준으로 저장합니다. 한 세트에서 한 번만 고를 수 있습니다(두 번째는 `RuntimeError`). 없는 문체나 실패한 문체는 `KeyError`이고 아무것도 저장하지 않습니다.
- 원칙 1, 5.
