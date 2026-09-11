# sddx 테스트

이 문서는 공급자 없는 계약, `resolve_backend.py` 픽스처 경계, Git sandbox 준비·정리를
소유합니다. 라이브 Cursor 또는 Grok 품질을 측정했다고 주장하지 않습니다.

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
증명합니다. 라이브 CLI, 과금, 모델 품질은 `not_measured`입니다.

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
