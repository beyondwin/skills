# Repository Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공통 변경의 검사 누락, 빈 검증의 성공, 원본과 다른 다운로드의 수용을 막는다.

**Architecture:** 레지스트리·라우터·배포 검사의 기존 경계를 유지한다. 제품 변경을 시작하기 전에 공통 기반을 검증하고 커밋하여 Git 인덱스를 사용하는 배포 테스트의 비교 기준을 고정한다.

**Tech Stack:** Python 표준 라이브러리, unittest, Git, GitHub Actions의 기존 matrix.

**Spec:** `docs/history/specs/2026-09-08-skills-hardening-design.md` §4.1–4.2, R1–R3.

## Global Constraints

- 설치 payload는 `skills/<name>/`, 제품 검증은 `tests/products/<name>/`, 관리자 계약은 `docs/maintainers/products/<name>/`에 둔다.
- 새 스킬, 범용 프레임워크, 필수 외부 공급자, 텔레메트리, 저장소 분할을 추가하지 않는다.
- catalog의 불변 두 제품 번들을 자동으로 갱신하지 않는다. 현재 지원 호스트 범위를 넓히지 않는다.
- 실제 모델·이미지 생성·배포는 포함하지 않는다.
- 이 계획의 writer는 통합 담당 한 명이다. 제품 파일과 제품 버전은 해당 제품 계획에서 변경한다.
- 모든 명령은 저장소 루트에서 실행한다. 구현 시 `b362972`를 포함하는 계획 완료 HEAD에서 격리 worktree를 만들고 시작한다.
- 아래 커밋은 실행 시 통합 담당이 직렬로 수행한다. 다른 에이전트는 Git 인덱스를 변경하지 않는다.

## File Structure

| 파일 | 책임 |
| --- | --- |
| `scripts/lib/product_registry.py` | 허용 키·타입·필수 목록 검증 |
| `scripts/lib/verification.py` | 실행 가능한 stage가 없는 성공 방지 |
| `scripts/lib/change_routing.py` | 변경 경로와 실제 전체 검사 matrix 연결 |
| `scripts/release.py` | 추출 payload와 신뢰 소스 비교, smoke 이전 거부 |
| `tests/repository/test_product_registry.py` | 레지스트리 반례 |
| `tests/repository/test_verify.py` | 빈 실행 반례 |
| `tests/repository/test_changed_targets.py` | selector가 선택하는 실제 stage 검증 |
| `tests/repository/test_release.py` | checksum을 다시 만든 변이 다운로드 검증 |

`products.toml`, `.github/workflows/verify.yml`의 수정은 필요하지 않다. 유효한 현재 등록과 matrix 소비 인터페이스를 유지한다. 공유 문서 갱신은 [통합 계획](2026-09-08-skills-hardening-integration.md)의 소유다.

### Task 1: 레지스트리와 실행 단계의 빈 성공 차단

**Files:** 위 목록의 `product_registry.py`, `verification.py`, `test_product_registry.py`, `test_verify.py`.

**Interfaces:**
- Consumes: 기존 `load_registry(path: pathlib.Path) -> ProductRegistry`, `_string_list(label: str, field: str, value: object) -> tuple[str, ...]`, `_reject_duplicates(values, message)`.
- Produces: 위 공개 함수의 시그니처를 유지한다. `run_stages(stage_list: Iterable[Stage]) -> int`는 빈 iterable에 1을 반환하며 stage를 호출하지 않는다.

- [ ] 기존 `RegistryParsingTests`에 아래 테스트를 추가한다. `_registry`와 `_product`는 같은 파일의 기존 TOML fixture 생성 함수다.

```python
def test_rejects_top_level_and_required_list_gaps(self):
    valid = _registry(_product())
    invalid = [
        valid.replace("schema_version = 1", "schema_version = true", 1),
        "unexpected = 1\n" + valid,
    ]
    for field in ("supported_hosts", "owned_paths", "verify_stages"):
        invalid.append(_registry(_product(**{field: "[]"})))
    for field, value in (
        ("supported_hosts", '["codex", "codex"]'),
        ("verify_stages", '["product-contract", "product-contract"]'),
        ("supported_hosts", '[" "]'),
        ("verify_stages", '[""]'),
    ):
        invalid.append(_registry(_product(**{field: value})))
    for source in invalid:
        with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "products.toml"
            path.write_text(source, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_registry(path)
```

- [ ] `test_verify.py`의 `VerifyStageTests`에 테스트를 추가한다. `mock`이 없으면 `from unittest import mock`을 추가한다.

```python
def test_empty_stage_plan_is_rejected(self):
    with mock.patch("scripts.lib.verification.run_stage") as run:
        self.assertNotEqual(run_stages(iter(())), 0)
    run.assert_not_called()
```

