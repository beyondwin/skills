# macOS 전용 지원과 품질 우선 속도

이 문서는 승인된 제품 결정이다. 현재 계약을 정의하지 않는다. 구현은 별도
계획이 이 파일을 `**Spec:**`으로 가리킬 때만 시작한다.

## 목적

다섯 스킬의 지원 OS를 macOS로 고정하고, Windows CI·Win32 특수경로가 만드는
유지 비용을 없앤 뒤, 그 순환을 스킬 결과 품질과 실행 루프 회귀에 다시 넣는다.
품질 바닥은 둘이다. 측정하지 않은 지원을 주장하지 않고, 스킬이 내는
글·그림·SDD·리뷰가 지금보다 나빠지지 않게 한다. 속도는 이 두 바닥을 지킨
뒤에만 취한다.

빨라야 하는 대상은 둘이다. 스킬을 고치고 합치는 속도, 그리고 스킬로 실제
작업을 하는 속도.

## 승인된 결정

- 저장소 전체에 적용한다. 다섯 스킬, CI, 공개 문서.
- 스킬 지원 OS는 macOS뿐이다. Windows와 Linux는 지원하지 않는다.
  `not_measured` 대기열로 두지 않는다.
- CI 러너 OS는 지원 증거가 아니다. Ubuntu에서 `full`을 돌려도 Linux 지원이
  아니고 macOS 지원 증거도 아니다. `macos-latest`를 추가하지 않는다.
- `windows-latest` 행과 `windows-portable` 프로필을 제거한다.
- Win32 전송 코드(`.cmd` 언랩, CRT 따옴표, `cmd.exe` 퍼센트 검사)를 제거한다.
- `products.toml`에 `supported_os` 필드를 넣지 않는다. OS 선언의 원본은 공개
  호환성 문장과 각 제품 `compatibility.md`다.
- 한영 사용자 문서는 유지한다. 카탈로그 `catalog/`는 건드리지 않는다.
- 이 변경에서 스킬 프롬프트·리뷰 루프·새 eval 하네스를 다시 쓰지 않는다.
- 구현 기준 브랜치는 `main`이다. Windows 지원을 위해
  `fix/sddx-windows-cmd-shim-unwrap`을 머지하지 않는다. 그 브랜치의 파일이
  작업 트리에 있으면 Win32 헬퍼는 같은 삭제 대상이다.

## 역할 분리

| 층 | 역할 | 지원 주장에 쓰는가 |
| --- | --- | --- |
| 스킬 사용 | macOS에서 측정된 호스트만 | 예 |
| 로컬 필수 검증 | 기여자 macOS에서 `python3 scripts/verify.py` | 저장소 계약만. 라이브 품질 아님 |
| CI | Ubuntu `full` | 아니오. POSIX 회귀 문 |
| 라이브 실행 | 명시적, 로컬, macOS, 비용 가능 | 해당 제품 호스트·동작의 측정만 |

Linux에서 테스트가 우연히 통과해도 제품을 Linux 지원으로 올리지 않는다.
Ubuntu CI를 없애지 않는다. 싼 POSIX 문이다.

## 자르는 것

- `scripts/lib/change_routing.py`의 `OS_ROWS`에서 `windows-latest` /
  `windows-portable` 쌍.
- `scripts/lib/verification.py`의 `windows-portable` 프로필,
  `WINDOWS_EXCLUDED_STAGES`, 그 프로필만 위한 단계 필터.
- `python3 scripts/verify.py --profile windows-portable`. 알 수 없는 프로필은
  지금처럼 실패한다. 별칭으로 `full`에 매지 않는다.
- SDDx `skills/sddx/scripts/resolve_backend.py`의 Win32 전송 묶음 전부:
  `_UNTRANSPORTABLE`, `_PERCENT_NAME`, `_expandable_percent_name`,
  `_quote_for_cmd`, `_is_cmd_wrapper`, `_unwrap_cmd_wrapper`(있으면),
  `_windows_command_line`, `_uses_cmd_exe`, `_command`의 nt/cmd 분기,
  `os.name == "nt"`일 때 문자열 command line을 만드는 `_subprocess_args`
  분기. 남은 `_command`는 두지 않는다. `_subprocess_args`만 리스트를 반환한다.
- 그 경로만 잠그는 테스트: `tests/products/sddx/test_resolve_backend.py`의
  Windows 전송 검사, `tests/products/sddx/test_run_worker.py`의 `.cmd` 픽스처
  왕복, `skipUnless(os.name == "nt")` 검사.
