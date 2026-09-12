# image-workbench Grok 호스트 지원 설계

**Status:** Approved in conversation on 2026-09-12; this file is the written spec.

**Scope:** 기존 제품 `image-workbench`에 지원 호스트 `grok`을 추가한다. Codex 경로는 유지한다. generate/edit는 각 호스트의 내장 이미지 도구만 쓴다. 라이브 smoke가 통과한 뒤에만 `products.toml`에 `grok`을 넣는다.

**Out of scope:** `catalog/` 본문·lock·버전, `korean-writing-editor`와 `pre-sdd-review` 호스트 확장, Claude Code·Cursor 지원, 비디오 도구(`image_to_video`, `reference_to_video`), 외부 이미지 API/CLI, `~/.grok` 또는 `~/.codex` 복사본, 생성 매체·receipt·개인 이미지 커밋, 태그·GitHub Release.

이 파일은 진행 중인 설계이다. 현재 계약을 정의하지 않는다. 산 계약은 구현 후 제품 README와 `docs/maintainers/products/image-workbench/`에 있다.

## Context

`image-workbench`는 프로젝트에 묶인 래스터 자산을 기획·생성·편집·점검한다. 지금 레지스트리 `supported_hosts`는 `["codex"]`뿐이다. `SKILL.md`는 generate/edit를 Codex 내장 이미지 생성으로만 묶고, 공개 지원 문장과 테스트가 그 문구를 고정한다. `CONTRIBUTING.md`는 `image-workbench` 호스트 확장을 금지한다.

Grok Build는 `image_gen`(생성)과 `image_edit`(편집)를 내장한다. 스킬 발견 경로는 `~/.grok/skills/`와 함께 `~/.agents/skills/`이다. Codex `$skill-installer` 기본 위치는 `~/.codex/skills/`이며 Grok은 그 경로를 스캔하지 않는다.

호환성 계약: 새 호스트를 레지스트리와 공개 안내에 넣으려면 같은 빌드에서 발견, 명시 호출, 암묵/near-miss, 출력 계약 smoke가 필요하다. 다른 호스트의 비슷한 도구만으로는 호환이 되지 않는다. how-it-works의 과거 Grok `--max-turns 1` 실패를 이 제품의 smoke 설계로 복사하지 않는다.

승인된 제품 결정:

- 범위는 전체 지원이다. brief/audit뿐 아니라 generate/edit도 Grok에서 돈다.
- Grok 설치는 `~/.agents/skills/image-workbench` 심볼릭 링크 하나다. `~/.grok/skills` 복사본은 만들지 않는다.
- 이 작업에서 라이브 smoke를 돌리고, 통과한 뒤에만 `grok`을 `supported_hosts`에 넣는다.
- 구현 뼈대는 한 스킬 + 호스트 내장 도구 표다. 호스트별 페이로드를 나누지 않는다.

## Goals

1. Codex 사용자는 지금과 같이 `$skill-installer`와 Codex 내장 이미지 도구로 생성·편집한다.
2. Grok 사용자는 `/image-workbench`로 같은 모드·ImageSpec·검사기·비파괴 저장 계약을 따르고, 생성은 `image_gen`, 편집은 `image_edit`를 쓴다.
3. 세션 미리보기 경로는 프로젝트 최종 파일이 아니다. 프로젝트 목적지에 복사한 뒤 `inspect_asset.py`로 확인한다.
4. 내장 도구가 없으면 hold이다. 외부 CLI나 다른 공급자로 조용히 바꾸지 않는다.
5. `grok` 지원 주장은 라이브 4항 smoke와 공급자 없는 `verify.py`가 함께 있을 때만 한다.
6. 카탈로그 고정 묶음은 그대로 둔다.

## Non-goals

- Imagine 스킬 본문을 `SKILL.md`에 복사하지 않는다.
- 비디오 생성·편집을 이 제품에 넣지 않는다.
- Claude Code, Cursor, Claude.ai, Cowork, Skills API, marketplace를 지원하지 않는다.
- 픽셀 크기가 aspect ratio와 다르다는 이유만으로 hold하지 않는다. 픽셀이 ImageSpec 수락 조건일 때만 막는다.
- 오프라인 픽스처 통과를 라이브 시각 품질로 확대하지 않는다.
- `catalog/`를 이 버전으로 재묶지 않는다.