- [ ] RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_product_registry tests.repository.test_verify` 실행. 현재 parser가 boolean/추가 키/빈 목록을 받아들이고 빈 runner가 0을 반환하여 새 테스트가 실패해야 한다. 기존 실패를 새 반례로 오인하지 않는다.

- [ ] `load_registry`의 product 파싱 전 검사를 다음 형태로 강화한다. `raw_products`의 기존 배열 검사와 중복·실제 경로 검사는 유지한다.

```python
if set(data) != {"schema_version", "products"}:
    raise ValueError("products.toml must contain only schema_version and products")
if type(data["schema_version"]) is not int or data["schema_version"] != 1:
    raise ValueError("schema_version must be integer 1")
```

- [ ] `_string_list`를 다음 구현으로 바꾸고 `_load_product`에서 기존 `owned_raw` 검사에 `or not owned_raw`를 추가한다. owned path의 기존 정규화 후 중복 검사도 유지한다.

```python
def _string_list(label: str, field: str, value: object) -> tuple[str, ...]:
    if (not isinstance(value, list) or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)):
        raise ValueError(f"product {label}: {field} must be a non-empty list of strings")
    _reject_duplicates(value, f"product {label}: duplicate {field}")
    return tuple(value)
```

- [ ] `run_stages`의 기존 loop 앞에 아래를 삽입하고 `for stage in selected:`로 순회한다. generator를 두 번 소모하지 않는다.

```python
selected = tuple(stage_list)
if not selected:
    print("FAILED: no verification stages selected", file=sys.stderr, flush=True)
    return 1
```

- [ ] GREEN: RED와 같은 두 모듈을 실행한다. 기존 네 제품 등록, 알려지지 않은 단계 거부, stage 실패 전파가 모두 통과해야 한다.
- [ ] 구현 diff를 검토한 뒤 통합 담당이 커밋한다.

```bash
git add scripts/lib/product_registry.py scripts/lib/verification.py tests/repository/test_product_registry.py tests/repository/test_verify.py
git diff --cached --check
git commit -m "fix: reject incomplete product verification contracts"
```

### Task 2: 공통 PR에 실제 repository-contract 실행

**Files:** `scripts/lib/change_routing.py`, `tests/repository/test_changed_targets.py`.

**Interfaces:**
- Consumes: 기존 `_matches_owned(path: str, owned_paths: Iterable[PurePosixPath]) -> bool`, `targets_for_paths`, `matrix_for_targets`, `full_repository_matrix`.
- Produces: `matrix_for_paths(paths: Iterable[str], registry: ProductRegistry) -> dict[str, list[dict[str, str]]]`. `matrix_for_event`의 시그니처와 JSON row 형식은 유지한다.

- [ ] 테스트에 `from unittest import mock`과 `from scripts.lib.verification import stages`를 추가한다. 기존 `MatrixSerializationTests`에 다음 반례를 넣는다.

```python
def test_common_pr_runs_repository_contract(self):
    cases = ((), ("scripts/lib/product_registry.py",), ("unknown-file",))
    for paths in cases:
        with self.subTest(paths=paths), mock.patch(
            "scripts.lib.change_routing.changed_paths", return_value=paths
        ):
            matrix = matrix_for_event("pull_request", ROOT, self.registry, "base", "head")
        self.assertEqual(matrix, full_repository_matrix())
        for row in matrix["include"]:
            self.assertEqual(row["selector"], "")
            names = [stage.name for stage in stages(ROOT, row["profile"], self.registry)]
            self.assertIn("repository-contract", names)

def test_product_only_pr_retains_narrow_selector(self):
    with mock.patch("scripts.lib.change_routing.changed_paths", return_value=(
        "skills/how-it-works/SKILL.md",
    )):
        matrix = matrix_for_event("pull_request", ROOT, self.registry, "base", "head")
    self.assertEqual(len(matrix["include"]), 2)
    self.assertEqual({row["selector"] for row in matrix["include"]}, {"--skill how-it-works"})
```

- [ ] RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_changed_targets` 실행. 현재 공통 PR은 모든 제품 selector를 반환하므로 첫 테스트가 실패한다.
- [ ] `matrix_for_paths`를 추가한다. 제품 네 개가 모두 선택되었다는 이유만으로 공통 변경으로 간주하지 않는다. 분류 기준은 실제 경로다.

```python
def matrix_for_paths(
    paths: Iterable[str], registry: ProductRegistry,
) -> dict[str, list[dict[str, str]]]:
    normalized = tuple(normalize_repo_path(path) for path in paths)
    if not normalized:
        return full_repository_matrix()
    for path in normalized:
        known = path.startswith(CATALOG_PREFIX) or any(
            _matches_owned(path, product.owned_paths) for product in registry.products
        )
        if not known:
            return full_repository_matrix()
    return matrix_for_targets(targets_for_paths(normalized, registry), registry)
```

