# How It Works Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 사용자 깊이 선택을 우선하는 how-it-works 2.0.0 계약과, 실제로 측정한 범위만 주장하는 출력·smoke 증거 경계를 만든다.

**Architecture:** 설치 payload는 Markdown 지침과 기존 메타데이터를 유지한다. 깊이·출력 정책은 기존 지침/픽스처를 함께 바꾸고, 선택적 smoke의 형식·증거 결속 검사는 제품 테스트 디렉터리의 작은 Python 표준 라이브러리 모듈로 분리한다. 과거 기록은 원문 그대로 남기며 제품 지원 대상과 현재 빌드 측정 상태를 분리한다.

**Tech Stack:** 기존 Agent Skills Markdown/YAML/TOML, Python 표준 라이브러리, unittest, 기존 `scripts.lib.product_contract.payload_sha256`.

**Spec:** `docs/history/specs/2026-09-08-skills-hardening-design.md` — H1–H4, §4.3, §5.3, §6–8.

**Base:** `b362972` (`docs: propose skills reliability hardening design`). 사용자가 이 설계와 계획 작성을 승인했으며, 계획 작성 중 반영된 설계 승인 메타데이터는 동작 계약 변경이 아니다.

## Global Constraints

- 설치 payload는 skills/<name>/, 제품 검증은 tests/products/<name>/, 관리자 계약은 docs/maintainers/products/<name>/에 둔다.
- 새 스킬, 범용 프레임워크, 필수 외부 공급자, 텔레메트리, 저장소 분할을 추가하지 않는다.
- 현재 지원 호스트 범위를 넓히지 않는다.
- 실제 모델·이미지 생성·배포는 포함하지 않는다.
- 제품 목표 버전은 `2.0.0`이다. 제품 version, SKILL metadata, CHANGELOG와 배포 검사를 함께 맞춘다.
- 공개·tag·push를 이 작업의 부수 효과로 수행하지 않는다. catalog lock/version도 유지한다.
- 실제 사용자 설치 경로에서 시험하지 않는다. 공백이 있는 임시 경로와 정상/기존/다른/깨진 링크를 사용한다.
- 수정한 지시문의 특정 문구가 존재한다는 것만으로 행동을 검증했다고 하지 않는다.
- 제품 단위 검사 후 통합된 전체 profile과 windows-portable을 수행한다. portable 통과는 native Windows recorder 증거가 아니다.

현재 단계에서는 이 계획 파일만 작성한다. 아래 체크박스·명령·코드는 후속 구현 작업의 지침이며 지금 제품 수정·테스트 변경·커밋·설치 실행을 승인하거나 수행하는 내용이 아니다.

## 파일 소유권과 연결 지점

제품 작업자가 수정할 파일:

- `skills/how-it-works/SKILL.md`: 깊이 선택, 여섯 산출, 언어별 진입 안내.
- `skills/how-it-works/references/output.md`: 출력 순서, 허점의 본문 표, 비교 정책.
- `skills/how-it-works/references/visuals.md`: 기준 Mermaid와 동일 hop ID.
- `skills/how-it-works/references/korean.md`: 일관된 해요체 예시.
- `skills/how-it-works/references/stakes.md`: 한국어/영어 배너, 조건부 확인·미확인 정책.
- `skills/how-it-works/references/sources.md`: 검증한 출처와 미확인 주장 구분.
- `skills/how-it-works/README.md`, `README.en.md`: 2.0.0 사용 계약, 설치 코드, payload 내부/공개 문서 링크.
- `skills/how-it-works/release.toml`, `CHANGELOG.md`: 버전과 변경 의미.
- `tests/products/how-it-works/cases.json`, `test_contract.py`: 문서·정적 픽스처 계약.
- `tests/products/how-it-works/live/README.md`, `live/cases.json`: 관측 차원과 운영 절차.
- 새 `tests/products/how-it-works/live/evidence_contract.py`: 선택적 증거의 순수 검증 함수. 설치 payload에 넣지 않는다.
- 새 `tests/products/how-it-works/test_evidence_contract.py`: 합성 출력·메타데이터의 결정적 반례.
- `docs/maintainers/products/how-it-works/contract.md`, `testing.md`, `compatibility.md`, `release.md`: 변경된 계약과 실제 검증 한계.

보존할 파일: `tests/products/how-it-works/live/smoke-record.json`의 schema 1 내용·당시 날짜·클라이언트 버전·판정. 당시 payload hash/model을 추측해 채우지 않는다. `agents/openai.yaml`은 현재 표시·호출 메타데이터가 새 계약을 잘못 설명하지 않는 한 수정하지 않는다.

통합 담당만 수정: `scripts/**`, `products.toml`, `tests/repository/**`, `docs/users/**`, CI, 다른 제품 파일. 제품 작업자는 공통 검사에서 발견한 옛 버전/문구 고정과 README 설치 블록 변경 사항을 경로·실패 출력으로 전달한다. 공통 digest/검사를 우회하거나 제거하지 않는다.

연결 인터페이스:

