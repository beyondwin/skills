# macOS 전용 지원과 품질 우선 속도 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 다섯 스킬을 macOS 전용으로 선언하고 Windows CI·Win32 전송을 제거한 뒤, 내부 검증 루프를 품질 바닥에 맞춰 고정한다.

**Architecture:** CI 러너는 지원 증거가 아니다. Ubuntu `full`만 남기고 `windows-portable`과 Win32 특수경로를 지운다. SDDx 제품 CLI만 Windows에서 `BLOCKED:` / exit 2로 거절한다. 공개 문장과 digest를 같은 사실로 잠근다.

**Tech Stack:** Python 3.11 stdlib, `unittest`, GitHub Actions `ubuntu-latest`, 기존 `scripts/verify.py` 오케스트레이터.

**Spec:** `docs/history/specs/2026-09-14-macos-only-quality-speed-design.md`

## Global Constraints

- 지원 OS는 macOS뿐이다. Windows와 Linux는 지원하지 않는다. `not_measured` 대기열로 두지 않는다.
- CI는 Ubuntu에서 `full`만 실행할 수 있다. 그 통과는 Linux 지원이 아니고 macOS 지원 증거도 아니다. `macos-latest`를 추가하지 않는다.
- `windows-latest` 행과 `windows-portable` 프로필을 제거한다. 알 수 없는 프로필은 실패하며 `full`로 매지 않는다.
- `products.toml`에 `supported_os`를 넣지 않는다. `catalog/`를 건드리지 않는다.
- 한영 사용자 문서는 유지한다. 스킬 프롬프트·새 eval 하네스·자동 재시도·리뷰어 생략을 이 계획에 넣지 않는다.
- 구현 기준 브랜치는 `main`이다. Windows 지원을 위해 `fix/sddx-windows-cmd-shim-unwrap`을 머지하지 않는다.
- Windows 거절 stderr는 정확히 `BLOCKED: Windows is not a supported OS`이고 exit는 2다. 시도 디렉터리 생성 전이다.
- 거절 위치는 `run_worker.py` `main()`(run과 status), `resolve_backend.py` `main()`만, `prepare_grok_sandbox.py`의 Python 3.11 검사 다음이다. `resolve()`는 거절하지 않는다.
- Linux 런타임은 거절하지 않는다. `verify.py`, `inspect_asset.py`, `evidence.py`에는 OS 거절을 넣지 않는다.
- 필수 검증: 제품 변경은 `python3 scripts/verify.py --skill <name>`, 머지 전은 `python3 scripts/verify.py`. 라이브 `--execute`는 이 계획의 통과 조건이 아니다.
- 고정 공개 문장은 스펙 「고정 공개 문장」절을 그대로 쓴다.

## File map

- Modify: `scripts/lib/change_routing.py` — `OS_ROWS`를 Ubuntu `full` 한 줄로
- Modify: `scripts/lib/verification.py` — Task 1에서 `PROFILES = ("full",)`와 프로필 필터만 제거. `WINDOWS_EXCLUDED_STAGES` 상수는 Task 2에서 `test_public_docs.py` import와 함께 삭제한다.
- Modify: `scripts/verify.py` — choices가 `PROFILES`를 따르므로 별도 분기 없음. 문서 문자열만 필요하면 고친다
- Modify: `tests/repository/test_changed_targets.py`, `tests/repository/test_community_and_ci.py`, `tests/repository/test_verify.py` — Windows 행·프로필 단언 삭제
- Modify: `docs/users/ko/verification.md`, `docs/users/en/verification.md`, `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md` — 고정 문장
- Modify: `tests/repository/test_public_docs.py` — `windows-portable` 헬퍼 제거, `WINDOWS_EXCLUDED_STAGES` import 삭제, digest·핀 문장 교체. `historical-unbound`와 `current-bounded` 핀은 유지한다.
- Modify: `CONTRIBUTING.md`, `AGENTS.md` — 내부 루프와 CI 프로필
- Modify: 각 제품 `docs/maintainers/products/<name>/compatibility.md`, 해당 `testing.md` / README / `skills/sddx/SKILL.md` / `skills/sddx/CHANGELOG.md`
- Modify: `skills/sddx/scripts/resolve_backend.py`, `run_worker.py`, `prepare_grok_sandbox.py` — Win32 삭제, Windows CLI 거절
- Modify: `tests/products/sddx/test_resolve_backend.py`, `tests/products/sddx/test_run_worker.py` — Windows 전송 검사 삭제, CLI 거절 검사 추가
- Do not modify: `catalog/`, `products.toml` 스키마, 스킬 프롬프트 본문, `.github/workflows/verify.yml` 러너 하드코딩(행렬은 Python이 만듦)

---

### Task 1: Ubuntu-only CI matrix and `full`-only profile