- [ ] `matrix_for_event`의 PR 분기를 `return matrix_for_paths(changed_paths(root, base, head), registry)`로, 마지막 fallback을 `return full_repository_matrix()`로 바꾼다. `changed_paths`에서 diff 실패가 빈 tuple을 반환하는 현재 계약은 유지한다.
- [ ] 기존 fallback 테스트의 기대값은 설계 §4.1의 승인된 변경을 명시하여 고친다. `ChangedPathAndCliTests`의 실제 임시 Git fixture로 잘못된 base/head가 selector 없는 두 row를 반환하는지 확인한다. catalog 전용 및 제품 전용 CLI 검사도 유지한다.
- [ ] GREEN: 위 모듈과 `tests.repository.test_verify` 실행. 단순 target 이름 검사뿐 아니라 각 profile의 `repository-contract` 포함을 확인한다.
- [ ] 통합 담당이 커밋한다.

```bash
git add scripts/lib/change_routing.py tests/repository/test_changed_targets.py
git diff --cached --check
git commit -m "fix: run repository checks for shared pull request changes"
```

### Task 3: 네 제품 다운로드를 신뢰 소스에 결속

**Files:** `scripts/release.py`, `tests/repository/test_release.py`.

**Interfaces:**
- Consumes: `payload_sha256(skill_root: Path) -> str`, `load_product_release(skill_root: Path) -> ProductRelease`, `_extracted_version_errors(skill_root: Path, expected: ProductRelease) -> list[str]`.
- Produces: `verify_product_download(root: Path, name: str, directory: Path) -> list[str]`의 기존 형식 유지. 비교 실패는 smoke를 호출하지 않고 반환한다.
- 제품 버전 변경과 Pre-SDD schema 3 smoke 상수 갱신은 후속 통합 계획에 속한다. 이 task는 현재 제품 baseline에서 독립 통과해야 한다.

- [ ] `test_release.py`에 `from unittest import mock`이 없으면 추가한다. 기존 `ProductDownloadTests`에 아래 변이 테스트를 추가한다. 임의 코드를 실행하지 않고 텍스트 주석만 바꾼다.

```python
def test_recomputed_checksum_cannot_replace_trusted_payload(self):
    mutations = (
        ("how-it-works", "references/output.md"),
        ("korean-writing-editor", "references/editorial-guide.md"),
        ("image-workbench", "scripts/inspect_asset.py"),
        ("pre-sdd-review", "evidence/evidence.py"),
    )
    for name, relative in mutations:
        with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            archive, _ = release.build_product(ROOT, name, output, require_release_entry=False)
            member = f"{name}/{relative}"
            suffix = b"\n# download mutation\n" if relative.endswith(".py") else b"\n<!-- download mutation -->\n"
            changed = []
            def rewrite(items):
                for info, data in items:
                    if info.filename == member:
                        data += suffix
                        changed.append(info.filename)
                    yield info, data
            self._rewrite_zip(archive, rewrite)
            self.assertEqual(changed, [member])
            write_checksums((archive,), output / "SHA256SUMS")
            with mock.patch.object(release, "_run_product_smoke", return_value=[]) as smoke:
                errors = release.verify_product_download(ROOT, name, output)
            self.assertIn(f"{name}: extracted payload does not match current source payload", errors)
            smoke.assert_not_called()
```

- [ ] RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.repository.test_release.ProductDownloadTests` 실행. Pre-SDD의 기존 보호는 통과하고 다른 제품의 변이 수용 반례가 실패해야 한다.
- [ ] `verify_product_download`에서 `validate_product` 뒤의 Pre-SDD 한정 hash block을 아래 공통 block으로 교체한다. 기존 version 검사를 hash보다 앞으로 이동한다. checksum·archive safety·추출·제품 검증과 Pre-SDD archive allowlist 검사는 그대로 유지한다.

```python
version_errors = _extracted_version_errors(skill_root, expected)
if version_errors:
    return version_errors
try:
    extracted_payload = payload_sha256(skill_root)
    source_payload = payload_sha256(root / "skills" / name)
except (OSError, ValueError) as exc:
    return [f"{name}: cannot compare extracted payload: {exc}"]
if extracted_payload != source_payload:
    return [f"{name}: extracted payload does not match current source payload"]
return _run_product_smoke(root, name, skill_root)
```

- [ ] GREEN: 같은 `ProductDownloadTests` 실행. 메타데이터 버전 불일치가 source hash 실패보다 먼저 보고되고, 같은 신뢰 원본의 네 제품이 통과해야 한다. checksum 자체를 인증으로 부르는 문구를 추가하지 않는다.
- [ ] 통합 담당이 커밋한다.

```bash
git add scripts/release.py tests/repository/test_release.py
git diff --cached --check
git commit -m "fix: bind downloaded skill payloads to trusted source"
```

- [ ] 제품 writer를 시작하기 전 공통 gate를 한 번 실행한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p 'test_*.py'
```

Expected: exit 0. 실패 시 원인을 해당 공통 diff로 한정하여 고친다. 통과 기록과 커밋을 [실행 인덱스](2026-09-08-skills-hardening-index.md)에 연결할 실행 ledger에 남긴 후 제품 병렬 작업을 시작한다.
