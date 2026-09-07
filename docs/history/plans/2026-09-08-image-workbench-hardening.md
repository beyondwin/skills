# Image Workbench Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** image-workbench의 입력 원본 보존, 좁은 파일 구조 검사, fixture 정답과 독립된 읽기 전용 행동 검사를 회복하고 standalone 문서 링크를 수정한다.

**Architecture:** 기존 stdlib inspector와 제품 evaluator의 진입점을 유지한다. inspector에는 출력 파일 동일성 검사와 이미 해석하는 형식의 필수 구조 검사를 추가하고, evaluator에는 expected/candidate 비교와 별개의 행동 불변식을 추가한다. 제품 payload·제품 테스트·제품 관리자 문서만 이 계획에서 변경하며 공통 검증과 배포 계약은 통합 담당에게 전달한다.

**Tech Stack:** Python 표준 라이브러리, unittest, JSON fixture, Markdown, TOML.

**Spec:** `docs/history/specs/2026-09-08-skills-hardening-design.md` — 승인된 §2, §3 I1–I3/R5, §4.3, §5.1, §6–8.

## Global Constraints

- 필수 구현 기준은 `b362972`다. 실행 checkout의 HEAD가 그 커밋을 조상으로 포함해야 한다. 설계서의 과거 감사 기준 `308bce9`로 checkout을 되돌리지 않는다.
- 설치 payload는 `skills/<name>/`, 제품 검증은 `tests/products/<name>/`, 관리자 계약은 `docs/maintainers/products/<name>/`에 둔다. `products.toml`의 `owned_paths`가 제품별 작업 경계다.
- 제품의 제안 버전은 `image-workbench | 2.0.2`다. 제품 version, SKILL metadata, CHANGELOG와 배포 검사는 함께 맞춘다.
- 새 스킬, 범용 프레임워크, 필수 외부 공급자, 텔레메트리, 저장소 분할을 추가하지 않는다. catalog lock/version도 유지한다.
- 현재 지원 호스트 범위를 넓히지 않는다. `supported_hosts = ["codex"]`와 기존 Codex image generation·local image viewing 전제를 유지한다.
- 같은 파일을 가리키는 상대 경로·절대 경로·symlink·hard link에서는 쓰기 전에 거부한다. 실패 시 입력 바이트는 보존된다.
- 원본과 무관한 기존 JSON 출력 파일의 현재 갱신 동작은 이번 수정에서 바꾸지 않는다.
- 완전한 비트스트림 디코딩, 시각 품질, 권리 검증을 성공했다고 출력하지 않는다. 기존 파일 사실 필드는 유지한다.
- `brief`/`audit`/no-op의 금지된 생성·교체 행동은 expected/candidate 값과 독립적으로 판정한다.
- 설치되는 README의 상대 링크는 payload 내부에서 해석 가능해야 한다. 저장소에만 있는 관리자/사용자 문서는 공개 저장소 URL로 연결한다.
- 실제 모델·이미지 생성·배포는 포함하지 않는다. 실제 설치본, 사용자 이미지, 자격 증명, catalog의 고정 바이트를 변경하지 않는다.
- R6의 물리적 모듈 분리·중앙 문서 digest 제거와 P5의 reviewer 역할·trigger 확대는 범위 밖이다.
- 현재 단계는 계획 작성이다. 아래의 구현·테스트 수정·커밋 명령은 이후 구현 실행 단계용이며 계획 승인만으로 실행하지 않는다.

---

## 파일 구조와 작업 순서

| 경로 | 책임 | 작업 |
| --- | --- | --- |
| `skills/image-workbench/scripts/inspect_asset.py` | 런타임 파일 사실과 입력 보존 | 1–3 |
| `tests/products/image-workbench/test_inspect_asset.py` | 실제 기존 binary fixture/helper를 쓰는 inspector 회귀 검사 | 1–3 |
| `tests/products/image-workbench/run.py` | 기존 evaluator self-test, 구조/행동 판정, mutation 검사 | 4 |
| `tests/products/image-workbench/test_payload_docs.py` | standalone 복사본의 README 링크 경계 검사, 신규 파일 | 5 |
| `skills/image-workbench/release.toml` | 제품 버전 원본 | 1 |
| `skills/image-workbench/SKILL.md` | version 복제와 좁은 inspector·행동 계약 | 1, 4, 5 |
| `skills/image-workbench/CHANGELOG.md` | `2.0.2` 출시 목표의 수정 이력 | 1–5 |
| `skills/image-workbench/README.md`, `README.en.md` | 설치 payload에서 읽는 공개 안내 | 5 |
| `skills/image-workbench/references/quality-rubric.md` | 파일 구조·시각 검사 증거의 경계 | 5 |
| `docs/maintainers/products/image-workbench/contract.md`, `testing.md`, `release.md` | 관리자용 구현·검증·배포 계약 | 5 |

작업 1 → 2 → 3은 같은 inspector와 테스트를 수정하므로 순차 진행한다. 작업 4는 조사·독립 리뷰를 병렬로 준비할 수 있지만 SKILL/CHANGELOG 변경과 커밋은 컨트롤러가 순차 적용한다. 작업 5는 1–4의 최종 계약을 문서에 묶는다. 각 작업의 Files 목록이 정확한 쓰기 allowlist다. `cases.json`의 현재 31개 정상 fixture와 category count는 그대로 보존하며 새 금지 반례는 evaluator self-test와 mutation 검사에 추가한다.

공통 `scripts/`, `products.toml`, `tests/repository/`, `docs/users/`, CI 파일은 이 계획의 쓰기 대상이 아니다. 이들 파일의 제품 버전·문서 문구 단언과 release smoke 변경 요청은 마지막 통합 인계에 모은다. 제품 코드 검사가 먼저 통과해야 하지만 공유 변경이 통합되기 전에 전체 저장소 게이트의 통과를 요구하지 않는다.

## 실행 준비

- [ ] 실행 컨트롤러가 별도 구현 승인을 확인하고 기존 dirty state를 기록한 뒤 격리 checkout에서 기준 커밋을 확인한다.

```bash
git merge-base --is-ancestor b362972 HEAD
git status --short
```

기대: 첫 명령 exit 0. 다른 작업자의 변경이 있으면 보존하고 해당 파일을 stage하지 않는다. 아래 명령의 기본 cwd는 저장소 루트이며 `PYTHONDONTWRITEBYTECODE=1`로 불필요한 캐시 파일을 만들지 않는다.