**Files:**
- Modify: `scripts/lib/change_routing.py:12-15`
- Modify: `scripts/lib/verification.py:13` (`PROFILES`) and the `if profile == "windows-portable":` filter. Do **not** delete `WINDOWS_EXCLUDED_STAGES` in this task.
- Modify: `tests/repository/test_changed_targets.py` (Windows 행 단언)
- Modify: `tests/repository/test_community_and_ci.py:88-108`
- Modify: `tests/repository/test_verify.py` (프로필 루프와 `windows-portable` 전용 테스트)

**Interfaces:**
- Consumes: 없음
- Produces: `OS_ROWS = (("ubuntu-latest", "full"),)`; `PROFILES = ("full",)`; `stages(..., profile="windows-portable", ...)`는 `ValueError: unknown profile: windows-portable`. `WINDOWS_EXCLUDED_STAGES`는 이 작업에서 심볼로 남는다.

- [ ] **Step 1: Write the failing routing tests**

`tests/repository/test_changed_targets.py`에서 Windows 행을 기대하는 단언을 Ubuntu-only로 바꾼다. 구현 전에는 실패한다.

`test_each_target_runs_ubuntu_full_and_windows_portable`를 다음 단언으로 교체하고 이름을 `test_each_target_runs_ubuntu_full_only`로 바꾼다:

```python
    def test_each_target_runs_ubuntu_full_only(self) -> None:
        matrix = matrix_for_targets(["how-it-works"], self.registry)
        rows = matrix["include"]
        self.assertEqual(
            [(row["os"], row["profile"], row["selector"], row["target"]) for row in rows],
            [
                ("ubuntu-latest", "full", "--skill how-it-works", "how-it-works"),
            ],
        )
```

`test_windows_rows_cover_every_selected_target`를 삭제하고, 같은 클래스에 다음을 둔다:

```python
    def test_matrix_has_no_windows_rows(self) -> None:
        matrix = matrix_for_targets(self.all_targets, self.registry)
        self.assertEqual(
            [row["os"] for row in matrix["include"]],
            ["ubuntu-latest"] * len(self.all_targets),
        )
        self.assertFalse(
            any(row["os"] == "windows-latest" for row in matrix["include"])
        )
        self.assertFalse(
            any(row["profile"] == "windows-portable" for row in matrix["include"])
        )
```

`test_full_repository_matrix_is_two_unselected_os_rows`를 `test_full_repository_matrix_is_one_ubuntu_full_row`로 바꾸고 기대를 `[("ubuntu-latest", "full", "", None)]`만 남긴다.

같은 파일에서 행 수가 OS 두 줄을 가정하는 단언을 한 줄로 고친다. 빠지면 Task 1 커밋 뒤 `test_changed_targets`가 실패한다:

- `test_matrix_rows_follow_targets_order_not_input_order`: `["catalog"] * 2 + ["korean-writing-editor"] * 2` → `["catalog", "korean-writing-editor"]`
- `test_product_only_pr_retains_narrow_selector`: `len(matrix["include"]), 2` → `1`
- `test_all_product_paths_retain_narrow_product_selectors`: `len(self.registry.products) * 2` → `len(self.registry.products)`
- `test_catalog_path_retains_narrow_catalog_selector`: `len(matrix["include"]), 2` → `1`
- `test_invalid_git_refs_use_full_repository_matrix`: `len(matrix["include"]), 2` → `1`
- `test_cli_writes_compact_full_matrix_for_main_and_dispatch`: `len(matrix["include"]), 2` → `1`
- `test_cli_writes_pr_matrix_from_changed_paths`: `len(matrix["include"]), 2` → `1`

그다음 `rg -n "\\* 2|, 2\\)|include\\]\\), 2" tests/repository/test_changed_targets.py`로 OS 행 수 단언이 남았는지 확인한다. `full_repository_matrix()`와 비교만 하고 길이를 2로 고정하지 않는 테스트는 그대로 둔다.

`tests/repository/test_community_and_ci.py`의 `full_rows`와 `pr_os_profiles` 기대를 `[("ubuntu-latest", "full")]` / `{("ubuntu-latest", "full")}`로 바꾼다.

- [ ] **Step 2: Run routing tests to verify they fail**

Run:

```bash
python3 -m unittest tests.repository.test_changed_targets.MatrixSerializationTests.test_each_target_runs_ubuntu_full_only tests.repository.test_changed_targets.MatrixSerializationTests.test_matrix_has_no_windows_rows tests.repository.test_changed_targets.MatrixSerializationTests.test_full_repository_matrix_is_one_ubuntu_full_row tests.repository.test_community_and_ci.CiWorkflowTests.test_ci_pins_required_actions_timeout_python_and_matrix
```

Expected: FAIL. `windows-latest` / `windows-portable`가 실제 `OS_ROWS`에 남아 단언과 어긋난다.

- [ ] **Step 3: Write the failing profile tests**

`tests/repository/test_verify.py`에서:

- `WINDOWS_STAGE_NAMES` 상수를 삭제한다.
- `test_windows_profile_excludes_unmeasured_native_gates`, `test_windows_profile_contains_portable_gates_in_order`, `test_windows_profile_excludes_image_gates_after_skill_selection`, `test_windows_pre_sdd_review_selection_keeps_only_portable_gates`, `test_windows_profile_keeps_korean_live_unit`를 삭제한다.
- `for profile in ("full", "windows-portable")` 루프를 `("full",)`만 쓰게 바꾼다.
- `test_korean_live_unit_discovers_live_tests`의 프로필을 `"full"`로 바꾼다.
- `test_selected_stages_use_sys_executable_and_tuple_argv`에서 `("windows-portable", "image-workbench", False)` 행을 삭제한다.
- 다음 테스트를 추가한다:

```python
    def test_windows_portable_profile_is_unknown(self) -> None:
        with self.assertRaises(ValueError) as raised:
            stages(ROOT, "windows-portable", self.registry)
        self.assertIn("unknown profile", str(raised.exception))
```

`test_live_unit_module_is_importable_without_fcntl`과 `test_unix_only_live_tests_are_skipped_without_unix_specials`는 삭제하지 않는다.

- [ ] **Step 4: Run profile tests to verify they fail**

Run:

```bash
python3 -m unittest tests.repository.test_verify.VerifyStageTests.test_windows_portable_profile_is_unknown
```

Expected: FAIL. `windows-portable`이 아직 알려진 프로필이라 `ValueError`가 나지 않거나, 단계 필터만 적용된다.

- [ ] **Step 5: Implement the matrix and profile cut**

`scripts/lib/change_routing.py`:

```python
OS_ROWS = (
    ("ubuntu-latest", "full"),
)
```

`scripts/lib/verification.py`:

```python
PROFILES = ("full",)
```

`stages()` 안의 `if profile == "windows-portable":` 블록만 삭제한다. `WINDOWS_EXCLUDED_STAGES` 상수와 `profile not in PROFILES` 분기는 이 작업에서 그대로 둔다. 상수를 지우면 `tests/repository/test_public_docs.py`가 같은 커밋에서 import 실패한다.

- [ ] **Step 6: Run the Task 1 tests and make sure they pass**

Run:

```bash
python3 -m unittest tests.repository.test_changed_targets tests.repository.test_community_and_ci tests.repository.test_verify
```

Expected: PASS. `test_cli_rejects_unknown_profile`의 `"linux"` 거절은 그대로 통과해야 한다. `WINDOWS_EXCLUDED_STAGES`가 아직 정의되어 있어 `tests.repository.test_public_docs` import는 깨지지 않아야 한다.

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/change_routing.py scripts/lib/verification.py tests/repository/test_changed_targets.py tests/repository/test_community_and_ci.py tests/repository/test_verify.py
git commit -m "$(cat <<'EOF'
fix: drop Windows CI rows and the windows-portable profile

Unsupported OS paths must not remain a required gate.
EOF
)"
```

---

### Task 2: Pin public OS sentences and verification profile docs

**Files:**
- Modify: `docs/users/ko/compatibility.md`, `docs/users/en/compatibility.md`
- Modify: `docs/users/ko/verification.md`, `docs/users/en/verification.md`
- Modify: `tests/repository/test_public_docs.py`
- Modify: `CONTRIBUTING.md`

**Interfaces:**
- Consumes: Task 1의 `PROFILES = ("full",)` 와 `WINDOWS_EXCLUDED_STAGES` 부재
- Produces: 스펙 고정 문장이 사용자 문서에 그대로 있고, `windows-portable`이 사용자 검증 안내와 CONTRIBUTING에 없으며, `PRE_SDD_SHARED_SECTION_DIGESTS` verification digest가 새 절과 일치

고정 문장 (스펙과 동일, 한 글자도 바꾸지 않는다):

한국어 호환성:

```text
지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI는 Ubuntu에서 `full` 프로필을 돌릴 수 있습니다. 그 통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.
```

영어 호환성:

```text
The supported OS is macOS only. Windows and Linux are unsupported. CI may run the `full` profile on Ubuntu. That pass is not Linux support and is not macOS support evidence.
```

한국어 검증 프로필:

```text
`full`이 유일한 프로필입니다. CI는 Ubuntu에서 `full`을 실행할 수 있으며, 그 통과는 macOS 지원 증거가 아닙니다.
```

영어 검증 프로필:

```text
`full` is the only profile. CI may run `full` on Ubuntu; that pass is not macOS support evidence.
```

pre-sdd 공유 검증 절 교체 문장:

한국어: `Ubuntu CI의 `full` 통과는 native macOS 지원을 증명하지 않습니다.`

영어: `An Ubuntu `full` CI pass does not prove native macOS support.`

- [ ] **Step 1: Rewrite the public-doc tests first**

`tests/repository/test_public_docs.py`에서 `WINDOWS_EXCLUDED_STAGES` import, `_WINDOWS_PORTABLE_STAGE_RE`, `_windows_portable_exclusion_sentence`, `_windows_portable_excluded_stages`, `test_windows_portable_user_guides_match_orchestrator_exclusions`를 삭제한다. Task 1이 남긴 `scripts/lib/verification.py`의 `WINDOWS_EXCLUDED_STAGES` 상수도 이 작업에서 삭제한다.

`pre_sdd_shared_contract_errors`의 verification 절 마지막 문장을 스펙 교체 문장으로 바꾼다.

`test_verification_owns_offline_live_evidence_and_profiles`에서 `self.assertIn("--profile windows-portable", text)`를 다음으로 바꾼다:

```python
            self.assertIn("--profile full", text)
            self.assertNotIn("windows-portable", text)
            self.assertIn("`full`", text)