## Decisions

### 1. 제품 정체와 버전

| 필드 | 값 |
| --- | --- |
| `name` | `image-workbench` |
| `display_name` | `Image Workbench` |
| 현재 버전 | `2.0.3` |
| 목표 버전 | `2.1.0` (MINOR) |
| `tag_prefix` | `image-workbench-v` |
| 라이선스 | Apache-2.0 |
| `supported_hosts` (smoke 후) | `codex`, `grok` |
| `verify_stages` | 유지: `product-contract`, `image-contract`, `image-inspector`, `python-compile` |

MINOR인 이유: Codex 기본 모드·출력·필수 공급자는 그대로이고, Grok은 추가 호스트다. 기존 Codex 사용자에게 새 필수 공급자를 요구하지 않는다. `SKILL.md` 실행 규칙이 바뀌므로 PATCH가 아니라 MINOR다. MAJOR가 아닌 이유: 기본 모드를 생성으로 바꾸지 않고, brief가 이미지 호출을 승인하게 하지 않는다.

이 스펙 승인과 구현 계획만으로 태그나 GitHub Release를 만들지 않는다.

`agents/openai.yaml`은 선택적 Codex 표시 메타데이터로 남긴다. 다중 호스트가 되어도 프론트매터는 이식 가능한 키만 둔다: `name`, `description`, `license`, `compatibility`, `metadata`. `allowed-tools`를 넣지 않는다.

### 2. 스킬 계약 (공통)

모드·권한·라우팅·ImageSpec·루브릭·검사기는 유지한다.

- 활성화: 프로젝트에 묶인 래스터. 명시 호출 `$image-workbench` 또는 `/image-workbench`. 예전 `kws-` 접두는 near-miss no-op.
- 모드 하나: `brief`, `generate`, `edit`, `audit`. `brief`/`audit`/비교/진단은 읽기 전용.
- 분명한 `generate` 또는 `edit`만 이미지 호출을 승인한다.
- SVG, 벡터, 아이콘, 네이티브 UI, 데이터 시각, 정확한 레이아웃은 네이티브 경로. 정확한 텍스트·라벨·로고·차트는 결정적 또는 혼합 경로. 다이어그램은 SVG/Mermaid/HTML/canvas.
- ImageSpec 필드와 입력 역할 `edit_target`, `subject_reference`, `style_reference`, `compositing_input`은 그대로.
- 기본 후보 1장. 요청된 자산당 도구 호출 1번. 요청하지 않은 배치 금지. 수정은 한 번에 한 조건.
- 최종 파일은 스킬 루트에서 `python3 scripts/inspect_asset.py <path>`. PNG·JPEG·WebP 구조 검사. 시각 검사와 권리는 별도.
- 비파괴 저장: 새 파일 또는 버전 형제. 교체는 명시 승인일 때만.

오프라인 픽스처의 `builtin_imagegen`은 “현재 호스트의 내장 이미지 도구 호출”이다. Codex 번들 생성/편집과 Grok `image_gen`/`image_edit`가 이 값이다. `third_party_cli`는 계속 실패다.

### 3. 호스트 내장 도구 표

`SKILL.md` Execute 절의 “use Codex built-in image generation only”를 아래로 바꾼다. 잠글 부분문자열 `built-in image generation only`와 `never a silent provider/CLI switch`는 유지한다.

호스트 표:

| 호스트 | generate | edit | 보기 |
| --- | --- | --- | --- |
| Codex | 기존 내장 이미지 생성 | 기존 내장 편집 | 로컬 이미지 보기 |
| Grok | `image_gen` | `image_edit` | 후보 파일을 열어 확인 |

지원하지 않는 호스트(Claude Code, Cursor 포함)에서는 generate/edit를 주장하지 않고, 내장 도구가 없으면 `fail-builtin-unavailable`과 같이 hold한다. 침묵 전환 없음.

Grok 번들 Imagine은 워크벤치가 호출을 강제하거나 금하지 않는다. 워크벤치가 모드·ImageSpec·저장·검사를 소유하고, Imagine은 프롬프트와 도구 인자만 도울 수 있다. `image_to_video`와 `reference_to_video`는 이 제품이 호출하지 않는다.

