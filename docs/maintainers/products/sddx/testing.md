# sddx 테스트

이 문서는 공급자 없는 계약, `resolve_backend.py` 픽스처 경계, Git sandbox 준비·정리와
범위가 제한된 라이브 재검증을 소유합니다. 라이브 관측을 일반적인 provider 품질이나
다른 호스트의 실행 보장으로 확대하지 않습니다.

픽스처 경로는 `tests/products/sddx/`입니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`tests/products/sddx/test_resolve_backend.py`는 PATH에 가짜 바이너리를
넣어 신원 규칙을 잠급니다. 실제 Cursor/Grok 계정을 쓰지 않습니다.
`tests/products/sddx/test_prepare_grok_sandbox.py`는 임시 저장소와 실제 linked
worktree를 만들고 Git 경로 계산, 기존 TOML 원문 복원, 재진입, 심볼릭 링크 거절,
CLI 성공·실패 출력을 검사합니다. 표준 `tomllib`를 사용하므로 Python 3.11 이상이
필요합니다.

생성되는 `sddx-worktree` 프로파일의 `read_write`는 linked worktree의 Git 디렉터리와
공용 `.git` 디렉터리를 허용합니다. 따라서 공용 `.git` 안에 있는 다른 브랜치 ref에도
쓰기 권한이 생깁니다. 이 검사는 정상적인 단일 컨트롤러 실행에서 기존 파일 변경을
보존하는지 확인하며, 악성 동시 변경에 대한 보안 경계나 Grok sandbox의 실제 실행
성공을 입증하지 않습니다.

결정적 검사:

- Grok 후보는 PATH의 `grok`뿐이다. `agent`만 있으면 `not_found`다.
- `agent`는 Cursor로 채택되지 않는다.
- Grok 신원의 `cursor-agent` 또는 `cursor`는 `identity_mismatch`다.
- Cursor는 headless print, force/yolo, trust, workspace/cwd, model, resume이
  필요하고 Grok 모델 id가 없으면 `no_grok_model`이다.
- Grok help에 `--cwd`가 없으면 `missing_flags`다.
- argv에 `--worktree`와 `--plugin-dir`가 없다. Grok 고정 플래그에
  `--disable-web-search`가 있다.

페이로드 계약 통과는 파일 정체성, 이식 가능한 frontmatter, 금지 문자열만
증명합니다. 이 공급자 없는 증거만으로 라이브 CLI, 과금, 모델 품질을
측정했다고 할 수 없습니다.

## 행동 probe

[행동 probe](../../../../tests/products/sddx/behavior-probes.md)는 이전 응답을 주지 않은
독립 문맥에서 native 모델이 제안한 행동을 컨트롤러가 수동 판정합니다. 2026-09-11
controller 시나리오 5개는 완료 판정, sandbox 실패, session 재사용·전환 기준을 모두
통과했습니다. 별도의 worker 역할 합성 표본에서는 external skill 읽기 제안이 baseline
2/5에서 candidate worker 안내 적용 후 0/5로 줄었습니다. 다섯 guided 응답은
`candidate-worker.md`를 읽었고, 최종 역할 문장과 내용은 같지만 기존 문단의 순서와
서식은 달랐습니다. 이 결과는 문자열 검사가 아니며, 작은 native simulation을 실제
Grok 호출이나 runtime 신뢰도 통계로 취급하지 않습니다.

## 2026-09-11 실제 Grok 재검증

측정 환경은 macOS 26.5.2, Python 3.14.7, Codex controller, Grok 1.0.25,
`grok-4.6` High였습니다. 새 remote 없는 로컬 저장소의 linked worktree에서 다음
절차를 수행했습니다.

1. 수정된 제품에서 resolver와 sandbox helper를 확인하고, 각 호출 전 `prepare`,
   worker 종료 후 `cleanup`을 실행합니다.
2. 첫 task에서 Unicode 공백 정규화 구현과 테스트를 worker가 직접 커밋하게 합니다.
3. 같은 worker session에 TypeError 메시지와 동등성 테스트를 추가하라는 통제된
   요구를 보내고, 수정 커밋 뒤 native scoped review를 반복합니다.
4. 새 session으로 CLI task를 실행하고 worker의 세 번째 직접 커밋을 확인합니다.
5. fixture에서 `python3 -m unittest discover -s tests -v`, 기준과 결과 commit을
   인자로 준 `git diff --check`, `git status --short`, 변경 파일 목록과 최근 commit을
   확인합니다.

실제 provider 호출은 세 번이었고 모두 worker exit 0, cleanup exit 0, report `DONE`,
worker 직접 커밋으로 끝났습니다. 첫 task는 구현 전 `textnorm` 부재로 loader-error
test 1개를 실행한 RED exit 1 뒤 GREEN 7 tests exit 0, 통제된 same-session 수정은
RED 8 tests exit 1 뒤 GREEN 8 tests exit 0이었고, 둘째 task는 RED 14 tests
exit 1 뒤 GREEN 14 tests exit 0이었습니다. 둘째 task의
RED/GREEN은 shell wrapper exit 0 안의 실제 test exit를 별도로 확인했습니다. 원래
구현 결함은 발견되지 않았으며, same-session 변경은 미리 승인된 추가 요구의 resume
동작을 검증한 것입니다.

최종 독립 unittest는 14 tests, exit 0이었고 전체 commit 범위의
`git diff --check`도 exit 0이었습니다. worktree는 clean이었으며 세 worker commit에는
요구된 애플리케이션·테스트·README 파일 다섯 개만 포함됐습니다. 컨트롤러가 구현을
수정하거나 커밋을 보조하지 않았습니다. 생성 sandbox 설정과 복원 기록은 정리됐고,
기존 설정 byte 보존은 라이브 fixture가 아니라 공급자 없는 검사에서 입증했습니다.

실제 tool trace의 수동 검토에서는 brief-first 순서를 확인했고 external skill·전체 계획
읽기, nested agent, MCP tool 호출이나 역할 위반은 관측되지 않았습니다. 기존 host
integration의 MCP 초기화·handshake·자동 재시작 경고는 계속 나타났습니다. 이 경고는
모델의 MCP tool 호출과 다르며, 경고가 사라진다고 보장하지 않습니다.

독립 whole-fixture native review는 clean checkout, 생성 설정·journal 부재, worker가
소유한 commit 범위, same-session 수정과 새 task session, 독립 14-test 로그를 다시
확인하고 Critical/Important/Minor 0건으로 accept했습니다.

제품 구현 HEAD에서 `python3 scripts/verify.py`는 868 unittest를 포함한 전체
공급자 없는 검사를 완료해 exit 0이었습니다. 이후 변경은 문서뿐이므로 전체 suite를
반복하지 않고 내용·링크·diff를 검사합니다. Cursor worker와 Claude Code host 실행은
`not_measured`입니다.

## 명령

```bash
python3 scripts/verify.py --skill sddx
python3 scripts/verify.py
python3 -m unittest tests.products.sddx.test_resolve_backend
python3 -m unittest discover -s tests/products/sddx -p test_prepare_grok_sandbox.py -v
git diff --check
```

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 오프라인 통과를 호스트 품질로 설명하지 마세요.
