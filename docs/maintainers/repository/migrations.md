# 마이그레이션과 Archive

Archive에서 공개 저장소로 가져온 출처 pin과 캡처 절차를 적습니다. 지금 쓰는
제품 계약을 바꾸지 않습니다.

아래 표는 가져온 출처 pin입니다. 지금 Archive 트리를 설명하지 않습니다.
로컬 checkout 경로를 이 기록의 일부로 취급하지 않습니다.

## Archive 스킬 이관 출처

이 문서는 공개 `beyondwin/skills` 저장소를 만들 때 쓴 `beyondwin/Archive`
출처를 고정합니다. 가져온 출처 pin입니다. 지금 Archive 트리를 설명하지
않습니다. Archive 이력을 다시 쓰지 마세요. 로컬 checkout 경로를 이 기록의
일부로 취급하지 마세요.

## 고정한 출처

| 항목 | 값 |
| --- | --- |
| 출처 저장소 | `https://github.com/beyondwin/Archive.git` |
| 고정 커밋 | `76e6bf4ebbc9430aee9a04a5b780ae38330f3021` |
| 매니페스트 | [`archive-source-manifest.json`](archive-source-manifest.json) |
| 매니페스트 해시 (`manifest_sha256`) | `6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78` |
| 출처 접두사 | `skills/korean-writing-editor/`, `skills/image-workbench/` |
| 추적된 출처 파일 | 22 |
| 캡처 도구 | `scripts/capture_archive_manifest.py` |

캡처 당시 Archive `HEAD`는 고정 커밋의 `origin/main`과 같았습니다. 추적된
작업 트리는 깨끗했습니다. 가져오기 전에 출처 접두사 중 하나라도 바뀌면 다시
캡처해야 합니다.

pin을 확인하려면 로컬 Archive checkout만 `--repository`로 넘기세요. 그
checkout 경로는 커밋하지 마세요.

```bash
python3 scripts/capture_archive_manifest.py verify \
  --repository <archive-checkout> \
  --manifest docs/maintainers/repository/archive-source-manifest.json
```

## 22개 파일 출처 경계

가져오기 권위는 두 접두사 아래의 추적된 파일 22개입니다. 각 파일은 Git
mode, blob OID, 바이트 크기, SHA-256으로 기록되어 있습니다. 이후 작업은
그 바이트를 복사합니다. Archive Git 이력을 가져오지 않습니다.

`korean-writing-editor` (13개 파일):

- `SKILL.md`, `README.md`, `CHANGE_PROTOCOL.md`
- `references/editorial-guide.md`, `references/sources.md`
- `evals/run.py`, `evals/cases.json`, `evals/README.md`
- `evals/live_matrix.py`, `evals/test_live_matrix.py`, `evals/live_cases.json`
- `evals/fixtures/task-7-install-state.json`
- `evals/fixtures/task-7-preflight-commit.json`

`image-workbench` (9개 파일):

- `SKILL.md`, `README.md`, `CHANGE_PROTOCOL.md`
- `references/image-spec.md`, `references/quality-rubric.md`, `references/sources.md`
- `scripts/inspect_asset.py`
- `evals/run.py`, `evals/cases.json`

## 식별자 목록

스캔은 아래 식별자 네 개의 정확한 이름만 봅니다.

- `korean-writing-editor`
- `image-workbench`
- `kws-korean-writing-editor`
- `kws-image-workbench`

체크인한 매니페스트의 모든 적중은 클래스 하나뿐입니다.

| 클래스 | 개수 | 의미 |
| --- | ---: | --- |
| `source` | 22 | 두 스킬 접두사 아래의 추적된 파일 |
| `active-routing` | 2 | `skills/AGENTS.md`, `skills/README.md` |
| `verification-registration` | 4 | `scripts/agent/contract.ts`, `verification-map.ts`, 그리고 그 테스트 |
| `skill-history-document` | 11 | 스킬별 운영·계획·스펙. catalog-identity 이력 포함 |
| `mixed-document` | 4 | 루트 `AGENTS.md`와 `README.md`, 그리고 얼린 plan-runner 카탈로그 단언 두 개 |
| `generated-residue` | 8 | 무시된 캐시 파일, 이름 있는 작업 트리 두 개, 무시된 세션 로그 두 개 |