프론트매터:

- `compatibility` 정확 문장:

```text
Requires Codex or Grok built-in image generation and local image viewing for generate or edit mode. Brief and audit modes can run read-only.
```

- `description`에서 `use Codex image generation only`를 `use the current host's built-in image generation only`로 바꾼다. 나머지 활성화/제외 문구는 유지한다.
- `metadata.version`은 `2.1.0`, `updated_at`은 구현일의 `YYYY-MM-DD`.

`SKILL.md` 본문에 아래 문장을 넣는다. 오프라인 evaluator가 부분문자열로 잠근다.

```text
Do not report a host session preview path as the project-bound final file.
```

Grok generate/edit 규칙도 같은 Execute 절에 적고 부분문자열로 잠근다.

```text
Map ImageSpec canvas to aspect_ratio when it is a ratio.
Do not pass n or count.
A pixel size that disagrees with aspect ratio is not itself a hold unless ImageSpec acceptance makes those pixels a critical condition.
```

### 4. Grok generate / edit 흐름

공통 앞단: 모드 → 프로젝트 맥락(소비 표면만) → ImageSpec → 승인된 도구 호출.

**generate.** `image_gen`에 ImageSpec을 반영한 프롬프트를 넣는다. `canvas`가 비율이면 `aspect_ratio`에 넣는다. 픽셀만 있으면 가장 가까운 지원 비율을 고르고, 실제 픽셀은 검사 단계에서 보고한다. 도구 `n`/`count`는 쓰지 않는다. 요청된 자산마다 호출 한 번.

**edit.** 편집 대상을 먼저 열어 역할과 불변 조건을 확인한다. `image_edit`의 `image` 배열 순서는 고정이다.

1. `edit_target` 하나 (필수)
2. 있으면 `subject_reference`
3. 있으면 `style_reference`
4. 있으면 `compositing_input`

`edit_target`이 없거나 둘이면 hold. 단일 이미지 편집은 Grok이 원본 비율을 유지한다. ImageSpec `canvas`가 원본과 다르면 그 차이를 보고하고, 비율 변경이 명시되지 않으면 도구 기본을 따른다. 픽셀 불일치는 그 자체로 hold가 아니다. ImageSpec `acceptance`가 픽셀을 수락 조건으로 둔 경우만 hold.

**세션 → 프로젝트.** Grok 결과는 세션 `images/N.jpg` 같은 경로로 떨어질 수 있다. 그 경로를 최종 산출로 보고하지 않는다. 프로젝트 목적지에 새 파일 또는 버전 형제로 복사한다. 그 프로젝트 경로에 `inspect_asset.py`를 돌린다. 형식이 PNG·JPEG·WebP가 아니면 hold. 복사 실패도 hold.

**시각 검사.** 기계 JSON은 품질을 대체하지 않는다. 후보를 열어 루브릭을 적용한다. 최종 보고는 프로젝트 경로, 프롬프트, 조작/라우트, 핵심 증거 상태, 소비 코드 변경 여부다.

**한 장.** 세션에 여러 장이 생겨도 요청하지 않은 배치는 납품하지 않는다.

### 5. Hold와 실패

기존 hold 유지: 편집 대상 모호, 권리·프라이버시 불명, 정확한 산출인데 결정적 경로 없음, 최종 경로·크기를 확인할 수 없음. 질문은 하나, 대체 경로는 명시적으로만.

Grok 추가:

- `image_gen`/`image_edit` 없음 → hold, 외부 CLI 없음
- 안전/모더레이션 차단 → 프롬프트를 바꿔 재시도하지 않고 차단을 보고
- 세션 결과를 프로젝트로 복사하지 못함 → 납품하지 않음
- 검사기가 형식 거부 → hold
- 실명 인물인데 참조 없음 → 권리 hold. 순수 `image_gen`으로 얼굴을 만들지 않음

문서에 남는 한계: Grok은 픽셀이 아니라 비율이다. 단일 편집은 원본 비율을 유지한다. 검사기는 전체 비트스트림을 디코딩하지 않는다. 라이브 시각 품질은 오프라인으로 증명하지 않는다. Codex가 `~/.agents/skills`도 보면 설치기와 링크를 둘 다 쓴 사람에게 사본이 둘일 수 있다. 문서에 호스트별 경로만 적고 자동 병합하지 않는다.