- [ ] 현재 제품 baseline을 한 번 기록한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
```

계획 작성 중 현재 helper로 독립 확인한 기존 결함은 IHDR CRC 오류, 필터 `5`, palette 없는 indexed PNG, 길이 `2`의 JPEG SOS, VP8L version `1`, expected/candidate 양쪽이 생성으로 바뀐 brief다. 현재 파서는 앞의 파일들을 수용했고 evaluator는 마지막 사례에 빈 오류 목록을 반환했다. 이는 계획의 반례 근거이며 이후 구현 단계의 RED 기록을 대신하지 않는다.

### Task 1: inspector 출력 별칭으로 인한 원본 손실 방지

**Files:**
- Modify: `skills/image-workbench/scripts/inspect_asset.py` — `main`의 출력 쓰기와 새 동일성 helper.
- Modify/Test: `tests/products/image-workbench/test_inspect_asset.py` — `AssetInspectorTests`.
- Modify: `skills/image-workbench/release.toml`.
- Modify: `skills/image-workbench/SKILL.md` — metadata만.
- Modify: `skills/image-workbench/CHANGELOG.md`.

**Interfaces:**
- Consumes: 기존 `inspect_file(path) -> AssetFacts`, `main(argv=None, output_stream=None, error_stream=None) -> int`, `StringSink`, `make_png(width, height, color_type, ...) -> bytes`.
- Produces: `_require_distinct_output(input_path: Path, output_path: Path) -> None`. 동일 파일이면 `ValueError`; 파일시스템 오류는 호출부의 stderr JSON 처리로 전달한다.
- 유지: 성공 JSON의 `alpha`, `byte_size`, `format`, `height`, `sha256`, `width`; 실패 exit 1·stderr 한 줄 JSON·빈 stdout; 관련 없는 출력 JSON 갱신.

- [ ] **Step 1: 독립 회귀 테스트를 먼저 추가한다.** 아래 메서드를 기존 `AssetInspectorTests`에 넣는다. 경로 시험은 공백이 있는 임시 디렉터리 안에서만 수행한다.

```python
    def test_output_aliases_preserve_source_bytes(self):
        data = make_png(3, 2, color_type=6)
        for spelling in ("absolute", "relative", "normalized"):
            with self.subTest(spelling=spelling), tempfile.TemporaryDirectory(prefix="image facts ") as directory:
                root = Path(directory)
                source = root / "asset.png"
                source.write_bytes(data)
                (root / "nested").mkdir()
                target = {
                    "absolute": str(source.resolve()),
                    "relative": os.path.relpath(source, Path.cwd()),
                    "normalized": str(root / "nested" / ".." / "asset.png"),
                }[spelling]
                stdout, stderr = StringSink(), StringSink()
                result = main([str(source), "--output", target], stdout, stderr)
                self.assertEqual(result, 1)
                self.assertEqual(source.read_bytes(), data)
                self.assertEqual(stdout.value, "")
                self.assertEqual(len(stderr.value.splitlines()), 1)
                error = json.loads(stderr.value)
                self.assertEqual(error["path"], str(source))
                self.assertTrue(error["error"])

    def test_output_symlink_alias_preserves_both_directions(self):
        data = make_png(3, 2, color_type=6)
        for reverse in (False, True):
            with self.subTest(reverse=reverse), tempfile.TemporaryDirectory(prefix="image facts ") as directory:
                source = Path(directory) / "asset.png"
                alias = Path(directory) / "alias.json"
                source.write_bytes(data)
                try:
                    alias.symlink_to(source)
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f"symlink unavailable on this host: {error}")
                input_path, output_path = (alias, source) if reverse else (source, alias)
                stdout, stderr = StringSink(), StringSink()
                self.assertEqual(main([str(input_path), "--output", str(output_path)], stdout, stderr), 1)
                self.assertTrue(alias.is_symlink())
                self.assertEqual(source.read_bytes(), data)
                self.assertEqual(alias.read_bytes(), data)
                self.assertEqual(stdout.value, "")
                self.assertEqual(json.loads(stderr.value)["path"], str(input_path))

    def test_output_hardlink_preserves_source_bytes(self):
        data = make_png(3, 2, color_type=6)
        with tempfile.TemporaryDirectory(prefix="image facts ") as directory:
            source = Path(directory) / "asset.png"
            alias = Path(directory) / "alias.json"
            source.write_bytes(data)
            try:
                os.link(source, alias)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"hard link unavailable on this host: {error}")
            stdout, stderr = StringSink(), StringSink()
            self.assertEqual(main([str(source), "--output", str(alias)], stdout, stderr), 1)
            self.assertTrue(source.samefile(alias))
            self.assertEqual(source.read_bytes(), data)
            self.assertEqual(alias.read_bytes(), data)
            self.assertEqual(stdout.value, "")
            self.assertTrue(json.loads(stderr.value)["error"])

    def test_existing_unrelated_json_output_is_updated(self):
        data = make_png(3, 2, color_type=6)
        with tempfile.TemporaryDirectory(prefix="image facts ") as directory:
            source = Path(directory) / "asset.png"
            output = Path(directory) / "facts.json"
            source.write_bytes(data)
            output.write_text('{"old": true}\n', encoding="utf-8")
            stdout, stderr = StringSink(), StringSink()
            self.assertEqual(main([str(source), "--output", str(output)], stdout, stderr), 0)
            self.assertEqual(source.read_bytes(), data)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {
                "alpha": True, "byte_size": len(data), "format": "png",
                "height": 2, "sha256": hashlib.sha256(data).hexdigest(), "width": 3,
            })
            self.assertEqual(stdout.value, "")
            self.assertEqual(stderr.value, "")
```

- [ ] **Step 2: RED를 기록한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -k output -v
```

기대: 동일·별칭 출력은 기존 코드에서 exit 0이 되어 실패하고, 정상 JSON 갱신 테스트는 이미 통과한다. macOS에서 symlink/hardlink 검사가 skip되면 해당 환경 문제를 기록하고 완료 근거로 삼지 않는다. 모든 플랫폼에서 skip 없는 링크 검사를 강제하거나 native Windows 지원을 새로 주장하지 않는다.

- [ ] **Step 3: 쓰기 직전 동일성 검사만 추가한다.** 같은 경로는 정규화로, hardlink는 inode 기반 `samefile`로 확인한다. 출력 파일 부재만 정상적인 새 출력으로 허용한다.

```python
def _require_distinct_output(input_path: Path, output_path: Path) -> None:
    if input_path.resolve() == output_path.resolve():
        raise ValueError("output path refers to the input asset")
    try:
        identical = input_path.samefile(output_path)
    except FileNotFoundError:
        return
    if identical:
        raise ValueError("output path refers to the input asset")
```

`main`의 `if args.output:` 블록을 다음으로 바꾼다. `inspect_file` 및 성공 JSON 생성은 그대로 둔다. 모든 기존 출력 파일을 거부하는 `exists()` gate나 exclusive-create 모드는 추가하지 않는다.

```python
    if args.output:
        try:
            _require_distinct_output(Path(args.path), Path(args.output))
            Path(args.output).write_text(rendered)
        except (OSError, ValueError) as error:
            message = error.strerror if isinstance(error, OSError) and error.strerror else str(error)
            _write_json({"error": message, "path": args.path}, error_stream)
            return 1
    else:
        output_stream.write(rendered)
```

이 변경은 검사 시점에 동일 파일인 경로를 차단하는 계약이다. 동시 외부 공격자가 경로를 교체하는 모든 TOCTOU 상황까지 해결했다고 확대해 설명하지 않는다.

- [ ] **Step 4: 최초 payload 변경과 같은 커밋에 버전과 실제 구현일을 맞춘다.** 아래 코드를 저장소 루트에서 한 번 실행해 `release.toml` version, `SKILL.md` metadata, CHANGELOG의 dated heading을 맞춘다. 계획 작성일을 구현일로 고정하지 않는다. `scripts/lib/product_contract.py::require_dated_changelog`와 `scripts/release.py::build_product`가 요구하는 날짜 제목은 출시 준비 형식이며 원격 공개 증거가 아니다. 기존 `2.0.0` 공개 사실을 보존한다.

