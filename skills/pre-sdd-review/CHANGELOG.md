# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 5.0.0 - 2026-09-19

### Changed

- 여러 계획의 발견은 겹칠 수 있고, 수리는 한 번에 하나만 합니다. 종결에는 수리 diff가 필요합니다.
- 앞 수리가 뒤 계획이 읽는 파일을 바꾸면, 발견이 0건이어도 종결 재검토를 합니다.
- 호스트가 동시에 쓸 수 있는 검토자 수만큼 발견을 나누며, 같은 검토자를 다른 계획에 재사용하지 않습니다.
- 캠페인 시작 때 찍은 HEAD가 바뀌면 그 기준으로 `READY`를 내지 않습니다.
- 앞 계획이 `BLOCKED`여도 뒤 계획의 발견은 이어집니다.

### Notes

- Record schema는 4입니다. Handshake `cli_version`은 5.0.0입니다. GitHub 태그와 Release는 만들지 않습니다.

## 4.0.0 - 2026-09-18

### Added

- 판정을 내지 않는 선행 원장 패스. 계획을 둘 이상 이름 댄 요청은 판정을 내는 첫
  호출 앞에 공유 파일 원장과 실행 순서를 만들고 기계 점검을 한 번에 돌린다.
- `Repository reality at this plan's turn`. freshness 에 baseline 과 ledger 가
  들어가고, 선행 계획이 있으면 리뷰어가 기준선 재구성을 진술한다.
- 리뷰어 지시 계약. 발견 지시와 종결 지시를 나누고, 종결 지시는 앞 회차 기록
  원문과 아직 아무 기록도 가리키지 않은 Task 목록을 싣는다.
- 되풀이된 결함 갈래 넷과 복합 제약의 증명 표.
- `start`에 `--ledger`와 반복 가능한 `--prior-plan` 인자가 늘었다.
- 관찰 이상에 `head_start_not_ancestor_of_head_end`와
  `document_changed_without_repair_pass`가 늘었다.

### Changed

- 수정 허용 목록이 설계·계획·원장 셋이다. 원장은 유도된 증거이지 권위가 아니다.
- 부분 닫힘이 일급이다. 잔여는 새 ID 가 아니라 같은 기록의 남은 자리다.
- 영향 표가 비어 있고 종결 리뷰어가 소비자 없음을 확인한 수리는 패스를 먹지
  않는다. `summary.counts.costless_repairs`가 이 수를 센다.
- 원 기록과 `class` 및 갈래가 같은 발견은 위치가 달라도 unmapped 가 아니다.
- 인계 재사용은 `full` run 만이다. 독립 1차 검토자를 구할 수 없으면 `BLOCKED`
  이고, 한 에이전트를 계획이 다른 호출에 돌려 쓰지 않는다.

### Breaking

- Record schema 와 handshake 가 `4` 다. 정규 줄은
  `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}` 다.
- record 에 `baseline` 과 `ledger` 가, `git` 에
  `head_start_is_ancestor_of_head_end` 가, finding 에 `source` 가 들어간다.
- `finding.repair_pass` 범위가 0..2 이고, `finding.status` 에 `partially-closed`
  가 들어가며, `degraded_reasons` 는 열거다.
- schema 2·3 은 계속 읽는다. 변경은 schema 4 만 받고, schema 3 pending 은
  `abandon` 만 허용한다.

### Notes

- GitHub 태그와 Release 는 만들지 않는다.

## 3.0.4 - 2026-09-17

### Fixed

- `finish` returns this run's observation anomalies; controllers print that list as an `Anomalies:` line instead of searching a windowed `summary`.
- A handoff from an `execution=blocked` run is never reused; `full` and `degraded` handoffs are reused only when documents, `HEAD`, and the request are unchanged.
- Controllers re-ask an incomplete reviewer once for the missing fields only.
- Finding severity follows the minimal document fix: `BLOCKER` needs outside authority or evidence, `IMPORTANT` is repairable within the two documents.

### Changed

- The `missing-coverage` fixture expects `IMPORTANT`; the `ready` fixture design states the function returns its input unchanged.

### Notes

- Record schema and the `--version` handshake are unchanged. No GitHub tag or GitHub Release is created.

## 3.0.3 - 2026-09-16

### Fixed

- Controllers print this run's observation anomalies on `READY`. Anomalies do not change the verdict.
- Incomplete finding records are re-asked without naming suspected findings, paths, symbols, or fixes.
- Red flags name the observed reuse, extra-reviewer, seeded-retry, and document-only `repo-reality` failures.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.2 - 2026-09-12

### Fixed