1. hash 계산은 기존 `payload_sha256(skill_root: Path) -> str`을 그대로 소비한다. 별도의 파일 정렬·모드·hash 알고리즘을 만들지 않는다.
2. 두 제품 README에는 `<!-- how-it-works-local-links -->` 바로 다음에 Python fenced block을 둔다. 이 블록은 `sys.argv[1]` source, `sys.argv[2]` target 두 인자를 받고, 공통 테스트가 그대로 추출·실행한다.
3. 지원 대상은 레지스트리의 기존 `codex`, `claude-code`다. 과거 통과·현재 미측정은 이 지원 대상을 자동으로 삭제하거나 확대하는 근거가 아니다.
4. Task 1 → Task 2 → Task 3 → Task 4 → Task 5 순서로 실행한다. 공통 설치/문서 검사 통합은 Task 4와 만난다. 현재 `how-it-works-contract` stage는 `-p test_contract.py`로 고정되어 있으므로 통합 담당이 이를 `-p test_*.py`로 바꾸고 소비 검사를 추가한다. 공유 release/version pin도 통합 담당이 바꾼 뒤에만 `--skill` 및 전체 검증을 실행한다.

---

### Task 1: 명시 깊이와 숫자 문맥의 우선순위를 2.0.0 계약으로 변경

**Files:**

- Modify: `skills/how-it-works/SKILL.md`의 Slots, Dump gate.
- Modify: `tests/products/how-it-works/cases.json`, `test_contract.py`의 jargon/default·case ID 검사.
- Modify: `docs/maintainers/products/how-it-works/contract.md`, `testing.md`의 깊이 계약.

**Interfaces:**

- Consumes: 설계 §5.3의 승인된 우선순위. 기존 trigger 및 debugging/ELI5 제외.
- Produces: `explicit rung > explicit depth alias > existing jargon default > one necessary question` 문서 계약과 아래 합성 입력 사례. 프로덕션 분류기나 모델 실행기를 새로 만들지 않는다.

- [ ] **Step 1: 기존 기대값을 보존한 상태에서 새 계약 회귀 검사를 추가한다.**

`test_contract.py`의 기존 `HowItWorksPayloadTests`에 다음을 추가한다. 이 검사는 문서에 정책이 선언되고 모순 문구가 제거되었는지만 증명한다.

```python
def test_v2_explicit_depth_precedence_contract(self) -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    self.assertIn(
        "explicit rung > explicit depth alias > existing jargon default > one necessary question",
        text,
    )
    self.assertIn("Interpret numeric aliases only when explicitly selecting depth", text)
    self.assertNotIn("jargon wins", text)
    self.assertNotIn("Aliases (쉽게, 한눈에, `5`) do not count as naming 그림", text)
```

- [ ] **Step 2: RED를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_contract.py -v`

Expected: 새 precedence 문구가 없어서 위 검사 실패. 기존 jargon 기대값은 이 시점에 먼저 바꾸지 않는다. 이 RED는 현재 문서와 새 승인 정책의 차이를 재현하며 실제 모델의 잘못된 응답을 재현한 것이 아니다.

- [ ] **Step 3: 지침·픽스처·관리자 설명을 동시에 바꾼다.**

Slots의 해당 부분을 다음 계약으로 바꾼다. 기존 slice/type/language gate와 한 번에 질문 하나 규칙은 유지한다.

```text
Depth precedence: explicit rung > explicit depth alias > existing jargon default > one necessary question.
An explicitly selected 그림/길/뼈대/허점 (picture/path/skeleton/fracture) wins.
Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon such as rebase, TTL, or Raft.
Use the existing jargon default only when neither a rung nor a depth alias was supplied.
Interpret numeric aliases only when explicitly selecting depth; numbers in the topic are not depth choices.
Never replace a filled rung. If the rung remains unresolved, ask one closed depth question.
```

숫자는 `깊이 5`, `depth 20`, 깊이 선택 질문에 대한 `10` 답변처럼 깊이를 고르는 문맥에서만 기존 대응 `5→그림, 10→길, 15→뼈대, 20→허점`을 쓴다. `Raft term 20`의 20, `HTTP/2`의 2, `5개 노드`의 5는 주제 데이터다. 새 jargon 사전·분류기를 도입하지 않는다.

기존 `jargon-rung` 사례를 승인된 정책 변경으로 명시해 `must: ["picture_default"]`, `forbidden: ["skeleton_default"]`로 바꾸고 다음 사례를 `cases.json` 뒤에 추가한다. `CASE_IDS`와 기존 정확한 fixture 검사도 같은 변경에서 맞춘다.

```json
[
  {"id":"explicit-fracture-jargon","prompt":"Raft 허점으로 설명해줘","must":["fracture"],"forbidden":["skeleton_default"]},
  {"id":"explicit-path-jargon","prompt":"rebase 길로 보여줘","must":["path"],"forbidden":["skeleton_default"]},
  {"id":"english-explicit-fracture","prompt":"Explain Raft at the fracture depth.","must":["fracture","english"],"forbidden":["korean_banner","skeleton_default"]},
  {"id":"jargon-without-depth","prompt":"Raft 원리부터 설명해줘","must":["skeleton_default"],"forbidden":["numeric_depth"]},
  {"id":"topic-number-is-not-depth","prompt":"Raft term 20의 원리부터 설명해줘","must":["skeleton_default"],"forbidden":["fracture"]},
  {"id":"explicit-numeric-depth","prompt":"Raft를 깊이 5로 설명해줘","must":["picture_default"],"forbidden":["skeleton_default"]}
]
```

`missing-rung`의 `DNS 흐름` 질문 사례와 debugging/ELI5 사례는 유지한다. fixture의 `must/forbidden`은 평가 규격 데이터이며 이를 읽는 모델을 실행한 결과가 아니다. 기존 `test_jargon_defaults_to_skeleton_not_picture`는 새 이름 `test_explicit_easy_alias_precedes_jargon`로 바꾸되 설계 §5.3에 따른 동작 변경임을 주석과 CHANGELOG에 남긴다.

- [ ] **Step 4: GREEN과 독립 검토를 수행한다.**

Run: Step 2와 동일한 unittest 명령.

Expected: 기존 제외 경계와 새 문서/사례 계약 통과. 리뷰어는 숫자 포함 주제, 명시 `길/허점`, 영어 rung에 미정의 예외가 생겼는지 문서를 직접 검토한다. 모델의 depth 준수율은 `not_measured`다.

### Task 2: 여섯 산출·허점·언어·고위험 출처 정책을 하나로 맞춤

**Files:**

- Modify: `skills/how-it-works/SKILL.md`, `references/output.md`, `visuals.md`, `korean.md`, `stakes.md`, `sources.md`.
- Modify: `tests/products/how-it-works/test_contract.py`, `cases.json`.
- Modify: `docs/maintainers/products/how-it-works/contract.md`, `testing.md`.

**Interfaces:**

- Consumes: Task 1의 채워진 rung/language와 기존 여섯 산출.
- Produces: 모든 rung의 기준 Mermaid + `H1`, `H2` 형식 hop 목록; 허점의 실패/적용 범위 표는 Body에 위치. Task 3은 이 표준 표기에서 문자 차원의 hop 대응만 검사한다.

- [ ] **Step 1: 모순을 직접 드러내는 문서 계약 검사를 추가한다.**

```python
def test_v2_fracture_and_stakes_contract(self) -> None:
    output = _reference("output.md")
    stakes = _reference("stakes.md")
    korean = _reference("korean.md")
    self.assertIn("Keep the baseline Mermaid and numbered hops in Map at every rung", output)
    self.assertIn("Put the failure/regime table in Body at 허점", output)
    self.assertNotIn("The 한 줄 is a **recommendation**, not a tie", output)
    self.assertNotIn("Do not fetch sources unless", stakes)
    self.assertIn("verified or explicitly unverified", stakes)
    self.assertIn("## 한국어", stakes)
    self.assertIn("## English", stakes)
    self.assertNotIn("물어라", stakes)
    self.assertNotIn("컴퓨터는 숫자 주소를 본다", korean)