```bash
python3 - <<'PY'
from datetime import date
from pathlib import Path
import re

root = Path("skills/image-workbench")
implementation_date = date.today().isoformat()
manifest = root / "release.toml"
manifest.write_text(manifest.read_text(encoding="utf-8").replace(
    'version = "2.0.1"', 'version = "2.0.2"', 1), encoding="utf-8")
skill = root / "SKILL.md"
text = skill.read_text(encoding="utf-8").replace('  version: "2.0.1"', '  version: "2.0.2"', 1)
text = re.sub(r'(?m)^  updated_at: "[0-9-]+"$', f'  updated_at: "{implementation_date}"', text, count=1)
skill.write_text(text, encoding="utf-8")
changelog = root / "CHANGELOG.md"
text = changelog.read_text(encoding="utf-8")
text = text.replace("## Unreleased\n", (
    f"## Unreleased\n\n## 2.0.2 - {implementation_date}\n\n"
    "Local release preparation only. No new GitHub tag or GitHub Release\n"
    "has been published for this version.\n"
), 1)
text = text.replace('target is `2.0.1`.', 'target is `2.0.2`.', 1)
changelog.write_text(text, encoding="utf-8")
PY
```

`2.0.2`의 날짜 제목 아래에 다음 Fixed 항목을 넣는다. 작업 2–5도 이 버전 영역에 변경별 항목을 추가하며 이후 실제 릴리스가 수행되기 전까지 미게시 설명을 유지한다. 공유 문서 검사에 기존 `2.0.1`/Unreleased 고정 단언이 있으면 통합 담당이 승인 설계 §6에 맞게 수정한다.

```markdown
### Fixed

- The inspector rejects output paths that alias the input asset, including
  symlinks and hard links, before writing. Existing unrelated JSON reports
  can still be updated.
```

- [ ] **Step 5: GREEN과 기존 inspector 계약을 확인한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -v
git diff --check
```

기대: 새 반례, 새 출력 JSON, 기존 오류 JSON·해시·크기 검사 모두 통과한다.

- [ ] **Step 6: 독립 리뷰 후 컨트롤러가 순차 커밋한다.** 리뷰어는 입력 보존과 관련 없는 JSON 갱신이 함께 유지되는지 확인한다. 오류 문자열 철자가 아니라 exit·stderr 형태·바이트 보존을 판단한다.

```bash
git add skills/image-workbench/scripts/inspect_asset.py tests/products/image-workbench/test_inspect_asset.py skills/image-workbench/release.toml skills/image-workbench/SKILL.md skills/image-workbench/CHANGELOG.md
git commit -m "fix(image-workbench): preserve input assets on aliased output"
```

### Task 2: PNG의 CRC·필터·indexed palette 최소 구조 검사

**Files:**
- Modify: `skills/image-workbench/scripts/inspect_asset.py` — PNG helpers와 `parse_png`.
- Modify/Test: `tests/products/image-workbench/test_inspect_asset.py` — 기존 fixture를 변형하는 회귀 테스트.
- Modify: `skills/image-workbench/CHANGELOG.md`.

**Interfaces:**
- Consumes: `make_png`, `make_png_with_idat`, `make_png_with_idat_chunks`, `parse_png(data) -> tuple[int, int, bool]`, 기존 `MAX_PNG_DECODED_BYTES = 64 * 1024 * 1024`, `PNG_CHANNELS`, `ADAM7_PASSES`, `_png_row_bytes`, `_png_decoded_byte_count`.
- Produces: `_png_scanline_sizes(width: int, height: int, bit_depth: int, color_type: int, interlace: int) -> Iterator[int]`, `_decode_png_idat(image_data: list[bytes], expected_size: int, scanline_sizes: Iterable[int]) -> None`.
- 유지: 기존 bytes/EOF/CRC/IDAT ordering/IEND 검사와 64 MiB cap. PNG reconstruction, palette index 픽셀 유효성, 완전한 decoder는 추가하지 않는다.

- [ ] **Step 1: CRC만 손상하거나 구조 한 조건만 바꾸는 반례를 추가한다.** 아래 메서드를 `AssetInspectorTests`에 추가한다. zlib와 다른 chunk CRC는 유효하게 유지하여 의도한 조건 때문에 실패하도록 한다.

```python
    def test_png_rejects_corrupt_ihdr_crc(self):
        data = bytearray(make_png(1, 1, color_type=6))
        data[29] ^= 1
        with self.assertRaises(ValueError):
            parse_png(bytes(data))

    def test_png_scanline_filter_bounds_across_idat_chunks(self):
        for filter_value in (0, 1, 2, 3, 4, 5, 255):
            with self.subTest(filter_value=filter_value):
                raw = b"\0\xff\xff\xff\xff" + bytes([filter_value]) + b"\xff" * 4
                compressed = zlib.compress(raw)
                data = make_png_with_idat_chunks(1, 2, 6, tuple(bytes([value]) for value in compressed))
                if filter_value <= 4:
                    self.assertEqual(parse_png(data), (1, 2, True))
                else:
                    with self.assertRaises(ValueError):
                        parse_png(data)

    def test_png_adam7_filter_positions_and_empty_passes(self):
        # 3x3 RGB8 Adam7 has six non-empty rows, including the filter byte.
        # Explicit independent fixture geometry: 4, 4, 7, 4, 4, 10 bytes.
        rows = [bytes([index % 5]) + b"\xff" * (size - 1)
                for index, size in enumerate((4, 4, 7, 4, 4, 10))]
        for broken in (False, True):
            with self.subTest(broken=broken):
                raw = bytearray(b"".join(rows))
                if broken:
                    raw[23] = 5  # Last pass filter, not an image sample.
                data = bytearray(make_png_with_idat(3, 3, 2, zlib.compress(raw)))
                data[28] = 1
                data[29:33] = struct.pack(">I", zlib.crc32(data[12:29]) & 0xFFFFFFFF)
                if broken:
                    with self.assertRaises(ValueError):
                        parse_png(bytes(data))
                else:
                    self.assertEqual(parse_png(bytes(data)), (3, 3, False))

    def test_indexed_png_requires_palette_without_trns(self):
        with self.assertRaises(ValueError):
            parse_png(make_png(1, 1, color_type=3))
        palette = b"\0\0\0\xff\xff\xff"
        self.assertEqual(
            parse_png(make_png(1, 1, color_type=3, before_trns=[(b"PLTE", palette)])),
            (1, 1, False),
        )

    def test_indexed_png_palette_size_respects_bit_depth(self):
        for entry_count in (2, 3):
            with self.subTest(entry_count=entry_count):
                data = bytearray(make_png(1, 1, 3, before_trns=[(b"PLTE", b"\0\0\0" * entry_count)]))
                data[24] = 1
                data[29:33] = struct.pack(">I", zlib.crc32(data[12:29]) & 0xFFFFFFFF)
                if entry_count == 2:
                    self.assertEqual(parse_png(bytes(data)), (1, 1, False))
                else:
                    with self.assertRaises(ValueError):
                        parse_png(bytes(data))
```

- [ ] **Step 2: RED를 기록한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -k png -v
```

기대: CRC, 필터 `5/255`, palette 부재·bit-depth 초과의 `ValueError` 기대가 실패한다. 정상 필터 `0..4`, 기존 alpha/tRNS, Adam7 정상 구조는 통과해야 한다. baseline 결함이 없어 보이면 테스트가 엉뚱한 CRC/길이 오류로 먼저 거부되는지 조사한다.

- [ ] **Step 3: IHDR CRC와 palette 검사를 보강한다.** `parse_png`에서 IHDR payload 해석 전에 아래 CRC 검사를 추가한다. 기존 indexed PLTE 분기에서 entry count를 계산한 직후 bit-depth 상한을 확인하고, 최종 IDAT 검사 전에 indexed PLTE 존재를 확인한다.

