# sddx 계약

이 문서는 SDDx의 제품 정체, 오케스트레이터 호스트, implementer backend
해석을 소유합니다.

## 제품 정체

제품 ID, 스킬 `name`, 디렉터리 이름은 `sddx`입니다. 표시 이름은 `SDDx`입니다.
슬래시 호출은 Claude Code `/sddx`, Codex `$sddx`입니다.

지원 호스트는 `claude-code`와 `codex`뿐입니다. Cursor CLI와 Grok CLI는
구현 worker이지 호스트가 아닙니다. `cursor`와 `grok`을 `supported_hosts`에
넣지 않습니다.

Superpowers SDD는 worktree, ledger, task-brief, review-package, 리뷰어
프롬프트, fix loop, whole-branch review를 소유합니다. `sddx`는 인자 해석,
backend picker, `resolve_backend.py`, implementer argv, worker 제약만
소유합니다. SDD 본문을 이 스킬에 복사하지 않습니다.

## Backend 해석

컨트롤러는 로드된 스킬 루트에서 `scripts/resolve_backend.py`를 실행합니다.
네트워크를 쓰지 않고 worker를 띄우지 않습니다. 성공 시 stdout은 JSON 한
객체와 LF입니다. 없는 backend는 종료 코드 0과 `available: false`입니다.
잘못된 인자만 비0입니다. 종료 코드만으로 다른 backend를 고르지 않습니다.

Grok 후보는 PATH의 `grok`뿐입니다. `agent`는 Grok 후보가 아닙니다. Cursor
후보는 `cursor-agent`, 그다음 신원이 Cursor Agent CLI인 `cursor`입니다.
`agent`는 Cursor 후보가 아닙니다. Grok Build 신원을 Cursor로 채택하지
않습니다.

## 함께 고칠 파일

동작 변경을 한 파일에만 넣지 마세요.

- 호스트 또는 backend 정체: `products.toml`, 이 계약, 제품 README, 공개
  호환성 안내, `tests/products/sddx/`
- `resolve_backend.py` 신원·플래그 규칙: `skills/sddx/scripts/resolve_backend.py`,
  `tests/products/sddx/test_resolve_backend.py`
- 버전과 설치 파일: `skills/sddx/release.toml`, `SKILL.md`, `CHANGELOG.md`