```

- [ ] **Step 2: RED를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_contract.py -v`

Expected: 현재 허점/출처/배너 문서가 새 계약을 충족하지 못해 실패. 고위험 banner의 옛 바이트 보존 검사는 아직 유지한다.

- [ ] **Step 3: 지침과 예시를 다음 내용으로 바꾼다.**

```text
Keep the baseline Mermaid and numbered hops in Map at every rung.
Put the failure/regime table in Body at 허점.
Keep hop identifiers stable when changing depth; explain added detail against the same hops.
Use only the selected language for headings, intent lines, body, banner, and next move.
For comparisons, state the tradeoff under the user's conditions. Do not require a personalized action recommendation for medical, legal, or financial topics.
```

`visuals.md`의 `허점: table`은 `Map의 기준 Mermaid 유지; Body의 실패/적용 범위 표`로 수정한다. `output.md`의 overlay 표도 같은 내용으로 바꾼다. 기존 six deliverables, ontology/collapse/term monotonicity, 렌더러 없는 fallback은 보존한다. 공통 템플릿의 `한 줄 / One sentence`는 출력할 때 둘 중 현재 언어 하나를 택한다는 설명을 붙인다.

한국어 고정 예시와 배너는 아래 문구로 통일한다. 기존 배너의 정확한 바이트 검사는 언어별 새 계약 검사로 교체하며 변경 근거는 H2다.

```markdown
한국어 intent: {slice}를 **{rung}** 깊이로 설명할게요. {particle}가 이동하는 순서를 따라가요.
한국어 그림 예시: 사이트 이름은 사람이 읽고, 컴퓨터는 숫자 주소를 써요. DNS는 이름에 연결된 주소를 조회하는 체계예요.

## 한국어
일반적인 작동 원리를 설명해요. 개인의 의료·법률·금융 결정을 위한 조언은 아니에요.

## English
This explains the general mechanism. It is not personalized medical, legal, or financial advice.
```

`stakes.md`와 `sources.md`에는 다음 정책을 같은 의미로 넣는다.

```text
Stable general principles need no unnecessary lookup.
Claims depending on date, jurisdiction, or material uncertainty must be verified or explicitly unverified.
When host policy and user constraints allow, check primary sources for those claims.
When lookup is unavailable or the user disallows it, label the dependent claim as unverified and state the date/jurisdiction limitation without inventing details.
Only sources actually fetched in the current turn may be labeled verified. Never invent paper or statute identifiers.
An unverified claim note is allowed even when no citation heading is emitted.
```

`output.md`의 근거 예시도 `검증함`과 `미확인`을 구분한다. 조회하지 않았을 때 근거 제목을 생략하라는 규칙이 미확인 표기를 금지하는 것으로 읽히지 않게 명시한다. 호스트 상위 정책과 사용자의 검색 금지를 우회하지 않는다.