```python
    actual_ihdr_crc = struct.unpack(">I", data[29:33])[0]
    expected_ihdr_crc = zlib.crc32(data[12:29]) & 0xFFFFFFFF
    if actual_ihdr_crc != expected_ihdr_crc:
        raise ValueError("invalid PNG IHDR CRC")

    # In the existing indexed PLTE branch, after palette_entries assignment:
    if palette_entries > 1 << bit_depth:
        raise ValueError("PNG palette exceeds bit depth")

    # After IEND presence is verified and before IDAT decoding:
    if color_type == 3 and palette_entries is None:
        raise ValueError("missing PNG PLTE")
```

첫 블록과 나머지 두 블록을 서로 다른 명시 위치에 넣는다. 기존 PLTE 중복·길이·IDAT/tRNS ordering 조건은 삭제하지 않는다. CRC 및 indexed PLTE 조건은 [PNG 사양의 chunk layout·IHDR·PLTE](https://www.w3.org/TR/png-3/)에 따른다.

- [ ] **Step 4: 압축 해제 중 scanline 첫 바이트만 검사한다.** `collections.abc`에서 `Iterable`, `Iterator`를 import하고 아래 helper를 추가한다. `_png_decoded_byte_count`의 O(1)/7-pass 산술을 그대로 유지하여 거대한 header를 검사하면서 행 수만큼 먼저 순회하지 않는다.

```python
def _png_scanline_sizes(
    width: int, height: int, bit_depth: int, color_type: int, interlace: int
) -> Iterator[int]:
    if interlace == 0:
        row_size = 1 + _png_row_bytes(width, bit_depth, color_type)
        for _ in range(height):
            yield row_size
        return
    for start_x, start_y, step_x, step_y in ADAM7_PASSES:
        pass_width = max(0, (width - start_x + step_x - 1) // step_x)
        pass_height = max(0, (height - start_y + step_y - 1) // step_y)
        if pass_width and pass_height:
            row_size = 1 + _png_row_bytes(pass_width, bit_depth, color_type)
            for _ in range(pass_height):
                yield row_size
```

기존 `_decode_png_idat`을 다음으로 교체한다. 전체 raw image를 별도로 저장하거나 복사하지 않고, IDAT 경계에 걸친 행의 남은 바이트만 유지한다. 필터 `0..4`는 [PNG 필터 정의](https://www.w3.org/TR/png-3/#9Filters)의 조건이며 필터 역변환은 실행하지 않는다.

```python
def _decode_png_idat(
    image_data: list[bytes], expected_size: int, scanline_sizes: Iterable[int]
) -> None:
    decompressor = zlib.decompressobj()
    decoded_size = 0
    sizes = iter(scanline_sizes)
    row_remaining = 0
    for chunk in image_data:
        if decompressor.eof:
            if chunk:
                raise ValueError("invalid PNG image data")
            continue
        try:
            decoded = decompressor.decompress(chunk, expected_size - decoded_size + 1)
        except zlib.error as error:
            raise ValueError("invalid PNG image data") from error
        decoded_size += len(decoded)
        if decoded_size > expected_size or decompressor.unconsumed_tail:
            raise ValueError("PNG image data size mismatch")
        if decompressor.unused_data:
            raise ValueError("invalid PNG image data")
        cursor = 0
        while cursor < len(decoded):
            if row_remaining == 0:
                row_remaining = next(sizes, 0)
                if not row_remaining:
                    raise ValueError("PNG image data size mismatch")
                if decoded[cursor] > 4:
                    raise ValueError("invalid PNG scanline filter")
            consumed = min(row_remaining, len(decoded) - cursor)
            cursor += consumed
            row_remaining -= consumed
    if not decompressor.eof:
        raise ValueError("invalid PNG image data")
    if decoded_size != expected_size or row_remaining or next(sizes, None) is not None:
        raise ValueError("PNG image data size mismatch")
```

`parse_png`의 마지막 decode 호출을 다음으로 바꾼다. 최대 예상 바이트 검사 뒤에 iterator를 소비하는 순서를 유지한다.

```python
    _decode_png_idat(
        image_data,
        expected_decoded_size,
        _png_scanline_sizes(width, height, bit_depth, color_type, interlace),
    )
```

- [ ] **Step 5: CHANGELOG의 `2.0.2` Fixed에 범위를 기록하고 GREEN을 확인한다.**

```markdown
- PNG inspection now checks the IHDR CRC, scanline filter range across
  non-interlaced and Adam7 rows, and required indexed palette structure.
  Existing bounded decompression and file-fact reporting remain in place.
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -v
git diff --check
```

기대: 전체 inspector 검사 PASS. 특히 `test_png_rejects_oversized_or_dimension_mismatched_decoded_data`와 `test_png_accepts_empty_trailing_idat_after_zlib_eof_only`가 유지된다.

- [ ] **Step 6: 독립 리뷰 후 컨트롤러가 순차 커밋한다.** 리뷰어는 일반 픽셀 바이트 `255`를 필터 오류로 오인하지 않는지, Adam7의 빈 pass와 분할 IDAT가 유지되는지, cap을 완화하지 않았는지 확인한다.

```bash
git add skills/image-workbench/scripts/inspect_asset.py tests/products/image-workbench/test_inspect_asset.py skills/image-workbench/CHANGELOG.md
git commit -m "fix(image-workbench): reject malformed PNG structure"
```

### Task 3: JPEG SOS와 WebP 예약 version 구조 검사

**Files:**
- Modify: `skills/image-workbench/scripts/inspect_asset.py` — `parse_jpeg`, `parse_webp`.
- Modify/Test: `tests/products/image-workbench/test_inspect_asset.py`.
- Modify: `skills/image-workbench/CHANGELOG.md`.

**Interfaces:**
- Consumes: 기존 `make_jpeg(1, 1)`, `make_webp_vp8(1, 1)`, `make_webp_vp8l(1, 1)`, `make_webp_extended_vp8(1, 1, alpha)`, `parse_jpeg`, `parse_webp`.
- Produces: 기존 parser signatures와 반환 의미 유지. JPEG 첫 SOS의 길이·component selector, VP8의 예약 version, VP8L version을 거부하는 `ValueError` 경로.
- 유지: VP8L 단독 `alpha=None`, VP8X alpha flag, 현재 RIFF 길이·padding·chunk order·canvas 검사. JPEG entropy decode·후속 scan 전체 파싱·VP8 entropy decode를 추가하지 않는다.

- [ ] **Step 1: 실제 기존 정상 fixture를 변형하는 테스트를 추가한다.**

```python
    def test_jpeg_sos_requires_matching_component_structure(self):
        valid = make_jpeg(1, 1)
        sos = valid.index(b"\xff\xda")
        length = struct.unpack(">H", valid[sos + 2:sos + 4])[0]
        payload = valid[sos + 4:sos + 2 + length]
        suffix = valid[sos + 2 + length:]
        self.assertEqual(payload[0], 3)
        variants = {
            "empty_header": b"",
            "zero_components": b"\0\0\x3f\0",
            "count_mismatch": bytes([2]) + payload[1:],
            "unknown_component": payload[:1] + b"\x7f" + payload[2:],
            "duplicate_component": payload[:3] + payload[1:2] + payload[4:],
            "invalid_table_selector": payload[:2] + b"\x40" + payload[3:],
        }
        self.assertEqual(parse_jpeg(valid), (1, 1, False))
        for name, scan_header in variants.items():
            with self.subTest(name=name):
                data = (valid[:sos] + b"\xff\xda"
                        + struct.pack(">H", len(scan_header) + 2)
                        + scan_header + suffix)
                with self.assertRaises(ValueError):
                    parse_jpeg(data)

    def test_webp_vp8_rejects_reserved_versions(self):
        valid = make_webp_vp8(1, 1)
        self.assertEqual(parse_webp(valid), (1, 1, False))
        for version in (4, 5, 6, 7):
            with self.subTest(version=version):
                data = bytearray(valid)
                data[20] = (data[20] & ~0x0E) | (version << 1)
                with self.assertRaises(ValueError):
                    parse_webp(bytes(data))

    def test_webp_vp8l_rejects_nonzero_version_preserves_alpha_hint(self):
        valid = make_webp_vp8l(1, 1)
        for version in range(1, 8):
            with self.subTest(version=version):
                data = bytearray(valid)
                data[24] = (data[24] & 0x1F) | (version << 5)
                with self.assertRaises(ValueError):
                    parse_webp(bytes(data))
        alpha_hint = bytearray(valid)
        alpha_hint[24] |= 0x10
        self.assertEqual(parse_webp(bytes(alpha_hint)), (1, 1, None))

    def test_webp_vp8x_reserved_bits_remain_rejected(self):
        valid = make_webp_extended_vp8(1, 1, alpha=True)
        self.assertEqual(parse_webp(valid), (1, 1, True))
        for offset, mask in ((20, 0x01), (20, 0x40), (20, 0x80), (21, 1), (22, 1), (23, 1)):
            with self.subTest(offset=offset, mask=mask):
                data = bytearray(valid)
                data[offset] |= mask
                with self.assertRaises(ValueError):
                    parse_webp(bytes(data))
```

- [ ] **Step 2: RED를 기록한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -k jpeg -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -k webp -v
```

기대: SOS 구조와 VP8/VP8L version 반례는 `ValueError not raised`로 실패한다. VP8X reserved regression은 기존 구현에서 이미 PASS이며 이 결과를 새로 수정한 결함으로 보고하지 않는다.

- [ ] **Step 3: JPEG 첫 SOS의 해석 가능한 필수 구조만 확인한다.** `parse_jpeg`의 `dimensions = None` 옆에 `frame_component_ids = set()`을 추가한다. SOF에서 기존 component 길이 조건을 정확한 `8 + 3 * components`와 일치하는지 확인하고, 해당 IDs를 저장한다. SOS에서 기존 scan/EOI 검사 직전에 다음 조건을 넣는다.

```python
    # In SOF processing, after reading the component count:
    if components == 0 or segment_length != 8 + 3 * components:
        raise ValueError("invalid JPEG SOF")
    identifiers = data[offset + 8:offset + segment_length:3]
    if len(set(identifiers)) != components:
        raise ValueError("invalid JPEG SOF component identifiers")
    frame_component_ids = set(identifiers)

    # In SOS processing, after requiring a preceding SOF:
    if segment_length < 6:
        raise ValueError("invalid JPEG SOS")
    scan_components = data[offset + 2]
    if not 1 <= scan_components <= 4 or segment_length != 6 + 2 * scan_components:
        raise ValueError("invalid JPEG SOS component count")
    selectors = data[offset + 3:offset + 3 + 2 * scan_components:2]
    tables = data[offset + 4:offset + 4 + 2 * scan_components:2]
    if len(set(selectors)) != scan_components or not set(selectors) <= frame_component_ids:
        raise ValueError("invalid JPEG SOS component selectors")
    if any((table >> 4) > 3 or (table & 0x0F) > 3 for table in tables):
        raise ValueError("invalid JPEG SOS table selectors")
```

근거는 [ITU T.81 Annex B.2.2–B.2.3](https://www.w3.org/Graphics/JPEG/itu-t81.pdf)의 frame/scan header 구조다. SOF marker 종류에 따라 의미가 다른 spectral/successive approximation 필드를 baseline JPEG 값 하나로 고정하지 않는다. 지원하는 모든 JPEG 변형을 완전하게 검증한다고 설명하지 않는다.

- [ ] **Step 4: WebP의 version 비트를 검사한다.** 기존 VP8 signature/최소 payload 길이 검사 다음에 첫 블록을, VP8L packed integer를 읽은 다음에 둘째 블록을 추가한다.

```python
        # VP8 three-byte frame tag: version occupies bits 1..3.
        version = (payload[0] >> 1) & 0x07
        if version > 3:
            raise ValueError("unsupported WebP VP8 version")

        # VP8L packed header: width 14, height 14, alpha hint 1, version 3.
        if (packed >> 29) != 0:
            raise ValueError("unsupported WebP VP8L version")
```

VP8의 `0..3`과 예약 값 구분은 [RFC 6386 §9.1](https://www.rfc-editor.org/rfc/rfc6386.html#section-9.1), VP8L version `0`은 [RFC 9649 §3.4](https://www.rfc-editor.org/rfc/rfc9649.html#section-3.4)에 따른다. alpha hint를 version과 혼동하지 않고 기존 `alpha=None` 계약을 유지한다.

- [ ] **Step 5: CHANGELOG를 추가하고 GREEN을 확인한다.**

```markdown
- JPEG inspection rejects malformed first-scan headers and invalid component
  selectors. WebP inspection rejects reserved VP8 versions and nonzero VP8L
  versions while preserving existing alpha reporting.
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_inspect_asset.py -v
git diff --check
```

기대: 기존 정상 JPEG/VP8/VP8L/VP8X facts와 신규 반례 모두 PASS.

- [ ] **Step 6: 독립 리뷰 후 컨트롤러가 순차 커밋한다.** header 한 조건을 깨뜨린 fixture가 해당 검사 때문에 거부되는지 검토한다. generic exception이나 IndexError를 성공으로 취급하지 않는다.

```bash
git add skills/image-workbench/scripts/inspect_asset.py tests/products/image-workbench/test_inspect_asset.py skills/image-workbench/CHANGELOG.md
git commit -m "fix(image-workbench): validate JPEG scan and WebP version headers"
```

### Task 4: expected/candidate 동시 오염과 독립된 행동 불변식

**Files:**
- Modify/Test: `tests/products/image-workbench/run.py` — 기존 `EvaluatorTests`, `evaluate_candidate`, `run_mutation_checks`, mutation 결과 문구.
- Modify: `skills/image-workbench/SKILL.md` — mode/no-op 경계 명확화.
- Modify: `skills/image-workbench/CHANGELOG.md`.

**Interfaces:**
- Consumes: `EvaluatorTests.valid_case(**overrides: object) -> dict[str, object]`, `load_cases(path: pathlib.Path) -> list[dict[str, object]]`, `_reference_case(cases_by_id, case_id)`, 기존 `evaluate_candidate(case) -> list[str]`, `validate_case(case) -> list[str]`.
- Produces: `_action_invariant_errors(case: dict[str, object]) -> list[str]`. request 문장이나 fixture 정답 비교에 의존하지 않고 각 side의 mode/route/trigger/action 조합을 검사한다.
- 유지: fixture schema `"1"`, 기존 31개 정상 cases와 category count, 기존 pair mismatch·role·status·replacement authority 검사, 기존 CLI `--self-test`/`--scope full`.

- [ ] **Step 1: 양쪽 값을 같이 오염시키는 회귀 테스트를 기존 `EvaluatorTests`에 추가한다.** 교체 권한이 true여도 읽기 전용 모드는 파일을 만들거나 교체할 수 없다. 테스트는 새 오류의 특정 문구를 요구하지 않는다.

```python
    def test_read_only_actions_are_rejected_when_both_sides_agree(self):
        for mode, route, trigger in (("brief", "brief", True), ("audit", "audit", True), ("none", "no_op", False)):
            for action in ("builtin_imagegen", "new_file", "replace_existing"):
                with self.subTest(mode=mode, action=action):
                    case = self.valid_case(
                        candidate_mode=mode, expected_mode=mode,
                        candidate_route=route, expected_route=route,
                        candidate_trigger=trigger, expected_trigger=trigger,
                        replacement_authorized=True,
                    )
                    if action == "builtin_imagegen":
                        case.update(candidate_tool_action=action, expected_tool_action=action)
                    else:
                        case.update(candidate_destination_action=action, expected_destination_action=action)
                    self.assertEqual(validate_case(case), [])
                    self.assertTrue(evaluate_candidate(case))

    def test_action_invariants_use_each_side_without_relying_on_pair_mismatch(self):
        case = self.valid_case(
            candidate_mode="generate", expected_mode="generate",
            candidate_route="no_op", expected_route="no_op",
            candidate_tool_action="builtin_imagegen", expected_tool_action="builtin_imagegen",
        )
        self.assertEqual(validate_case(case), [])
        self.assertTrue(evaluate_candidate(case))
        case.update(candidate_route="raster_generate", expected_route="raster_generate",
                    candidate_trigger=False, expected_trigger=False)
        self.assertEqual(validate_case(case), [])
        self.assertTrue(evaluate_candidate(case))

    def test_existing_authorized_generation_edit_and_no_op_stay_valid(self):
        cases = load_cases(pathlib.Path(__file__).with_name("cases.json"))
        selected = {
            "auth-generate-tool", "auth-edit-target-tool", "save-replacement-authorized",
            "auth-brief-no-tool", "auth-audit-no-tool", "near-miss-legacy-kws-invocation",
            "near-miss-svg", "save-preview-only", "auth-edit-missing-target-hold",
        }
        self.assertEqual({str(case["id"]) for case in cases} & selected, selected)
        for case in cases:
            if case["id"] in selected:
                with self.subTest(case_id=case["id"]):
                    self.assertEqual(validate_case(case), [])
                    self.assertEqual(evaluate_candidate(case), [])
```

- [ ] **Step 2: RED를 기록한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
```

기대: expected/candidate가 함께 금지 행동으로 바뀐 사례에서 오류 목록이 비어 실패한다. 정상 31개 fixture의 현재 값을 금지 행동으로 바꿔 새 정책의 정답처럼 만들지 않는다.

- [ ] **Step 3: pair 비교 전에 별도의 불변식 결과를 합친다.** 아래 helper를 `evaluate_candidate` 앞에 넣고 해당 함수의 초기 `errors`를 `_action_invariant_errors(case)`로 바꾼다. 기존 pair/role/status/authority 코드는 유지한다. 이 helper를 schema validator에 중복 호출하지 않아 schema 오류와 행동 위반을 구분한다.

```python
def _action_invariant_errors(case: dict[str, object]) -> list[str]:
    case_id = str(case.get("id", "<unknown>"))
    errors: list[str] = []
    for side in ("candidate", "expected"):
        read_only = (
            case.get(f"{side}_mode") in {"brief", "audit", "none"}
            or case.get(f"{side}_route") in {"brief", "audit", "no_op"}
            or case.get(f"{side}_trigger") is False
        )
        if not read_only:
            continue
        if case.get(f"{side}_tool_action") == "builtin_imagegen":
            errors.append(f"{case_id}: {side} read-only action cannot generate")
        if case.get(f"{side}_destination_action") in {"new_file", "replace_existing"}:
            errors.append(f"{case_id}: {side} read-only action cannot write an asset")
    return errors
```

여기서 `new_file`/`replace_existing`은 기존 이미지 산출물 destination enum이다. brief의 텍스트 답변 작성이나 audit의 기존 이미지 열람을 막는 새 정책으로 확대하지 않는다. `preview`/`hold` 같은 비쓰기 상태를 blanket 거부하지 않는다.

- [ ] **Step 4: full-scope mutation에도 co-mutation 9개를 넣는다.** 기존 8개 mutation을 모두 보존한 채 `run_mutation_checks`의 반환 직전에 아래 블록을 추가한다. 실제 fixture에서 각 모드의 정상 사례를 가져오며 없는 fixture는 기존 `_reference_case`의 오류로 드러난다.

```python
    for case_id in ("auth-brief-no-tool", "auth-audit-no-tool", "near-miss-legacy-kws-invocation"):
        for action in ("builtin_imagegen", "new_file", "replace_existing"):
            mutated, lookup_errors = _reference_case(cases_by_id, case_id)
            errors.extend(lookup_errors)
            if mutated is None:
                continue
            mutated["replacement_authorized"] = True
            field = "tool_action" if action == "builtin_imagegen" else "destination_action"
            for side in ("candidate", "expected"):
                mutated[f"{side}_{field}"] = action
            if not validate_case(mutated) + evaluate_candidate(mutated):
                errors.append(f"mutation: {case_id} co-mutated {field} was accepted")
```

CLI의 기존 `8 mutation checks: PASS` 출력은 실제 새 개수에 맞는 `17 mutation checks: PASS`로 변경한다. 31개 fixture category count와 의미를 바꾸지 않는다. 오류 문자열의 특정 철자로만 불변식의 성공을 판단하는 새 테스트는 쓰지 않는다.

- [ ] **Step 5: SKILL과 CHANGELOG를 좁게 맞춘다.** `Mode And Authorization`의 기존 읽기 전용 문단 바로 뒤에 다음 문단을 추가한다. no-op activation 문단의 기존 규칙은 유지한다.

```markdown
Read-only modes and no-op routes do not generate, create, or replace image
assets. A replacement authorization does not change a brief, audit, or no-op
into an edit request.
```

CHANGELOG의 `2.0.2` Fixed에 추가한다.

```markdown
- Offline evaluation now rejects generation and asset writes in brief,
  audit, and no-op decisions even when candidate and expected values agree
  on the prohibited action.
```

- [ ] **Step 6: self-test와 full evaluator의 GREEN을 확인한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
git diff --check
```

기대: 기존 및 신규 self-test PASS, 31 fixture PASS, 17 mutation PASS. 라이브 generation을 실행한 증거로 표현하지 않는다. `canonical_frontmatter()`의 `2.0.1`은 문법 단위시험의 독립 유효 문자열이며 현재 제품 버전을 읽는 시험이 아니므로 이 작업에서 기계적으로 교체할 필요가 없다.

- [ ] **Step 7: 독립 리뷰 후 컨트롤러가 순차 커밋한다.** 리뷰어는 두 값을 함께 바꾼 반례가 pair mismatch 없이도 실패하는지, 정상 authorized replacement/edit와 preview/hold가 유지되는지 확인한다.

```bash
git add tests/products/image-workbench/run.py skills/image-workbench/SKILL.md skills/image-workbench/CHANGELOG.md
git commit -m "fix(image-workbench): enforce independent read-only action invariants"
```

### Task 5: standalone 문서 링크와 검사 증거 경계 정합화

**Files:**
- Create/Test: `tests/products/image-workbench/test_payload_docs.py`.
- Modify: `skills/image-workbench/README.md`.
- Modify: `skills/image-workbench/README.en.md`.
- Modify: `skills/image-workbench/SKILL.md` — Inspect And Evaluate와 inspector output 안내만.
- Modify: `skills/image-workbench/references/quality-rubric.md`.
- Modify: `skills/image-workbench/CHANGELOG.md`.
- Modify: `docs/maintainers/products/image-workbench/contract.md`.
- Modify: `docs/maintainers/products/image-workbench/testing.md`.
- Modify: `docs/maintainers/products/image-workbench/release.md`.

**Interfaces:**
- Consumes: 작업 1–4의 `main`, `AssetFacts`, PNG/JPEG/WebP 구조 검사, `_action_invariant_errors`, 버전 `2.0.2`.
- Produces: standalone payload에서 해석 가능한 README 링크, 지원 범위를 과장하지 않는 두 언어 안내, 제품 오프라인 검사 명령과 통합 담당 인계.
- 링크 계약: payload 내부 파일은 상대 링크 유지, 저장소 문서는 `https://github.com/beyondwin/skills/blob/main/docs/...` 공개 URL. 네트워크 응답 확인을 로컬 링크 검사 결과로 주장하지 않는다.

- [ ] **Step 1: standalone 복사본에서 링크 탈출을 잡는 테스트 파일을 작성한다.** 이 테스트는 공유 링크 validator를 새로 만드는 대신 이 제품 README 두 개의 설치 경계만 검사한다.

```python
from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PAYLOAD = REPOSITORY_ROOT / "skills" / "image-workbench"
DOC_PREFIX = "/beyondwin/skills/blob/main/docs/"


class PayloadDocumentationTests(unittest.TestCase):
    def test_readme_links_work_from_standalone_payload(self):
        with tempfile.TemporaryDirectory(prefix="image payload ") as directory:
            root = Path(directory) / "image-workbench"
            shutil.copytree(PAYLOAD, root)
            for name in ("README.md", "README.en.md"):
                document = root / name
                targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8"))
                self.assertTrue(targets, name)
                for target in targets:
                    with self.subTest(document=name, target=target):
                        parsed = urlsplit(target)
                        if parsed.scheme:
                            self.assertEqual(parsed.scheme, "https")
                            self.assertEqual(parsed.netloc, "github.com")
                            self.assertTrue(parsed.path.startswith(DOC_PREFIX))
                            relative = "docs/" + unquote(parsed.path[len(DOC_PREFIX):])
                            self.assertTrue((REPOSITORY_ROOT / relative).is_file())
                            continue
                        resolved = (document.parent / unquote(parsed.path)).resolve()
                        self.assertTrue(resolved.is_relative_to(root.resolve()), target)
                        self.assertTrue(resolved.is_file(), target)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: RED를 기록한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p test_payload_docs.py -v
```

기대: 기존 `../../docs/users/...` 및 `../../docs/maintainers/...`가 standalone payload 밖으로 나가므로 `is_relative_to` assertion이 실패한다. 원격 URL의 실제 HTTP 응답은 이 테스트의 범위가 아니다.

- [ ] **Step 3: README의 저장소 문서 링크만 공개 URL로 바꾸고 검사 범위를 설명한다.** 아래 매핑을 한국어/영어 README 각각에 적용한다. `[English](README.en.md)`, `[한국어](README.md)`, `[CHANGELOG](CHANGELOG.md)`는 그대로 둔다.

| 현재 링크 경로 | 새 링크 경로 |
| --- | --- |
| `../../docs/users/ko/compatibility.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md` |
| `../../docs/users/ko/installation.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/ko/installation.md` |
| `../../docs/users/ko/safety-and-privacy.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md` |
| `../../docs/users/ko/verification.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md` |
| `../../docs/users/en/compatibility.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/en/compatibility.md` |
| `../../docs/users/en/installation.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/en/installation.md` |
| `../../docs/users/en/safety-and-privacy.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/en/safety-and-privacy.md` |
| `../../docs/users/en/verification.md` | `https://github.com/beyondwin/skills/blob/main/docs/users/en/verification.md` |
| `../../docs/maintainers/products/image-workbench/contract.md` | `https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/contract.md` |
| `../../docs/maintainers/products/image-workbench/testing.md` | `https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/testing.md` |
| `../../docs/maintainers/products/image-workbench/compatibility.md` | `https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/compatibility.md` |
| `../../docs/maintainers/products/image-workbench/release.md` | `https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/image-workbench/release.md` |

두 README의 기존 inspector 안내 바로 뒤에 각각 다음 문단을 추가한다.

```markdown
검사기는 PNG의 CRC·scanline 필터·필수 indexed palette, JPEG 첫 SOS 구조,
WebP의 해석 가능한 header/version 등 일부 필수 구조를 확인합니다. 통과해도
완전한 비트스트림 디코딩이나 시각 품질·권리 확인을 뜻하지 않습니다. 최종
후보는 반드시 열어서 확인합니다. `--output facts.json`은 별도 JSON 보고서를
갱신할 수 있지만 입력 이미지와 같은 파일을 가리키면 쓰기 전에 거부합니다.
```

```markdown
The inspector checks selected required structures, including PNG CRCs,
scanline filters and indexed palettes, the first JPEG SOS header, and
interpreted WebP header/version fields. Passing does not prove complete
bitstream decoding, visual quality, or rights clearance. Open every final
candidate for visual review. `--output facts.json` can update a separate JSON
report, but rejects any output that refers to the input image before writing.
```

- [ ] **Step 4: SKILL/rubric/관리자 계약에 같은 증거 경계를 반영한다.** 아래 영문 문단을 `SKILL.md`의 inspector 설명 다음과 `quality-rubric.md`의 Mechanical Criteria에 넣는다. 기존 `Open every candidate`, `Visual review remains required`, 네 evidence status 정의는 유지한다.

```markdown
The inspector verifies selected file facts and required parsed structure,
not complete bitstream decoding. Visual quality and rights remain separate
checks. Its JSON output must not alias the input asset; a separate existing
JSON report may be updated.
```

`contract.md`의 파일 사실 설명 뒤에 다음 계약을 넣는다. 앞서 존재하는 unsupported “경로 준비 상태” 주장을 실제 destination 배포 성공으로 확대하지 않는다.

```markdown
inspector 출력은 입력과 정규화 경로 또는 파일 동일성이 같으면 거부합니다.
symlink와 hard link를 포함하며 입력 바이트는 보존합니다. 별도의 기존 JSON
보고서를 갱신하는 동작은 유지합니다. 성공 JSON 필드와 stderr 한 줄 오류
형식은 바꾸지 않습니다.

PNG의 IHDR CRC·scanline 필터·indexed PLTE, JPEG 첫 SOS의 길이·component
selector, WebP version 등 해석하는 구조의 필수 조건을 검사합니다. 완전한
비트스트림 디코딩, 모든 PNG/JPEG/WebP 변형의 검증, 시각 품질, 권리 검증은
이 검사 결과로 입증하지 않습니다. 최종 후보를 열어 보는 시각 검사는 별도
필수입니다.

오프라인 evaluator는 expected/candidate의 단순 일치와 별개로 brief·audit·
no-op의 이미지 생성·신규 저장·교체를 거부합니다. 교체 허용 값이 true여도
읽기 전용 모드의 권한을 확대하지 않습니다.
```

`testing.md`의 결정적 픽스처 목록에 `test_payload_docs.py`의 standalone 링크 경계와 `run.py`의 co-mutation 9개를 추가하고, 명령 블록은 기존 명령과 아래 추출본 검사 명령을 함께 제공한다. `release.md`에는 `2.0.2`가 출시 목표이며 tag/push/공개가 수행된 증거가 아니라는 설명을 넣고, checksum·신뢰 소스 hash 비교의 공통 코드 소유권은 통합 담당임을 적는다.

```markdown
- `test_payload_docs.py`는 임시 standalone 복사본의 README 상대 링크가
  payload 안에서 해석되는지 확인합니다. 공개 docs URL은 저장소 안의 대응
  파일까지만 검사하며 원격 HTTP 응답을 증명하지 않습니다.
- evaluator는 기존 8개 mutation에 expected/candidate 동시 오염 9개를 더해
  읽기 전용 행동 경계를 검사합니다. 실제 이미지 호출 없이 실행합니다.
```

CHANGELOG의 `2.0.2` Fixed에는 다음 항목을 추가하고, 기존 Notes의 미게시 경계를 보존한다.

```markdown
- Standalone README links to repository documentation use public URLs.
  Inspector documentation now distinguishes selected structural checks
  from complete decoding, visual review, and rights verification.
```

- [ ] **Step 5: 제품 오프라인 GREEN과 문서 diff를 확인한다.**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/image-workbench -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --self-test
PYTHONDONTWRITEBYTECODE=1 python3 tests/products/image-workbench/run.py --scope full
git diff --check
```

기대: 제품 테스트, fixture, mutation 모두 PASS. 특정 안내 문구 포함만으로 시각 품질·실제 스킬 행동을 검증했다고 보고하지 않는다. README와 rubric의 실제 내용을 독립 리뷰어가 읽어 기존 시각 QA를 약화하지 않았는지 확인한다.

- [ ] **Step 6: 독립 리뷰 후 컨트롤러가 순차 커밋한다.**

```bash
git add tests/products/image-workbench/test_payload_docs.py skills/image-workbench/README.md skills/image-workbench/README.en.md skills/image-workbench/SKILL.md skills/image-workbench/references/quality-rubric.md skills/image-workbench/CHANGELOG.md docs/maintainers/products/image-workbench/contract.md docs/maintainers/products/image-workbench/testing.md docs/maintainers/products/image-workbench/release.md
git commit -m "docs(image-workbench): align standalone links and inspection evidence"
```

## 통합 담당 인계와 최종 검증

제품 컨트롤러는 아래 요청과 제품 task별 RED/GREEN·리뷰 결과를 통합 담당에게 전달한다. 이 절의 shared 명령은 공통 계획의 변경이 합쳐진 뒤 통합 담당이 실행한다.

- `tests/repository`의 공개 문서 단언이 저장소 밖 상대 링크를 강제한다면 승인 설계 §4.3의 공개 URL 계약으로 고친다. digest·극성·모순 검사 자체를 제거하지 않는다.
- 공유 `docs/users`의 image inspector 검증 범위와 `2.0.2` 관련 사실을 실제 구현에 맞춘다. 공통 clone/link 설치 멱등성 코드는 R4의 통합 담당이 수정한다. 이 제품은 실제 설치 경로를 갱신하지 않는다.
- 공통 selector에 새 `test_payload_docs.py`가 기존 `image-inspector`의 `test_*.py` discovery로 포함되는지 확인한다. 제품 evaluator의 mutation 성공 개수는 실제 17개로 반영한다.
- `tests/repository/test_release_contract.py`의 version pin과 공유 문서의 기존 버전/Unreleased 고정 단언은 통합 담당이 승인 설계 §6에 맞게 갱신한다. release check/build가 `release.toml`의 `2.0.2`, SKILL metadata, 실제 구현일의 dated changelog를 함께 읽는지 확인한다. 이전 `2.0.0` 공개 증거와 현재 미게시 목표를 혼동하지 않는다.
- verify-download는 공통 R2 계약의 checksum → ZIP 구조 → 안전한 추출 → metadata → 로컬 신뢰 payload hash → 추출 smoke 순서에 따라 이 제품을 검사한다. 원본과 checksum이 함께 바뀐 archive 반례는 공통 계획이 소유한다.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill image-workbench
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile windows-portable
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py check --product image-workbench
```

위 `--profile windows-portable` 옵션과 제품 `image-inspector`의 `test_*.py` discovery는 현재 `scripts/verify.py`와 `scripts/lib/verification.py`에서 확인했다. 전체 suite와 windows-portable은 통합 담당이 한 번 실행한다. 새 실패나 변경이 없으면 같은 전체 검증을 반복하지 않는다. portable 통과는 native Windows symlink/recorder 실행 증거가 아니다.

통합 후 깨끗한 추적 트리에서 로컬 standalone build·추출본 검사·verify-download를 다음처럼 실행한다. 출력은 임시 디렉터리에만 두고 publish/tag/push는 하지 않는다. 각 shell invocation이 별개이면 `IMAGE_HARDENING_ARTIFACTS` 값은 컨트롤러가 같은 terminal session에서 유지한다.

```bash
IMAGE_HARDENING_ARTIFACTS=$(mktemp -d)
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py build --product image-workbench --output "$IMAGE_HARDENING_ARTIFACTS"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/release.py verify-download --product image-workbench --input "$IMAGE_HARDENING_ARTIFACTS"
```

출력 폴더는 `mktemp -d`로 만든 빈 디렉터리이므로 기존 사용자 파일을 덮어쓰지 않는다. 실제 다운로드가 아닌 로컬 build 산출물임을 보고한다. 현재 `scripts/release.py::_run_inspector`는 추출 inspector 경로를 `IMAGE_WORKBENCH_INSPECTOR`에 넣고 이 제품의 `test_*.py`를 실행한다. 같은 smoke는 evaluator의 `--scope full --skill-root`에 추출 skill root를 전달한다. 통합 담당은 이 연결을 유지하고 그 결과를 추출본 회귀 근거로 기록한다. 동일 archive를 수동 재추출해 같은 suite를 중복 실행하지 않는다. 새 `test_payload_docs.py`는 저장소 payload의 standalone 복사를 검사하므로 원격 문서 HTTP 응답이나 archive provenance를 검증한 것으로 보고하지 않는다.

제품 완료 보고는 수정 범위, task별 RED/GREEN·독립 리뷰, 제품 gate, 추출본 gate, 공통 통합 gate 결과를 구분한다. 실제 모델 행동, 생성 이미지 품질, 상업적 권리, 새 호스트 지원, 원격 배포는 `not_measured`다.

## 계획 자체 점검 결과

- §5.1/I1: 작업 1의 동일·relative·normalized·symlink 양방향·hardlink 반례와 unrelated JSON 정상 갱신으로 대응한다.
- §5.1/I2: 작업 2의 IHDR CRC·filter·indexed PLTE, 작업 3의 JPEG SOS·WebP version으로 대응하며 작업 5가 완전한 decoder·시각 QA 주장을 차단한다.
- §5.1/I3: 작업 4의 양쪽 동시 오염과 route/trigger 독립 조건, 정상 generation/edit/hold/preview fixture 보존으로 대응한다.
- R5/§4.3: 작업 5의 standalone 복사본 링크 테스트와 두 언어 README 공개 URL로 대응한다. 설치 멱등성과 공유 문서는 통합 계획의 소유권이다.
- §6: 작업 1에서 최초 payload 변경과 함께 `2.0.2`와 실제 구현일의 dated heading을 맞추고 각 후속 변경은 같은 버전 이력에 기록한다. 날짜 제목에는 로컬 출시 준비와 미게시 상태를 명시한다. 공개/tag/push와 catalog 갱신은 없다.
- §7–8: 제품 RED/GREEN·독립 리뷰 → 컨트롤러 순차 커밋 → 공통 통합·portable·추출본 검사 순서다. 제품 범위 밖 파일을 stage하지 않는다.
- 기존 helper 이름과 `main`의 세 인자 호출, parser 반환값, evaluator API를 실제 코드와 대조했다. 새 helper는 이 계획에서 signature와 구현을 함께 정의했다.
- 설계와 충돌하여 사용자 결정을 다시 받아야 할 항목은 없다. 추적해야 할 의존성은 공통 문서 단언·release 검증 통합이며 이 계획에서 공유 코드를 임의 수정하지 않는다.