```

`test_shared_guides_name_current_evidence_dimensions`의 compatibility 핀에서 `"native Windows"`만 빼고 `"historical-unbound"`와 `"current-bounded"`는 남긴다. 그 옆에 언어별 OS 고정 문장을 추가한다:

```python
                compatibility = _read(base / "compatibility.md")
                for phrase in ("historical-unbound", "current-bounded"):
                    self.assertIn(phrase, compatibility)
                if language == "ko":
                    self.assertIn(
                        "지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다.",
                        compatibility,
                    )
                    self.assertIn(
                        "그 통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.",
                        compatibility,
                    )
                else:
                    self.assertIn(
                        "The supported OS is macOS only. Windows and Linux are unsupported.",
                        compatibility,
                    )
                    self.assertIn(
                        "That pass is not Linux support and is not macOS support evidence.",
                        compatibility,
                    )
                self.assertNotIn("windows-portable", compatibility)
```

`CONTRIBUTING.md`를 읽는 기존 검사가 `windows-portable`을 요구하면 Ubuntu `full`만 언급하도록 바꾼다. 현재 `test_community_and_ci.py`가 CONTRIBUTING 본문의 프로필 문자열을 직접 핀하지 않으면 CONTRIBUTING은 Step 3에서만 고친다.

- [ ] **Step 2: Run public-doc tests to verify they fail**

Run:

```bash
python3 -m unittest tests.repository.test_public_docs.UserGuideFactTests.test_verification_owns_offline_live_evidence_and_profiles tests.repository.test_public_docs.UserGuideFactTests.test_shared_guides_name_current_evidence_dimensions tests.repository.test_public_docs.UserGuideFactTests.test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits
```

Expected: FAIL. 문서가 아직 `windows-portable`과 native Windows 문장을 가지고 있고 digest가 어긋난다.

- [ ] **Step 3: Edit the user docs and CONTRIBUTING**

`docs/users/ko/compatibility.md`:
- how-it-works smoke 문단(`historical-unbound`, `current-bounded`, 현재 설치 파일 실행 `not_measured`)은 그대로 둔다.
- 그 문단의 마지막 문장 `새 native Windows 측정은 없습니다.`만 한국어 호환성 고정 문장으로 교체한다. 문단 전체를 바꾸지 않는다.
- `Windows에서 의미 있는 검사는 한국어 편집기 오프라인 스위트와 저장소 계약입니다.` 문장은 삭제한다. image-workbench 그림 도구 문장은 남긴다.

`docs/users/en/compatibility.md`도 영어 고정 문장으로 같은 치환을 한다. how-it-works evidence 문장은 남기고 native Windows 한 문장만 교체한다.

`docs/users/ko/verification.md`:
- `windows-portable` 제외 설명과 `python3 scripts/verify.py --profile windows-portable` 예제를 지운다.
- 프로필 자리에 한국어 검증 프로필 고정 문장을 넣는다.
- `python3 scripts/verify.py --profile full` 예제는 남긴다.
- 오프라인 픽스처 절의 `비-Windows의 windows-portable 통과...`를 `Ubuntu CI의 full 통과는 native macOS 지원을 증명하지 않습니다.`로 교체한다.
- 마지막 `native Windows와 Linux는 ... not_measured` 문장도 고정 호환성 사실과 맞게 삭제하거나 같은 미지원 선언으로 바꾼다. 사용자 검증 안내에는 `windows-portable` 문자열이 한 번도 남아선 안 된다.

`docs/users/en/verification.md`도 영어 짝으로 동일하게 맞춘다.

`CONTRIBUTING.md`의 `CI runs only python scripts/verify.py --profile <full|windows-portable>`를 다음으로 바꾼다:

```text
CI runs only `python scripts/verify.py --profile full`. It does not use secrets, live `--execute`/`--preflight`, a provider CLI, or a remote image call. An Ubuntu CI pass is not macOS support evidence.
```

Requirements 절 근처에 내부 루프를 한 블록으로 추가한다:

```text
Local inner loop: after a product edit run `python3 scripts/verify.py --skill <name>`. Before merge run `python3 scripts/verify.py`. Live `--execute` only when that product's runtime or execution contract changed, on macOS, and only with explicit approval.
```

- [ ] **Step 4: Recompute pre-sdd verification digests**

문서를 고친 뒤:

```bash
python3 - <<'PY'
import hashlib, re, pathlib
ROOT = pathlib.Path("docs/users")
heading = {
    "ko": "## 오프라인 픽스처",
    "en": "## Offline fixtures",
}
pattern_for = lambda h: re.compile(rf"^{re.escape(h)}\s*$.*?(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)
for lang in ("ko", "en"):
    text = (ROOT / lang / "verification.md").read_text(encoding="utf-8")
    matches = pattern_for(heading[lang]).findall(text)
    if len(matches) != 1:
        raise SystemExit(f"{lang}: expected 1 owned section, got {len(matches)}")
    digest = hashlib.sha256(matches[0].encode("utf-8")).hexdigest()
    print(lang, digest)
PY
```

출력된 `ko`/`en` hex를 `PRE_SDD_SHARED_SECTION_DIGESTS`의 `("ko", "verification")`과 `("en", "verification")`에 넣는다. safety digest는 바꾸지 않는다.

- [ ] **Step 5: Run public-doc tests to verify they pass**

Run:

```bash
python3 -m unittest tests.repository.test_public_docs
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/users/ko/compatibility.md docs/users/en/compatibility.md docs/users/ko/verification.md docs/users/en/verification.md tests/repository/test_public_docs.py CONTRIBUTING.md scripts/lib/verification.py
git commit -m "$(cat <<'EOF'
docs: declare macOS-only skill support in public guides

Ubuntu CI remains a POSIX gate and must not read as OS support.
EOF
)"
```

---

### Task 3: Product compatibility, SKILL red flag, and maintainer inner loop

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/maintainers/products/sddx/compatibility.md`, `docs/maintainers/products/sddx/testing.md`, `docs/maintainers/products/sddx/contract.md` (Windows 전송 문장이 있으면)
- Modify: `skills/sddx/SKILL.md`, `skills/sddx/README.md`, `skills/sddx/README.en.md`, `skills/sddx/CHANGELOG.md`
- Modify: `docs/maintainers/products/pre-sdd-review/compatibility.md`, `docs/maintainers/products/pre-sdd-review/testing.md`, `docs/maintainers/products/pre-sdd-review/release.md`
- Modify: `docs/maintainers/products/how-it-works/compatibility.md`
- Modify: `docs/maintainers/products/korean-writing-editor/compatibility.md`
- Modify: `docs/maintainers/products/image-workbench/compatibility.md`
- Modify: `docs/maintainers/README.md` (호스트 지원 행이 OS와 섞이면 한 줄만)