`cases.json`에는 `fracture-keeps-map`, `high-stakes-no-lookup`, `high-stakes-english`, `high-stakes-comparison` 합성 사례를 추가한다. 각 prompt는 각각 `Raft 허점`, `계약 해지의 일반 원리를 길로 설명해줘. 검색하지 마`, `Explain compound interest as a path in English`, `고정금리와 변동금리의 작동 차이를 그림으로 비교해줘`를 사용한다. must는 차례로 `baseline_mermaid/numbered_hops/body_regime_table`, `unverified_dependent_claim/no_invented_statute`, `english_banner`, `conditional_tradeoff`이며 forbidden은 차례로 `table_only_map`, `verified_without_fetch`, `korean_banner`, `forced_personal_recommendation`이다.

- [ ] **Step 4: GREEN과 내용 검토를 수행한다.**

Run: Step 2와 동일한 명령.

Expected: 문서·fixture 계약 통과. 옛 배너와 jargon 문구를 재도입하는 문자열 회귀도 실패해야 한다. 이 단계는 실제 설명의 진실성·해요체 준수·영어 출력 품질을 검증한 것으로 보고하지 않는다.

### Task 3: 과거 smoke 보존과 관측 차원별 새 증거 계약

**Files:**

- Create: `tests/products/how-it-works/live/evidence_contract.py`.
- Create: `tests/products/how-it-works/test_evidence_contract.py`.
- Modify: `tests/products/how-it-works/test_contract.py`, `live/cases.json`, `live/README.md`.
- Modify: `docs/maintainers/products/how-it-works/compatibility.md`, `testing.md`.
- Preserve: `tests/products/how-it-works/live/smoke-record.json`의 기존 바이트.

**Interfaces:**

- Consumes: `payload_sha256(Path) -> str`, `load_product_release(Path).version`, Task 2의 표준 hop 표기.
- Produces: `observe_text(text: str) -> dict[str, dict[str, str]]`, `record_binding(record: dict, *, current_version: str, current_hash: str) -> str`.
- `record_binding` 결과는 `historical-unbound`, `unbound`, `different-payload`, `current-bounded` 중 하나다. `current-bounded`는 입력 메타데이터가 현재 payload에 연결된다는 뜻이며 실제 호출 실행이나 전 차원 통과를 뜻하지 않는다.
- 차원 이름은 `fence`, `hop_ids`, `skill_loading`, `mermaid_syntax`, `meaning`. 각 값은 `{"status": "pass|fail|not_measured", "method": "..."}`다.

- [ ] **Step 1: 합성 반례 검사를 먼저 추가한다.**

새 test 파일은 다음 import와 fixture를 정의한다. 아래 값은 오직 합성 단위 테스트 입력이며 실제 smoke 기록에 쓰지 않는다.

```python
import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.lib.product_contract import payload_sha256

spec = importlib.util.spec_from_file_location("how_evidence", HERE / "live" / "evidence_contract.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def synthetic_record():
    dimensions = {name: {"status": "not_measured", "method": "not_run"}
                  for name in module.DIMENSIONS}
    return {
        "schema_version": 2, "product": "how-it-works", "product_version": "2.0.0",
        "payload_sha256": "a" * 64, "model": "synthetic-model",
        "host": "codex", "client_version": "synthetic-client",
        "runner_version": "how-evidence-1", "executed_on": "2026-09-08",
        "cases": {"explicit-dns-path": {"invocation": "pass", "dimensions": dimensions}},
    }

class EvidenceContractTests(unittest.TestCase):
    def test_broken_mermaid_does_not_prove_syntax_or_loading(self):
        text = '```mermaid\nnot mermaid H1\n```\n1. **H1** — synthetic hop\n'
        result = module.observe_text(text)
        self.assertEqual(result["fence"]["status"], "pass")
        self.assertEqual(result["hop_ids"]["status"], "pass")
        for key in ("mermaid_syntax", "meaning", "skill_loading"):
            self.assertEqual(result[key]["status"], "not_measured")

    def test_mismatched_hops_fail(self):
        text = '```mermaid\nflowchart LR\nA["H1 start"]\n```\n1. **H2** — stop\n'
        self.assertEqual(module.observe_text(text)["hop_ids"]["status"], "fail")

    def test_legacy_record_is_unchanged_and_unbound(self):
        record = json.loads((HERE / "live" / "smoke-record.json").read_text())
        before = copy.deepcopy(record)
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "historical-unbound")
        self.assertEqual(record, before)

    def test_different_payload_cannot_claim_current_build(self):
        record = synthetic_record()
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="b"*64),
                         "different-payload")
        record["model"] = None
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "unbound")

    def test_regex_cannot_be_syntax_evidence(self):
        record = synthetic_record()
        record["cases"]["explicit-dns-path"]["dimensions"]["mermaid_syntax"] = {
            "status": "pass", "method": "regex"}
        with self.assertRaisesRegex(ValueError, "invalid evidence method"):
            module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_current_metadata_binding_is_not_a_quality_verdict(self):
        record = synthetic_record()
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "current-bounded")
        self.assertEqual(record["cases"]["explicit-dns-path"]["dimensions"]["meaning"]["status"],
                         "not_measured")
        self.assertEqual(module.record_binding(record, current_version="2.0.1", current_hash="a"*64),
                         "different-payload")

    def test_source_reference_mutation_breaks_binding(self):
        with tempfile.TemporaryDirectory(prefix="how-evidence-") as directory:
            copied = Path(directory) / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", copied)
            record = synthetic_record()
            record["payload_sha256"] = payload_sha256(copied)
            target = copied / "references" / "output.md"
            target.write_bytes(target.read_bytes() + b"\nSynthetic audit mutation.\n")
            self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash=payload_sha256(copied)),
                             "different-payload")

    def test_invalid_record_shapes_are_rejected(self):
        variants = []
        for key, value in (("schema_version", True), ("extra", "unexpected"),
                           ("executed_on", "not-a-date"), ("cases", {})):
            record = synthetic_record()
            record[key] = value
            variants.append(record)
        missing = synthetic_record()
        del missing["cases"]["explicit-dns-path"]["dimensions"]["meaning"]
        variants.append(missing)
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_duplicate_or_absent_hops_never_prove_quality(self):
        duplicate = '```mermaid\nA["H1 start"]\n```\n1. **H1** — a\n2. **H1** — b\n'
        self.assertEqual(module.observe_text(duplicate)["hop_ids"]["status"], "fail")
        missing = module.observe_text("A plain answer.")
        self.assertEqual(missing["fence"]["status"], "fail")
        for key in ("hop_ids", "skill_loading", "mermaid_syntax", "meaning"):
            self.assertEqual(missing[key]["status"], "not_measured")
```