### 6. 설치

**Codex.** 유지. `$skill-installer` → `$CODEX_HOME/skills/image-workbench` (없으면 `~/.codex/skills/image-workbench`). `install-codex.md`의 세 제품 목록에서 빼지 않는다. `CODEX_PRODUCTS`에 `image-workbench`가 남는다.

**Grok.** how-it-works/sddx와 같은 일회성 Python 링커. 마커는 `<!-- image-workbench-local-links -->`. 펜스 바이트는 how-it-works 블록을 복사한다. 재타자하지 않는다. 호출은 하나다.

```text
python3 - "$PWD/skills/image-workbench" "$HOME/.agents/skills/image-workbench" <<'PY'
```

제거:

```bash
ls -ld ~/.agents/skills/image-workbench
unlink ~/.agents/skills/image-workbench
```

`~/.grok`와 `~/.codex`와 `~/.claude` 복사본을 만들지 않는다. `ln -s` 안내를 쓰지 않는다. 같은 링크는 `already linked`, 다른 링크·파일·디렉터리·레이스는 거부.

이 마커와 펜스는 다음 네 문서에 정확히 하나씩 있다.

- `skills/image-workbench/README.md`
- `skills/image-workbench/README.en.md`
- `docs/users/ko/install-local.md`
- `docs/users/en/install-local.md`

`install-local.md`에는 `$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench`를 넣지 않는다. 그 줄은 제품 README와 `install-codex.md`가 소유한다. `tests/repository/test_installation_contract.py`의 `DOCUMENTS`/`MARKER`는 how-it-works 전용으로 남긴다. image-workbench 마커는 제품 계약 테스트가 잠근다.

`docs/users/*/installation.md` 표의 `image-workbench` 행은 Codex 설치기와 Grok 로컬 링크를 모두 가리킨다. 본문에 설치 명령 블록을 두지 않는다.

제품 README 첫 호출은 Codex `$image-workbench`와 Grok `/image-workbench`를 둘 다 보여 준다.

### 7. 공개 지원 문장과 거버넌스

공개 지원 문장 (한영 호환성, 제품 README `## 지원 호스트` / `## Supported hosts`, `tests/repository/test_public_docs.py` `IMAGE_SUPPORT`):

```text
image-workbench: Codex and Grok supported; generate/edit requires the current host's built-in image generation and local image viewing.
```

이 문장과 `products.toml`의 `grok`은 라이브 4항 smoke가 통과한 같은 변경에서만 넣는다. smoke 전에는 공개 문장을 Codex-only로 두고, `SKILL.md` 도구 표와 Grok 설치 안내는 넣을 수 있다.

`CONTRIBUTING.md` 현재 문장:

```text
Do not broaden host support for `korean-writing-editor`, `image-workbench`, or `pre-sdd-review`.
```

교체:

```text
Do not broaden host support for `korean-writing-editor` or `pre-sdd-review`. `image-workbench` claims Codex and Grok only after a recorded smoke on the current build.
```

`how-it-works`와 `sddx`의 Codex·Claude Code 범위 문장은 유지한다.

루트 README 제품 표의 image-workbench 호스트 칸은 `Codex, Grok`이다. 도입부의 “나머지 세 제품은 Codex에서만” 문장은 image-workbench를 빼고 한국어 편집기와 Pre-SDD만 Codex-only라고 고친다.

`catalog/` CHANGELOG의 옛 `Codex-only` 문구는 당시 릴리스 기록이므로 고치지 않는다.

`references/sources.md`에 존재하지 않는 Imagine URL을 만들지 않는다. Grok 도구는 호스트 능력으로 `compatibility.md`에 적는다. 공급자 순위나 런타임 클라이언트를 추가하지 않는다.

### 8. 테스트

**오프라인.** CI와 `python3 scripts/verify.py`는 자격 증명·공급자 호출이 없다.

잠글 것:

- `CANONICAL_COMPATIBILITY`를 결정 3의 새 문장으로 교체
- `built-in image generation only`, `never a silent provider/CLI switch`, `Do not report a host session preview path as the project-bound final file.`
- `SKILL.md` 본문에 `image_gen`과 `image_edit`
- `builtin_imagegen`은 호스트 내장. `third_party_cli` 실패
- 새 픽스처 `fail-session-preview-as-final` (category `handoff`): 프로젝트 산출 generate에서 호스트 세션 미리보기만 최종 경로이면 올바른 결정은 `hold`이다. 사용자가 미리보기만 요청한 `save-preview-only`는 그대로 `preview`가 맞다.
- 픽스처 개수는 지금 31 (`handoff` 5)이다. 이 케이스를 넣으면 `EXPECTED_CATEGORY_COUNTS.handoff`는 6, 총 32. `run.py`의 `expected 31 cases` 문자열과 성공 출력 `31 cases:`와 `docs/users/*/verification.md`의 `31` 픽스처 숫자를 32로 맞춘다. `test_public_docs.py` `test_shared_guides_name_current_evidence_dimensions`의 `"31"`도 `"32"`로 바꾼다. mutation 개수 17은 새 mutation을 넣지 않으면 유지한다.
- `IMAGE_SUPPORT` 새 문장 (smoke 후 커밋)
- `install-local.md` owned tuple에 `image-workbench` 추가
- 제품 README에 레지스트리 호스트 `codex`와 `grok` 소문자 포함 (`test_product_readmes_match_registry_hosts`)
- `test_release_contract.py` `EXPECTED["image-workbench"]` = `2.1.0`
- 로컬 링크 마커·호출·`unlink ~/.agents/skills/image-workbench`·`ln -s` 금지. `~/.grok` 대상 경로 금지

**라이브 smoke.** how-it-works처럼 `--max-turns 1`로 자르지 않는다. 합성·비개인 프롬프트만 쓴다.

구현 첫 단계는 코드량보다 Grok 프로브다. 실패하면 `grok`을 레지스트리에 넣지 않는다.

프로브 (지원 주장 전):

1. 저장소에서 링커로 `~/.agents/skills/image-workbench` 생성
2. `grok inspect`에 이름 `image-workbench`와 그 경로
3. 이 세션에서 `image_gen` / `image_edit` 도구가 존재
4. 한 장의 합성 generate 결과가 세션 경로로 떨어지면 임시 프로젝트 경로로 복사 가능하고 `inspect_asset.py`가 형식을 읽음
5. 생성 파일은 커밋하지 않고 삭제하거나 저장소 밖에 둔다

4항 smoke (지원 주장 전제, 프로브 성공 후 `SKILL.md` 도구 표가 있는 빌드):

1. **발견** — `grok inspect`에 링크 경로
2. **명시 호출** — `/image-workbench` + brief. 이미지 도구 없음. ImageSpec만
3. **암묵 / near-miss** — 프로젝트 래스터 요청은 활성화. `kws-image-workbench`는 no-op
4. **출력 계약** — brief/audit은 파일을 안 만듦. generate 또는 edit 한 번: 프로젝트 비파괴 저장, inspector 통과, 후보를 열어 확인

커밋하는 증거는 `tests/products/image-workbench/live/smoke-record.json`과 `tests/products/image-workbench/live/README.md`다. 필드: 날짜, Grok 신원 문자열, 스킬 버전, 페이로드 hash(SKILL.md SHA-256), 네 항 각각 `pass`/`fail`/`not_run`, inspector가 본 `format`·`width`·`height`(이미지 바이트와 SHA-256은 넣지 않음). 프롬프트 원문, 절대 경로, receipt, 이미지 바이트는 커밋하지 않는다.

네 항이 모두 `pass`가 아니면 `products.toml`에 `grok`을 넣지 않고 공개 지원 문장을 바꾸지 않는다. `SKILL.md` 도구 표는 남아도 된다. 실패 원인(발견, 도구 없음, 복사 실패, 형식 거부, near-miss 오작동)을 보고하고 이 스펙의 지원 주장을 닫는다.

### 9. 파일

설치 페이로드에서 만지는 것:

- `skills/image-workbench/SKILL.md`
- `skills/image-workbench/README.md`
- `skills/image-workbench/README.en.md`
- `skills/image-workbench/CHANGELOG.md`
- `skills/image-workbench/release.toml`

저장소 계약:

- `tests/products/image-workbench/run.py`
- `tests/products/image-workbench/cases.json`
- `tests/products/image-workbench/live/README.md` (생성)
- `tests/products/image-workbench/live/smoke-record.json` (생성, smoke 후)
- `tests/repository/test_public_docs.py`
- `tests/repository/test_release_contract.py`
- `docs/maintainers/products/image-workbench/{contract,testing,compatibility,release}.md`

거버넌스 (catalog 제외):

- `products.toml` (`grok`은 smoke 후)
- `CONTRIBUTING.md`
- 루트 `README.md`, `README.en.md`
- `docs/users/ko|en/{installation,install-local,compatibility}.md`
- 필요하면 `docs/maintainers/repository/architecture.md`의 제품 한 줄. `verify_stages`는 바꾸지 않는다.

만지지 않는 것: `catalog/**`, `skills/image-workbench/scripts/inspect_asset.py`(동작 변경 없음), `skills/image-workbench/references/image-spec.md`와 `quality-rubric.md`(필드/역할/상태 유지), 다른 제품 `SKILL.md`, `tests/repository/test_installation_contract.py`의 how-it-works `DOCUMENTS`.

### 10. 구현 순서

코드와 산 문서는 이 스펙이 승인된 뒤에만 바꾼다.

1. Grok 프로브. 실패하면 호스트 지원을 주장하지 않고 멈춘다.
2. 오프라인 테스트(RED): 새 compatibility 문장, 세션 경로 금지 문구, `fail-session-preview-as-final`, `image_gen`/`image_edit` 존재. 아직 `products.toml`에 `grok`을 넣지 않는다.
3. `SKILL.md` 도구 표와 버전 `2.1.0`으로 테스트를 통과시킨다.
4. Grok 로컬 링크 설치 문서와 마커 테스트. 공개 지원 문장은 아직 Codex-only.
5. 라이브 4항 smoke. 생성 파일은 커밋하지 않는다.
6. smoke가 모두 `pass`일 때만 `products.toml` `supported_hosts = ["codex", "grok"]`, `IMAGE_SUPPORT`, CONTRIBUTING, 루트 README, 호환성 문서를 같은 변경에서 맞춘다.
7. `python3 scripts/verify.py --skill image-workbench`와 `python3 scripts/verify.py`가 공급자 없이 통과해야 끝이다.

## Verification

완료 조건:

1. `python3 scripts/verify.py`와 `--skill image-workbench`가 공급자 없이 통과한다.
2. smoke 기록의 네 항이 `pass`이고, 그때 `products.toml` `supported_hosts`가 `codex`와 `grok`이다. smoke가 실패하면 레지스트리에 `grok`이 없다.
3. `SKILL.md` compatibility가 결정 3 문장과 같고, 본문에 `image_gen`, `image_edit`, `built-in image generation only`, 세션 경로 금지 문장, `aspect_ratio`, `n or count`, pixel/acceptance hold 문장이 있다.
4. `release.toml`과 `metadata.version`이 `2.1.0`이다.
5. Grok 링크 대상은 `~/.agents/skills/image-workbench`뿐이고 `~/.grok` 복사 안내가 없다.
6. `catalog/` diff가 비어 있다.
7. `inspect_asset.py` 동작이 이 작업으로 바뀌지 않았다.
8. `git diff --check`가 통과한다.
9. 태그와 GitHub Release를 만들지 않았다.

## Recovery

- 프로브 또는 smoke가 도구 부재·발견 실패·복사 실패면 `grok`을 레지스트리에 넣지 않는다. Codex 경로를 되돌리지 않기 위해 `SKILL.md` 도구 표의 Codex 행은 유지한다.
- 공개 문서가 Grok을 지원한다고 적었는데 smoke 기록이 없으면 문장을 Codex-only로 되돌리고 테스트를 맞춘다.
- `install-local.md`에 image-workbench `$skill-installer` 줄이 들어가면 `test_install_local_owns_how_it_works_links`가 실패한다. 그 줄은 제품 README와 `install-codex.md`로 되돌린다.
- how-it-works 설치 마커가 두 개가 되면 제품 마커 이름을 `<!-- image-workbench-local-links -->`로 분리한다.
- 생성 이미지가 스테이징되면 커밋하지 말고 삭제한다.
- 카탈로그 파일이 바뀌면 그 diff를 버린다.
