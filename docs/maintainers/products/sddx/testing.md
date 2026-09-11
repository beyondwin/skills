# sddx 테스트

이 문서는 공급자 없는 계약과 `resolve_backend.py` 픽스처 경계를
소유합니다. 라이브 Cursor 또는 Grok 품질을 측정했다고 주장하지 않습니다.

픽스처 경로는 `tests/products/sddx/`입니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill sddx`입니다.
`tests/products/sddx/test_resolve_backend.py`는 PATH에 가짜 바이너리를
넣어 신원 규칙을 잠급니다. 실제 Cursor/Grok 계정을 쓰지 않습니다.

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
git diff --check
```

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지
않습니다. 오프라인 통과를 호스트 품질로 설명하지 마세요.