관련 없는 `kws-*` 트리는 범위 밖입니다. catalog-identity 계획과 스펙은
식별자 네 개를 이름 내기 때문에 포함합니다. 이후 정확한 경로 삭제를 위한
`skill-history-document`로 남깁니다.

## 고정 당시 본 작업 트리

이 Archive 작업 트리 추가는 고정 당시 깨끗했고 이미 `main`에 병합되어
있었습니다. 공개 삭제 게이트 뒤에 `--force` 없이 지웠습니다.

| 작업 트리 (저장소 상대) | 브랜치 | Tip |
| --- | --- | --- |
| `.superpowers/worktrees/kws-korean-writing-editor-cross-model-evaluation` | `codex/kws-korean-writing-editor-cross-model-evaluation` | `90b0776b7cce407cdc1cf3509d5f1dc9e09df107` |
| `.superpowers/worktrees/kws-korean-writing-editor-live-hardening` | `kws-korean-writing-editor-live-hardening` | `64bb7a20898a93b1866698639dd5cde41aeaf334` |
| `.superpowers/worktrees/skills-catalog-identity` | `skills-catalog-identity` | `6788ed37aa43d7014e15c29048e52141b0116cce` |

앞의 작업 트리 경로 두 개는 스캔한 식별자와 맞습니다. 매니페스트에는
`generated-residue`로 나옵니다. `skills-catalog-identity` 경로에는 정확한
식별자가 없습니다. 그래서 식별자 적중이 아니라 여기에 적습니다.

## 무시한 캐시 전용 레거시 디렉터리

`skills/kws-korean-writing-editor/`는 무시한 바이트코드만 있습니다.

- `evals/__pycache__/live_matrix.cpython-314.pyc`
- `evals/__pycache__/test_live_matrix.cpython-314.pyc`

`skills/kws-image-workbench/` 디렉터리는 없었습니다.
`skills/korean-writing-editor/evals/__pycache__/` 아래에도 무시한 `.pyc`
파일이 두 개 더 있습니다. 경로가 아니라 *내용*이 식별자를 가리키는 무시된
세션 로그도 기록합니다.

- `.remember/logs/memory-2026-08-23.log`
- `.remember/logs/memory-2026-08-24.log`

`.git` 내부는 식별자 적중이 아닙니다. 작업 트리 내부는
`.superpowers/worktrees/<name>`으로 접힙니다. 공개 삭제 게이트 뒤에 그
잔여물은 Archive의 현재 트리와 무시된 트리에서 지웠습니다.

## 제거 게이트

공개 저장소 생성, `v2.0.0` 공개, 독립 다운로드 검증이 끝날 때까지 Archive는
손대지 않았습니다. 그 게이트 뒤에 Archive 현재 트리 복사본과 두 스킬의
활성 참조를 되돌릴 수 있는 일반 커밋으로 지웠습니다. Archive에서 되돌리려면
그 제거 커밋을 `git revert`합니다.

## 이관 이후

| 항목 | 값 |
| --- | --- |
| 공개 저장소 | `https://github.com/beyondwin/skills` |
| 공개 `v2.0.0` 커밋 | `d072a37870b5099cb131c91b5270fd7ad032db9f` |
| 공개 릴리스 | `https://github.com/beyondwin/skills/releases/tag/v2.0.0` |
| Archive 제거 커밋 | `e25fd6d023f8baac4f1c48a0df312ba5e9b53bcd` |

이 표는 끝난 이관을 기록합니다. 마켓플레이스 등록을 주장하지 않습니다.
위의 고정 항목은 가져온 출처 pin으로 남습니다.