- Controllers consult `summary` before `start`, close same-plan pending runs, and reuse an unchanged `REVISE`/`BLOCKED` handoff.
- Split plan reviews on one host run one after another. A reused controller thread is not an independent primary.
- A first review with zero findings skips repair and closure.
- `repair_passes` counts only passes with a repaired finding.
- Mutation lock files are removed when the command releases them.

### Changed

- Product READMEs state the summary-before-start, serialize, and zero-finding skip rules.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.1 - 2026-09-11

### Fixed

- Recorder JSON lines keep a single LF on Windows text stdout, so release
  smoke and `--version` match the Unix byte contract.

### Changed

- Product README language was simplified with no behaviour change.
- Standalone README now uses the shared heading set and points install procedures at the split user guides.

### Notes

- No GitHub tag or GitHub Release is created.

## 3.0.0 - 2026-09-08

### Changed

- New optional recorder schema 3 binds records to a locally salted checkout identity.
- Schema 2 remains readable as historical-unbound evidence and cannot be mutated.
- Run locks serialize finish, abandon, and outcome; reads isolate corrupt records.
- Structurally valid contradictory observations remain recorded and appear as anomalies.
- Installed README links resolve inside the payload or point to public repository docs.
- Reviewer roles, scalar risk triggers, two-document repairs, repair limits, and semantic verdicts are unchanged.
- This change does not publish a release or claim new native platform/model evidence.

## 2.0.0 - 2026-09-05

### Changed

- The evidence recorder is one standard-library script,
  `evidence/evidence.py`, run with `python3` from the loaded skill root. The
  `pre-sdd-review-evidence` launcher, installer, and package are removed.
- Records use schema 2: one file per run under `~/.pre-sdd-review/runs/`,
  and six commands `start`, `finish`, `abandon`, `outcome`, `show`, `summary`.
  Schema 1 receipts are not read.
- The controller passes the design path it resolved from `**Spec:**`; the
  recorder no longer parses that field. An unresolved design is recorded as
  null with a `BLOCKED` verdict.
- `finish` rejects a repair pass without a repaired finding. `summary` is
  agent-readable JSON with verdict counts, abandon reasons, per-plan chains,
  repeated finding patterns, outcome coverage, and anomalies, each carrying
  run IDs.
- `outcome` records one label (`good`, `false-ready`, `noisy`, `abandoned`)
  and an optional note, and may be re-recorded.
- Reviewer protocol: a `repo-reality` finding must cite a repository path
  other than the reviewed design or plan.

## 1.3.1 - 2026-09-02

### Changed

- Plans that explicitly name a required implementation base now block before
  reviewer dispatch when that base is unresolved or not an ancestor of the
  current `HEAD`.
- Provider-free coverage now includes the stale implementation-base boundary.

## 1.3.0 - 2026-08-30

### Changed

- Scoped re-review stops at unmapped material findings instead of widening the
  repair or starting another invocation.
- Each invocation uses at most a primary role and one triggered risk role;
  fresh closure agents do not add roles.
- Authority-preserving repairs need no approval. Unresolved product decisions
  are grouped into one checkpoint.
- Reporting now validates each receipt from the same bounded byte snapshot used
  for its size and SHA-256, avoiding repeated reads of one review/outcome pair.
- Source installation ignores only an ordinary `__pycache__` containing regular
  `.pyc` files; unsafe cache entries and runtime-manifest drift still fail.
- User and evidence guides now lead with installation and the basic workflow,
  then separate safety boundaries, operations, measured support, and residual
  limits.

## 1.2.0 - 2026-08-30

### Added

- The optional local `pre-sdd-review-evidence` CLI records provider-neutral,
  content-bounded review and outcome receipts. Recording is non-blocking and
  never changes a review verdict.
- The skill now starts compatible evidence before semantic review, finalizes
  it after the verdict, and hands a controller-local run ID only to an
  explicitly combined SDD flow.
- Product and maintainer guidance now documents explicit launcher install,
  local receipt privacy, immutable outcome limits, heuristic candidates, and
  the native-platform `not_measured` boundary.

## 1.1.0 - 2026-08-29

### Changed

- One invocation reviews exactly one implementation plan. Separate plan-local
  reviews never produce an aggregate `READY`.
- Structural document repairs now record a repair-impact map and receive a
  bounded regression re-review. The two-pass repair limit is unchanged.
- Final `REVISE` and `BLOCKED` reports include an unresolved handoff packet
  and a compact pass receipt. User documents and full model responses are not
  stored.

### Verification

- Added synthetic fixtures for schema-consumer drift, vacuous state
  verification, and conditional edit-surface drift.

## 1.0.0 - 2026-08-29

### Notes

- This is the first independent product release contract for Pre-SDD Review: a
  Codex-only readiness gate with provider-free contract evidence and
  documented maintainer protocols.
- This entry records the release contract only. It does not claim that a tag,
  published package, or GitHub Release exists.