**Interfaces:**
- Consumes: Task 2의 공개 고정 문장
- Produces: 각 제품 호환성 문서가 macOS 전용·Windows/Linux 미지원·Ubuntu CI 비증거. SDDx `SKILL.md` 빨간 깃발이 POSIX-only 금지 대신 macOS + Windows CLI 거절

- [ ] **Step 1: Add failing maintainer-doc pins where a test already owns the sentence**

`rg -n "windows-portable|native Windows|POSIX-only" docs skills tests/repository tests/products`로 남은 제품 문장과 그걸 핀하는 테스트를 찾는다. 핀이 있으면 테스트를 새 문장으로 먼저 바꾸고 실패를 확인한다. 핀이 없으면 Step 2에서 문서만 고친다.

SDDx `SKILL.md` 교체 문장 (스펙과 동일):

```text
The supported OS is macOS. Do not add Windows transport. Refuse Windows at the product CLIs.
```

`Do not replace Windows support with POSIX-only code`는 남아선 안 된다.

- [ ] **Step 2: Run any updated pins to verify they fail**

Run (경로가 있으면):

```bash
rg -n "POSIX-only|windows-portable|native Windows" tests
python3 -m unittest tests.products.sddx.test_contract tests.products.pre-sdd-review.test_contract tests.repository.test_public_docs
```

Expected: 문서가 아직 옛 문장이면 FAIL. 핀이 없는 제품은 이 단계가 no-op일 수 있다. no-op이면 Step 3로 간다.

- [ ] **Step 3: Edit product docs**

공통으로 각 `compatibility.md`에 다음 사실을 한국어로 넣는다. 호스트 표는 건드리지 않는다.

- 지원 OS는 macOS뿐
- Windows와 Linux는 지원하지 않음
- Ubuntu `full` CI 통과는 제품 OS 지원 증거가 아님

구체적 치환:

- SDDx `compatibility.md`: `Windows 합성 argv 전송` / `실제 Windows Cursor/Grok CLI` 행 삭제. 알려진 한계의 `.cmd` 절을 “Windows는 미지원이며 제품 CLI가 거절한다”로 교체. `windows-latest`/`windows-portable` 실행 문장 삭제.
- SDDx `testing.md`: Windows `.cmd` 왕복이 CI에서 돈다는 문장 삭제. skipUnless nt 왕복은 삭제 대상이라고 적는다.
- SDDx README / README.en.md: npm `.cmd` 전달 문단을 지원 OS + Windows 거절로 교체.
- SDDx CHANGELOG Unreleased: Windows quoting/unwrap Fixed 항목을 “Windows is unsupported; product CLIs refuse it”로 바꾸고, 전송 수정 설명을 지원 주장으로 남기지 않는다.
- pre-sdd-review `compatibility.md`: CLI matrix Windows 행을 `unsupported`로. Linux 행은 제품 미지원으로 바꾸고 `CI POSIX 검사 ≠ Linux 제품 지원` 한 줄을 적는다. `windows-portable` 문장 삭제.
- pre-sdd-review `testing.md` / `release.md`: native Windows `not_measured`를 미지원으로.
- how-it-works / korean-writing-editor / image-workbench `compatibility.md`: OS 한 절만 추가. 호스트 smoke 규칙은 유지.

`AGENTS.md` 검증 절에 다음을 추가한다:

```markdown
- 제품 파일만 고치면 `python3 scripts/verify.py --skill <name>`을 먼저 돌립니다. 머지 전에는 `python3 scripts/verify.py`입니다.
- CI Ubuntu `full` 통과를 macOS 지원 증거로 쓰지 않습니다. 라이브 `--execute`는 해당 제품 런타임·실행 계약이 바뀐 뒤에만, macOS에서, 명시적으로 합니다.
```

- [ ] **Step 4: Run document-contract tests**

Run:

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py --skill pre-sdd-review
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py --skill korean-writing-editor
python3 scripts/verify.py --skill image-workbench
```

Expected: 각 명령 exit 0. 실패하면 그 제품 테스트가 핀하는 문장을 스펙 고정 문장에 맞춰 테스트와 문서를 같이 고친다. 라이브 모델 호출은 하지 않는다.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md docs/maintainers/products skills/sddx/SKILL.md skills/sddx/README.md skills/sddx/README.en.md skills/sddx/CHANGELOG.md
git commit -m "$(cat <<'EOF'
docs: align product OS claims with macOS-only support

Keep host matrices unchanged and stop describing Windows transport as measured.
EOF
)"
```

`git status`에 빠진 제품 문서가 있으면 같은 커밋에 넣는다. `catalog/`는 넣지 않는다.

---

### Task 4: Remove SDDx Win32 transport and refuse Windows CLIs

**Files:**
- Modify: `skills/sddx/scripts/resolve_backend.py`
- Modify: `skills/sddx/scripts/run_worker.py`
- Modify: `skills/sddx/scripts/prepare_grok_sandbox.py`
- Modify: `tests/products/sddx/test_resolve_backend.py`
- Modify: `tests/products/sddx/test_run_worker.py`
- Test: 같은 파일에 CLI 거절 테스트 추가

**Interfaces:**
- Consumes: Task 3의 SKILL 빨간 깃발과 README 거절 문장
- Produces: `_subprocess_args(executable: str, arguments: list[str], *, env: Mapping[str, str] | None = None) -> list[str]`는 항상 `[executable, *arguments]`를 반환한다. `env`는 명령 벡터에 쓰지 않는다. `_command`는 삭제한다.
- Produces: `refuse_windows() -> int | None` — `os.name == "nt"`이면 stderr에 `BLOCKED: Windows is not a supported OS`를 쓰고 `2`를 반환, 아니면 `None`
- Produces: `run_worker.main`, `resolve_backend.main`, `prepare_grok_sandbox` 모듈 진입이 파서보다 먼저 `refuse_windows()`를 호출

- [ ] **Step 1: Write the failing CLI-refusal tests**

`tests/products/sddx/test_resolve_backend.py` 상단에 `import contextlib`와 `import io`를 추가한다. Windows 전송 테스트(`test_windows_*`, unwrap, comspec, percent names)는 아직 두지 말고, 거절 테스트만 먼저 넣는다.

```python
    def test_main_refuses_windows_before_resolve(self) -> None:
        module = self._load()
        stderr = io.StringIO()
        with mock.patch.object(module.os, "name", "nt"):
            with contextlib.redirect_stderr(stderr):
                code = module.main(["--backend", "grok", "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "BLOCKED: Windows is not a supported OS\n")

    def test_resolve_does_not_refuse_when_os_name_is_nt(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.object(module.os, "name", "nt"):
            with mock.patch.dict(os.environ, self._path(), clear=False):
                resolved = module.resolve("grok")
        self.assertIn(resolved["available"], (True, False))
```

`tests/products/sddx/test_run_worker.py`에:

```python
    def test_main_run_refuses_windows_before_attempt_dir(self) -> None:
        module = self.load()
        attempt = self.base / "missing-attempt"
        stderr = io.StringIO()
        argv = [
            "run",
            "--backend", "grok",
            "--worktree", str(self.worktree),
            "--brief", str(self.brief),
            "--attempt-dir", str(attempt),
            "--effort", "high",
        ]
        with mock.patch.object(module.os, "name", "nt"):
            with contextlib.redirect_stderr(stderr):
                code = module.main(argv)
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "BLOCKED: Windows is not a supported OS\n")
        self.assertFalse(attempt.exists())

    def test_main_status_refuses_windows(self) -> None:
        module = self.load()
        stderr = io.StringIO()
        argv = ["status", "--attempt-dir", str(self.base / "nope")]
        with mock.patch.object(module.os, "name", "nt"):
            with contextlib.redirect_stderr(stderr):
                code = module.main(argv)
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "BLOCKED: Windows is not a supported OS\n")
```

`self.worktree` / `self.brief` 이름이 픽스처와 다르면 `RunnerFixture`가 이미 만드는 경로를 쓴다. `invoke` 없이 `main()`만 호출한다.

`tests/products/sddx/test_prepare_grok_sandbox.py` 상단에 `import contextlib`와 `import io`를 추가한다. `SandboxTests`에 같은 stderr/exit 단언을 추가한다. 이 클래스는 이미 `self.module`로 스크립트를 로드한다. `self.module.os.name`을 `"nt"`로 패치하고 `self.module.main([])`을 호출한다. `prepare_grok_sandbox.py`는 `resolve_backend`을 import하지 않는다. 거절 두 줄은 그 파일에 복제한다.

기존 `test_subprocess_args_keep_direct_commands_as_a_list`와 `TransportTests.test_hostile_arguments_survive_the_launch_transport`는 유지한다.

- [ ] **Step 2: Run refusal tests to verify they fail**

Run:

```bash
python3 -m unittest tests.products.sddx.test_resolve_backend tests.products.sddx.test_run_worker tests.products.sddx.test_prepare_grok_sandbox
```

Expected: 새 거절 테스트 FAIL (`main`이 Windows에서 아직 프로브/파서를 진행). 기존 Windows 전송 테스트는 아직 PASS일 수 있다.

- [ ] **Step 3: Implement refusal, then delete Win32 helpers**

`skills/sddx/scripts/resolve_backend.py`에:

```python
WINDOWS_UNSUPPORTED = "Windows is not a supported OS"


def refuse_windows() -> int | None:
    if os.name == "nt":
        print(f"BLOCKED: {WINDOWS_UNSUPPORTED}", file=sys.stderr)
        return 2
    return None
```

`main()` 첫 줄:

```python
def main(argv: list[str] | None = None) -> int:
    refused = refuse_windows()
    if refused is not None:
        return refused
    parser = argparse.ArgumentParser(prog="resolve_backend.py")
```

`run_worker.py`:

```python
from resolve_backend import ALIASES, _subprocess_args, refuse_windows, resolve
```

```python
def main(argv: list[str] | None = None) -> int:
    refused = refuse_windows()
    if refused is not None:
        return refused
    args = build_parser().parse_args(argv)
```

`prepare_grok_sandbox.py`는 `resolve_backend`을 import하지 않는다. `tomllib` import 성공 직후, `main()` 첫 줄에서 같은 거절을 복제한다:

```python
def main(argv: list[str] | None = None) -> int:
    if os.name == "nt":
        print("BLOCKED: Windows is not a supported OS", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser()
```

문구와 공백은 `refuse_windows()`와 바이트 단위로 같아야 한다.

그다음 Win32 묶음을 삭제한다. 남은 `_command` 심볼은 두지 않는다:

- `_UNTRANSPORTABLE`, `_PERCENT_NAME`, `_expandable_percent_name`
- `_quote_for_cmd`, `_is_cmd_wrapper`, `_unwrap_cmd_wrapper`(있으면)
- `_windows_command_line`, `_uses_cmd_exe`, `_command`

`_subprocess_args`만 남긴다:

```python
def _subprocess_args(
    executable: str, arguments: list[str], *, env: Mapping[str, str] | None = None
) -> list[str]:
    del env
    return [executable, *arguments]
```

`run_worker.py`가 `_command`를 import하지 않는지 확인한다. `except ValueError: return fail("an argument cannot cross the backend command transport")`는 `build_argv`의 `ValueError`를 위해 남긴다. `_subprocess_args`는 더 이상 그 이유로 올리지 않는다. 주석 `The Windows transport validates against this same environment.`를 지운다.

- [ ] **Step 4: Delete Windows transport tests and `.cmd` fixtures that only serve them**

`tests/products/sddx/test_resolve_backend.py`의 `windows argument transport` 절을 통째로 지우되, `test_subprocess_args_keep_direct_commands_as_a_list`만 그 자리에 남긴다. 이름에 `windows`가 없더라도 함께 지울 것:

- `test_windows_cmd_wrapper_is_invoked_through_comspec`
- `test_windows_cmd_wrapper_quotes_hostile_arguments`
- `test_windows_subprocess_args_bypass_list2cmdline`
- `test_windows_exe_command_line_quotes_newlines`
- `test_windows_exe_command_line_quotes_spaces`
- `test_windows_exe_command_line_rejects_nul`
- `test_windows_cmd_wrapper_rejects_untransportable_arguments`
- `test_windows_transport_checks_the_actual_child_environment`
- `test_windows_cmd_wrapper_rejects_expandable_percent_names`
- `test_direct_invocation_never_rejects_percent_names`
- `test_windows_exe_is_invoked_directly`
- `test_windows_cmd_fixture_prints_grok_version`
- `test_windows_cmd_wrapper_round_trips_arguments`

`_windows_env` 헬퍼와 `.cmd`를 쓰는 `_write_cli` 분기가 이 테스트들만 쓰면 함께 삭제한다.

`tests/products/sddx/test_run_worker.py`에서 `write_cmd`와 `@unittest.skipUnless(os.name == "nt", ...)` 테스트를 삭제한다. `@unittest.skipUnless(os.name != "nt", ...)` POSIX 시그널 테스트는 남긴다.

- [ ] **Step 5: Run sddx tests to verify they pass**

Run:

```bash
python3 scripts/verify.py --skill sddx
```

Expected: exit 0. `sddx-contract`가 Windows 전송 테스트 없이 통과하고, 거절 테스트가 포함되어 통과한다.

잘못된 구현이 여기 통과하면 안 된다:

- `resolve()`가 `os.name == "nt"`에서 거절되면 `test_resolve_does_not_refuse_when_os_name_is_nt`가 FAIL해야 한다.
- 거절을 parse_args 뒤에 두면 필수 인자 없는 Windows 호출이 argparse로 먼저 죽는다. `main([])`에 가까운 호출로 거절이 먼저인지 확인하려면 `test_main_status_refuses_windows`가 유효한 status argv를 쓰므로, 추가로 `run_worker.main([])`는 argparse SystemExit가 날 수 있다. 거절이 파서보다 앞이면 `main([])`도 exit 2와 `BLOCKED:`여야 한다. 그 단언을 `test_main_status_refuses_windows` 옆에 추가한다:

```python
    def test_main_refuses_windows_before_argparse(self) -> None:
        module = self.load()
        stderr = io.StringIO()
        with mock.patch.object(module.os, "name", "nt"):
            with contextlib.redirect_stderr(stderr):
                code = module.main([])
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "BLOCKED: Windows is not a supported OS\n")
```

- [ ] **Step 6: Full provider-free verify**

Run:

```bash
python3 scripts/verify.py
rg -n "windows-portable|_quote_for_cmd|_unwrap_cmd_wrapper|_windows_command_line|_expandable_percent_name|_PERCENT_NAME|_UNTRANSPORTABLE|_is_cmd_wrapper|_uses_cmd_exe" scripts skills tests docs/users docs/maintainers
```

Expected: `python3 scripts/verify.py` exit 0. `rg`는 `docs/history/`와 이 계획·스펙, 그리고 “미지원이라 제거했다”는 CHANGELOG 과거 시제 외에는 `windows-portable` 사용법과 Win32 심볼이 없어야 한다. `catalog/` 히트는 허용한다. `docs/history/` 히트는 허용한다.

라이브 공급자 호출은 하지 않는다.

- [ ] **Step 7: Commit**

```bash
git add skills/sddx/scripts/resolve_backend.py skills/sddx/scripts/run_worker.py skills/sddx/scripts/prepare_grok_sandbox.py tests/products/sddx/test_resolve_backend.py tests/products/sddx/test_run_worker.py tests/products/sddx/test_prepare_grok_sandbox.py
git commit -m "$(cat <<'EOF'
fix(sddx): refuse Windows CLIs and delete Win32 argv transport

macOS is the supported OS; cmd.exe quoting is no longer a product path.
EOF
)"
```

`git status`에 sddx 테스트 픽스처 삭제가 있으면 같은 커밋에 넣는다.

---

## Self-review

**Spec coverage**

- macOS 전용 선언, Linux/Windows 미지원 → Task 2·3
- Ubuntu CI, `macos-latest` 추가 금지 → Task 1 (`OS_ROWS` 한 줄)
- `windows-portable` 제거, 별칭 금지 → Task 1 `ValueError`
- Win32 심볼 삭제 → Task 4
- SDDx CLI 거절, `resolve()` 비거절 → Task 4 테스트
- 다른 제품 CLI 비거절 → Task 4 범위에 넣지 않음
- `products.toml` / `catalog/` 금지 → File map
- 고정 공개 문장·digest → Task 2
- 내부 루프 AGENTS/CONTRIBUTING → Task 2·3
- 라이브 비조건 → 모든 검증 단계
- 작업 순서 1→4 → Task 1→4
- 프롬프트 재작성 금지 → File map / Global Constraints

**Placeholders:** 없음. digest 값은 Step 4 스크립트가 계산한다.

- `_subprocess_args` → `list[str]`; `_command` 없음; `refuse_windows` → `int | None`; exit `2`.