- [ ] **Step 2: RED를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_evidence_contract.py -v`

Expected: 새 모듈 부재로 import 실패. 파일을 추가한 뒤에는 hop 불일치·과거 결속·regex 승격 반례가 각각 실패하는지 확인한다. 현재 공통 stage의 discovery pattern은 새 파일을 누락하므로, 통합 담당의 pattern 수정 전에는 이 직접 unittest 명령으로 실행한다.

- [ ] **Step 3: 외부 호출 없는 최소 검증 모듈을 구현한다.**

```python
import re
from datetime import date

DIMENSIONS = ("fence", "hop_ids", "skill_loading", "mermaid_syntax", "meaning")
METHODS = {
    "fence": {"lexical"}, "hop_ids": {"lexical"},
    "skill_loading": {"host_event"},
    "mermaid_syntax": {"parser", "renderer"},
    "meaning": {"semantic_review"},
}
FIELDS = {"schema_version", "product", "product_version", "payload_sha256", "model",
          "host", "client_version", "runner_version", "executed_on", "cases"}

def observe_text(text: str) -> dict[str, dict[str, str]]:
    result = {name: {"status": "not_measured", "method": "not_run"} for name in DIMENSIONS}
    blocks = re.findall(r"(?ms)^```mermaid[ \t]*\n(.*?)^```[ \t]*$", text)
    result["fence"] = {"status": "pass" if blocks and all(b.strip() for b in blocks) else "fail",
                       "method": "lexical"}
    if result["fence"]["status"] == "pass":
        source_ids = set(re.findall(r"\bH[1-9][0-9]*\b", "\n".join(blocks)))
        prose = re.sub(r"(?ms)^```.*?^```[ \t]*$", "", text)
        list_ids = re.findall(r"(?m)^\s*[0-9]+\.\s+\*\*(H[1-9][0-9]*)\*\*", prose)
        match = bool(source_ids) and source_ids == set(list_ids) and len(list_ids) == len(set(list_ids))
        result["hop_ids"] = {"status": "pass" if match else "fail", "method": "lexical"}
    return result