- 공개·관리자 문서의 `windows-portable` 사용법과 “native Windows 측정 없음”을
  미지원 선언으로 바꾸는 문장. 아래 고정 문구를 쓴다.

남기는 것: Ubuntu `full` CI, 제품별 `--skill` 라우팅, 한영 문서, 카탈로그,
기존 오프라인 계약 검사, 라이브 실행은 런타임이 바뀔 때만 macOS에서 하는
규칙, SDDx의 세션 ID·타임아웃·MCP 도구 필터.

## Windows 실행 거절

Linux 런타임은 거절하지 않는다. CI가 Ubuntu이기 때문이다.

Windows에서는 SDDx 제품 CLI만 거절한다. 메시지와 종료는 기존 `BLOCKED:` /
exit 2 계약을 따른다. 시도 디렉터리를 만들기 전에 거절한다.

대상과 문장:

| CLI | 거절 위치 | stderr | exit |
| --- | --- | --- | --- |
| `skills/sddx/scripts/run_worker.py` | `main()`, `run`과 `status` 모두 | `BLOCKED: Windows is not a supported OS` | 2 |
| `skills/sddx/scripts/resolve_backend.py` | `main()`만. `resolve()`는 거절하지 않는다 | 동일 | 2 |
| `skills/sddx/scripts/prepare_grok_sandbox.py` | Python 3.11 검사 다음, 서브커맨드 전 | 동일 | 2 |

`os.name == "nt"`일 때만 거절한다. 단위 검사는 POSIX에서 `os.name`을 `"nt"`로
패치한다. 실제 Win32 이미지를 만들지 않는다.

다른 제품 Python CLI(`inspect_asset.py`, `evidence.py`, `verify.py`)에는 OS
거절을 넣지 않는다. 마크다운 스킬은 런타임 가드가 없다.

## 고정 공개 문장

한영이 같은 사실을 말한다. 테스트는 이 문장 또는 아래 영어 짝을 핀한다.

한국어 호환성:

> 지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI는 Ubuntu에서 `full` 프로필을 돌릴 수 있습니다. 그 통과는 Linux 지원이 아니고 macOS 지원 증거도 아닙니다.

영어 호환성:

> The supported OS is macOS only. Windows and Linux are unsupported. CI may run the `full` profile on Ubuntu. That pass is not Linux support and is not macOS support evidence.

한국어 검증, `windows-portable` 프로필 설명과 예제 명령을 지운 자리:

> `full`이 유일한 프로필입니다. CI는 Ubuntu에서 `full`을 실행할 수 있으며, 그 통과는 macOS 지원 증거가 아닙니다.

영어 검증:

> `full` is the only profile. CI may run `full` on Ubuntu; that pass is not macOS support evidence.

`docs/users/ko/verification.md`와 `docs/users/en/verification.md`의
pre-sdd 공유 절에 있던 Windows 문장은 아래로 교체한다. digest를 같은 변경에서
재계산한다.

한국어:

> Ubuntu CI의 `full` 통과는 native macOS 지원을 증명하지 않습니다.

영어:

> An Ubuntu `full` CI pass does not prove native macOS support.

호스트 지원 문장(`korean-writing-editor: Codex supported` 등)은 바꾸지 않는다.
OS와 호스트는 겹치지 않는다. `how-it-works`의 `historical-unbound` /
`current-bounded` 설명 문장은 유지하고, 그 문단의 Windows 한 문장만 위 고정
문장으로 바꾼다.

## 제품 문서

각 제품 `compatibility.md`에 지원 OS macOS, Windows/Linux 미지원, Ubuntu CI는
증거가 아님을 적는다. `not_measured` Windows 행은 미지원으로 바꾼다.

SDDx `SKILL.md`의 `Do not replace Windows support with POSIX-only code`는
다음으로 바꾼다.

> The supported OS is macOS. Do not add Windows transport. Refuse Windows at the product CLIs.

SDDx README의 npm `.cmd` 전달 설명은 지원 OS와 Windows 거절로 바꾼다.
측정 표의 “Windows 합성 argv 전송 `measured`”와 “실제 Windows Cursor/Grok CLI
`not_measured`” 행은 제거한다. Windows는 미지원이다.

pre-sdd-review CLI matrix의 Windows `not_measured`는 미지원으로 바꾼다.
Linux 행은 제품 미지원으로 바꾸되, 기록기 테스트가 Ubuntu에서 도는 사실과
모순되지 않게 “CI POSIX 검사 ≠ Linux 제품 지원”을 한 줄로 적는다.

## 재투자 (이 변경 안과 다음)

이 변경에 넣는 재투자:

1. `AGENTS.md`와 `CONTRIBUTING.md`에 내부 루프를 적는다. 제품 파일만 고치면
   `python3 scripts/verify.py --skill <name>`. 머지 전에는
   `python3 scripts/verify.py`. 라이브 `--execute`는 그 제품 런타임·실행
   계약이 바뀐 뒤에만, macOS에서, 명시적으로.
2. 라이브 증거 문턱을 낮추지 않는다. 오프라인 통과를 라이브 품질로 쓰지
   않는 기존 규칙을 유지한다.
3. 새 eval 하네스, 자동 재시도, 리뷰어 생략을 추가하지 않는다.

이 변경 밖, 이후 제품 수정에 쓰는 재투자:

- Windows 이식에 쓰던 순환을 그 제품의 결과 품질 검사에 쓴다.
- 실행 경로를 만질 때만 해당 제품의 기존 오프라인·계약 검사를 보강하고,
  필요할 때만 macOS 라이브를 다시 잰다.
- SDDx 프롬프트·리뷰 품질은 별도 설계가 있을 때만 바꾼다.

## 검사와 실패

필수 로컬 검증은 `python3 scripts/verify.py`다. CI는
`python scripts/verify.py --profile full`과 기존 selector만 쓴다.
`--profile windows-portable`는 실패해야 한다.

문서 테스트는 `windows-portable` 제외 문장 헬퍼를 제거하고, 위 고정 문장을
핀한다. `PRE_SDD_SHARED_SECTION_DIGESTS`의 verification digest는 문장 교체와
같은 커밋에서 맞춘다.

SDDx 거절 검사는 패치된 `os.name == "nt"`에서 CLI `main`만 호출한다.
`resolve()`를 거절하면 안 된다. POSIX `run` 경로가 리스트 argv를 유지하는지
기존 검사가 계속 통과해야 한다.

잘못된 구현이 통과하면 안 되는 예:

- Windows 행만 지우고 `windows-portable` 프로필을 남겨 문서와 CI가 어긋남.
- 프로필을 지우면서 공개 문서에 `--profile windows-portable`이 남음.
- Win32 헬퍼를 남긴 채 테스트만 skip.
- `resolve()`까지 Windows에서 거절해 단위 테스트가 POSIX에서 패치만으로
  전부 실패.
- Ubuntu 통과를 macOS 지원이라고 쓰는 문장.

## 범위 밖

- `macos-latest` CI 추가
- `products.toml` 스키마 변경
- `catalog/` 고정 묶음 재작성
- Linux CLI 거절
- 스킬 프롬프트·how-it-works 슬라이스·한국어 편집기 모드 재작성
- 한영 문서 쌍 제거
- 라이브 모델 호출을 이 변경의 통과 조건으로 넣기

## 작업 순서

1. CI 행렬과 `windows-portable` 프로필 제거. 라우팅·verify 테스트가 초록.
2. 공개 문서 고정 문장과 digest. 저장소 문서 테스트가 초록.
3. 제품 compatibility / README / SKILL / 내부 루프 문서.
4. SDDx Win32 삭제와 Windows CLI 거절. `python3 scripts/verify.py --skill sddx`
   그리고 전체 `python3 scripts/verify.py`.

슬라이스 1이 끝나면 Windows CI가 더 이상 필수 문이 아니다. 그 전에 Windows
전송을 더 고치지 않는다.

## 버전

SDDx는 이미 대상 `2.0.0` 파괴 구간이다. Windows 거절과 전송 삭제는 그 구간에
넣는다. 다른 제품은 OS 선언·문서·CI만 바뀌면 런타임 동작이 아니므로 각
`release.md`의 SemVer 표로 patch 문서를 따른다. 제품 CLI에 OS 거절을 넣는
것은 SDDx뿐이다.

## 성공 기준

- 공개 문서가 macOS만 지원하고 Windows/Linux를 미지원으로 말한다.
- CI include에 `windows-latest`가 없다. `PROFILES`는 `("full",)`뿐이다.
- SDDx 소스에 `_quote_for_cmd`, `_unwrap_cmd_wrapper`, `_windows_command_line`,
  `_expandable_percent_name`, `_PERCENT_NAME`, `_UNTRANSPORTABLE`,
  `_is_cmd_wrapper`, `_uses_cmd_exe`가 없다.
- Windows로 패치한 SDDx CLI `main`이 시도 디렉터리 없이 exit 2와 고정
  `BLOCKED:` 문장을 낸다.
- `python3 scripts/verify.py`가 macOS 로컬에서 통과한다. 라이브 호출은 이
  기준에 넣지 않는다.
- 기존 제품 오프라인 계약 검사의 의미가 약해지지 않는다.