def record_binding(record: dict, *, current_version: str, current_hash: str) -> str:
    if type(record.get("schema_version")) is not int:
        raise ValueError("schema_version must be an integer")
    if record["schema_version"] == 1:
        if set(record) != {"schema_version", "executed_on", "hosts"}:
            raise ValueError("invalid historical record fields")
        date.fromisoformat(record["executed_on"])
        if not isinstance(record["hosts"], list):
            raise ValueError("invalid historical hosts")
        return "historical-unbound"
    if record["schema_version"] != 2 or set(record) != FIELDS:
        raise ValueError("invalid current record fields")
    if record["product"] != "how-it-works":
        raise ValueError("invalid product")
    for key in ("product_version", "host", "client_version", "runner_version", "executed_on"):
        if not isinstance(record[key], str) or not record[key].strip():
            raise ValueError(f"invalid {key}")
    date.fromisoformat(record["executed_on"])
    if record["host"] not in {"codex", "claude-code", "grok", "cursor"}:
        raise ValueError("invalid host")
    if not isinstance(record["payload_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", record["payload_sha256"]):
        raise ValueError("invalid payload hash")
    if record["model"] is not None and (not isinstance(record["model"], str) or not record["model"].strip()):
        raise ValueError("invalid model")
    if not isinstance(record["cases"], dict) or not record["cases"]:
        raise ValueError("invalid cases")
    for case_id, case in record["cases"].items():
        if not isinstance(case_id, str) or not case_id or not isinstance(case, dict):
            raise ValueError("invalid case")
        if set(case) != {"invocation", "dimensions"} or not isinstance(case["invocation"], str) or case["invocation"] not in {"pass", "fail", "not_measured"}:
            raise ValueError("invalid invocation")
        if not isinstance(case["dimensions"], dict) or set(case["dimensions"]) != set(DIMENSIONS):
            raise ValueError("invalid dimensions")
        for name, item in case["dimensions"].items():
            if not isinstance(item, dict) or set(item) != {"status", "method"}:
                raise ValueError("invalid dimension")
            if not isinstance(item["status"], str) or item["status"] not in {"pass", "fail", "not_measured"}:
                raise ValueError("invalid status")
            allowed = {"not_run"} if item["status"] == "not_measured" else METHODS[name]
            if not isinstance(item["method"], str) or item["method"] not in allowed:
                raise ValueError("invalid evidence method")
    if record["model"] is None:
        return "unbound"
    if record["product_version"] != current_version or record["payload_sha256"] != current_hash:
        return "different-payload"
    return "current-bounded"
```

이 모듈은 schema 1의 전체 과거 호스트 판정을 새 뜻으로 재검증하지 않는다. 기존 `test_contract.py`의 과거 필드/호스트/판정 형식 검사를 유지하고, 그 검사와 위 결속 검사를 분리한다. 입력의 `host_event`, `parser`, `semantic_review`는 운영자가 제출한 관측 방식 선언이며 이 순수 함수가 실제 실행 사실까지 인증하지 않는다. 관측 출처가 없으면 값을 만들어 넣지 않고 `not_measured/not_run`을 기록한다.

위 검사는 동일 버전/hash와 알려진 model, 실제 공통 hash 함수가 읽는 임시 reference 변이, boolean schema·추가 키·잘못된 날짜·빠진 차원, 중복 hop, fence 부재를 각각 다룬다. 일치하는 H1/H2가 있어도 문법·의미는 통과로 승격하지 않는다.

- [ ] **Step 4: 라이브 운영 문서·기존 계약 검사를 새 증거 의미로 맞춘다.**

`live/README.md`는 기존 schema 1 파일을 `historical-unbound`로 명시한다. 새 schema 2 기록은 위 FIELDS와 차원 구조를 사용하되, 이번 구현에서는 실제 새 기록 파일을 만들지 않는다. 실행일·model·클라이언트/실행기 값은 실제 관측값만 기록하고 모델을 확인할 수 없으면 `null`로 둔다. hash는 모든 payload 수정이 끝난 뒤 기존 `payload_sha256`으로 계산한다.

기존 `supported`와 현재 측정 상태를 같은 조건문으로 계산하지 않는다. 제품 지원 대상은 Codex/Claude Code 그대로이며 현재 2.0.0의 실제 실행 증거는 `not_measured`다. Grok 과거 실패와 Cursor 과거 미측정도 그대로 설명한다. 과거 테스트의 레지스트리 비교는 지원 대상 유지 검사로 이름/설명을 바꾸고, 과거 통과가 현재 payload를 검증했다고 해석하지 않는다.

`live/cases.json`의 세 기존 synthetic prompt는 유지한다. `expect`는 형식 관측/로딩 관측/미측정을 분리하도록 바꾸고 `test_contract.py`의 `LIVE_CASES_PAYLOAD`, 필드 집합, README marker 검사도 함께 조정한다. 설명을 요구하지 않는 near-miss는 invocation 차원만 판정하고 출력 차원은 미측정으로 둔다. 스킬 이름을 답변에 쓰거나 출력 chrome을 맞추는 것만으로 `skill_loading=pass`를 주지 않는다.

Mermaid parser/renderer가 이미 실행 가능하고 실행했을 때에만 `mermaid_syntax`에 해당 방법의 결과를 적는다. 이 작업은 parser/renderer 설치를 요구하지 않는다. 문법·인과·깊이 전환·접근성은 문서·정규식 검사로 대체하지 않는다. 전체 응답/비공개 prompt/자격증명은 저장소에 커밋하지 않는다.

- [ ] **Step 5: GREEN과 결속 반례를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py' -v`

Expected: 과거 기록을 수정하지 않고 모든 순수 검사 통과. 원본 smoke 파일은 `git diff -- tests/products/how-it-works/live/smoke-record.json` 출력이 비어 있어야 한다. 선택적 운영 모듈이 설치 payload에 들어가지 않았는지도 기존 payload 검사가 확인한다.

### Task 4: 2.0.0 문서·반복 설치·standalone 링크 정합성

**Files:**

- Modify: `skills/how-it-works/release.toml`, `SKILL.md` metadata, `CHANGELOG.md`, `README.md`, `README.en.md`.
- Modify: `tests/products/how-it-works/test_contract.py`의 version/README 문구 검사.
- Modify: `docs/maintainers/products/how-it-works/contract.md`, `testing.md`, `compatibility.md`, `release.md`.

**Interfaces:**

- Consumes: Task 1–3의 확정 계약과 통합 담당의 marker 기반 설치/링크 검사.
- Produces: version `2.0.0`, 두 README의 동일 Python 설치 블록, payload 밖 문서의 공개 저장소 URL. 공통 파일은 직접 고치지 않는다.

- [ ] **Step 1: 버전과 설치 블록 계약의 RED를 추가한다.**

```python
def test_v2_release_and_repeatable_install_contract(self) -> None:
    from scripts.lib.product_contract import load_product_release
    self.assertEqual(load_product_release(SKILL).version, "2.0.0")
    for filename in ("README.md", "README.en.md"):
        text = (SKILL / filename).read_text(encoding="utf-8")
        self.assertIn("<!-- how-it-works-local-links -->\n```python\n", text)
        self.assertNotIn(
            "ln -s \"$PWD/skills/how-it-works\" ~/.agents/skills/how-it-works", text
        )
        self.assertNotIn(
            "](../../docs/", text
        )
```

- [ ] **Step 2: RED를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p test_contract.py -v`

Expected: 1.0.0 버전/기존 링크 명령 때문에 실패. 파일 이름·버전 검사를 삭제해 통과시키지 않는다.

- [ ] **Step 3: 제품 README의 설치 코드를 아래 인터페이스로 교체한다.**

clone 뒤 `cd skills`를 명시한다. 아래 코드는 source와 target 두 인자를 받는 일회성 Python 블록이다. 별도의 영구 installer나 스킬 런타임을 추가하지 않는다. 두 README는 이 marker와 코드를 동일하게 유지한다.

````markdown
<!-- how-it-works-local-links -->
```python
import os
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: python3 - SOURCE TARGET")
source = Path(sys.argv[1]).expanduser().resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if not source.is_dir() or not (source / "SKILL.md").is_file():
    raise SystemExit("source must be a skill directory")
if target.is_symlink():
    try:
        same = target.resolve(strict=True) == source
    except (OSError, RuntimeError):
        same = False
    if same:
        print("already linked")
        raise SystemExit(0)
    raise SystemExit("refusing different or dangling link")
if target.exists():
    raise SystemExit("refusing existing file or directory")
target.parent.mkdir(parents=True, exist_ok=True)
try:
    target.symlink_to(source, target_is_directory=True)
except FileExistsError:
    raise SystemExit("target appeared during installation; inspect it before retrying")
print("linked")
```
````

README 실행 안내는 이 블록을 `python3 - SOURCE TARGET`의 표준입력으로 실행하는 일회성 here-document 방법을 설명한다. source 인자는 clone 뒤 `$PWD/skills/how-it-works`, target 인자는 호스트별 `$HOME/.agents/skills/how-it-works` 또는 `$HOME/.claude/skills/how-it-works`이며 각 target을 별도 호출한다. source/target은 반드시 인자로 인용해 전달한다. 여기서 실제 HOME 경로를 실행하지 않는다. 현재 대상으로 다른 파일/링크를 발견하면 자동 교체하지 않는다.

같은 payload의 `README.en.md`, `README.md`, `CHANGELOG.md` 링크는 상대 링크로 유지한다. `../../docs/...` 링크는 해당 실제 경로를 보존해 `https://github.com/beyondwin/skills/blob/main/docs/...`로 바꾼다. 이 변경은 설치본 경로 해석을 고치는 것이며 원격 URL의 HTTP 응답을 검증했다는 뜻이 아니다.

- [ ] **Step 4: 버전·이력을 한 변경으로 맞춘다.**

```toml
schema_version = 1
name = "how-it-works"
version = "2.0.0"
tag_prefix = "how-it-works-v"
license = "Apache-2.0"
```

`SKILL.md` metadata.version도 `2.0.0`으로 바꾸고 updated_at은 실제 구현일을 사용한다. `CHANGELOG.md`에는 실제 구현일의 2.0.0 항목을 추가하며 다음 내용을 기록한다: 명시 깊이/별칭 우선은 MAJOR 동작 변경; 숫자 문맥; 허점의 표 위치; 한국어/영어·출처 정책; 안전한 재설치·문서 링크; 과거 smoke는 새 버전의 라이브 통과 증거가 아님. 기존 1.0.0 미공개 이력은 남긴다. version 관련 기존 1.0.0 테스트와 release 문서 명령 예시를 2.0.0으로 맞추되 GitHub Release/tag가 생성되었다고 쓰지 않는다.

README의 지원 문장은 지원 대상 `codex/claude-code`와 역사적 측정일을 별개로 설명한다. 과거의 실패/미측정 상태를 현재 버전에서 실제 실행한 실패로 바꾸지 않는다. 공통 public docs의 기존 문구 고정·digest·버전 검사 수정은 통합 담당에게 넘긴다.

- [ ] **Step 5: GREEN과 통합 설치 반례를 확인한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py' -v`

Expected: 제품 계약 통과. 통합 담당에게 두 marker 블록을 전달하고 `tests/repository/test_installation_contract.py`가 공백 포함 임시 source/target에서 첫 설치, 같은 링크 반복, 실제 디렉터리, 다른 링크, 깨진 링크를 실행하도록 한다. source fixture는 `SKILL.md` 파일만 존재하면 되고 본문 frontmatter 유효성까지 요구하지 않는다. 첫/반복은 성공하고 반복 때 원본에 중첩 링크가 생기지 않아야 한다. 거부 경우에는 대상과 원본의 바이트·링크가 유지되어야 한다. 제품 작업자가 공통 테스트 파일을 동시에 수정하지 않으며, 제품 검사 통과를 공유 테스트 GREEN으로 보고하지 않는다.

### Task 5: 제품 증거를 봉합하고 통합 담당에게 인계

**Files:**

- Inspect: Task 1–4의 변경 파일 전체와 제품 관리자 문서.
- Modify only if a fresh failure requires it: 위 제품 소유 파일.
- No ownership: 공유 검증/배포 스크립트와 다른 제품 변경.

**Interfaces:**

- Consumes: 제품 2.0.0 payload, 정적 계약 결과, 합성 증거 검사 결과, 공통 설치/링크 검사 결과.
- Produces: 제품 단위 완료 근거와 미측정 항목, 통합 전체 profile·windows-portable·추출 ZIP 검사에 필요한 제품 경로/버전.

- [ ] **Step 1: 최종 변경 범위와 과거 기록 보존을 확인한다.**

Run: `git diff --name-only` 및 `git diff --check`.

Expected: 이 작업자가 쓴 변경은 명시한 제품 소유 경로 안에만 있다. 공유 작업자의 dirty 파일을 되돌리지 않는다. 과거 `smoke-record.json`은 변함없고 `synthetic-model`/합성 hash가 실제 실행 기록으로 추가되지 않았다.

- [ ] **Step 2: 제품 소유 테스트의 전체 discovery를 실행한다.**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/how-it-works -p 'test_*.py' -v`

Expected: 제품 소유 테스트와 새 `test_evidence_contract.py`가 실제 실행되고 exit 0. 현재 `--skill`의 `product-contract`는 공유 `tests.repository.test_release_contract`의 옛 버전 pin도 소비하므로, 이 단계에서 `--skill` GREEN을 요구하거나 주장하지 않는다. 공유 검사를 제품 작업자가 완화해서 통과시키지 않는다.

- [ ] **Step 3: 공통 단계·버전 pin 통합 후 최종 검증을 위임한다.**

통합 담당은 `scripts/lib/verification.py`의 `how-it-works-contract` pattern을 `test_*.py`로 변경하고 `tests/repository/test_verify.py`에 실제 소비 검사를 추가한다. 공유 release/version pin과 문서 고정도 통합한 다음 아래 순서로 실행한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill how-it-works
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
```

Expected: 제품 선택의 `product-contract`, `how-it-works-contract`, `python-compile`과 전체 profile이 exit 0이며, stage 소비 검사로 새 증거 테스트의 실행이 입증된다. `--skill` 성공만으로 repository 전체 검사가 수행되었다고 보고하지 않는다.

공통 배포 변경과 함께 how-it-works 2.0.0의 fresh standalone ZIP 추출본 검사를 수행한다. 동일 신뢰 원본은 통과하고 reference 바이트와 checksum을 함께 바꾼 변이는 거부되어야 한다. build/check의 깨끗한 추적 트리 요구와 release 절차는 통합 계획이 관리하며 이 제품 계획 때문에 사용자 WIP를 커밋·삭제하지 않는다. 이 제품의 버전 때문에 catalog lock을 갱신하지 않는다.

- [ ] **Step 4: 완료 증거를 다음 범위로 보고한다.**

문서/fixture 계약, 합성 fence/hop 검사, 메타데이터 결속 검사, 임시 경로 설치 검사, 추출 payload 검사 각각의 실행 명령과 exit 결과를 구분한다. 실제 skill loading·모델 깊이 준수·Mermaid 문법·의미 정확성·호스트별 시각/접근성 품질은 실행하지 않았으므로 `not_measured`다. 새 실패·변경이 없으면 전체 검증을 반복하지 않는다.

## 자기 검토와 남은 의존성

- H1/§5.3 우선순위·숫자 문맥·기존 제외 경계 → Task 1. 정책 변경의 RED를 기록한 다음 기존 기대값을 바꾸므로 옛 계약을 덮어쓰지 않는다.
- H2 여섯 요소·같은 hop·허점 Body 표·KO/EN·verified/unverified·비교 → Task 2.
- H3 역사적 미결속/현재 payload·model 결속과 지원 대상 분리 → Task 3. 과거 파일을 그대로 보존한다.
- H4 fence/hop/loading/syntax/meaning 차원과 미측정 → Task 3. 정규식은 문자 존재/ID 집합만 검사한다.
- §4.3 설치/링크·§6 2.0.0·문서/배포 정합성 → Task 4 및 통합 담당.
- §7 반례·제품/전체/portable/ZIP 경계·§8 소유권 → Task 5.
- 별도 필수 runtime/parser/provider나 실제 호출은 없다. 새 evidence 모듈은 제품 테스트 안에서만 소비한다.
- 아직 측정하지 않은 실제 모델·문법·의미 결과를 구현의 필수 유료 gate로 바꾸지 않는다. payload hash 결속은 서명이나 실제 실행 인증도 아니다.
- 구현 전 추가 사용자 정책 선택은 필요하지 않다. 공통 설치 검사는 `tests/repository/test_installation_contract.py`, 새 테스트의 stage 소비 검사는 `tests/repository/test_verify.py`에 있으며 통합 담당이 소유한다. 공유 버전 pin 갱신과 ZIP 실행 시점은 통합 계획에 따른다. 같은 파일을 여러 작업자가 수정하지 않는다.

계획 자체의 검토는 설계 커버리지·파일 소유권·함수 이름·기록 필드·테스트 명령을 대상으로 한다. 계획 안의 Python 코드는 구현 예시이며 이 문서를 작성하는 과정에서 제품 테스트나 실제 설치를 실행한 증거는 아니다.
