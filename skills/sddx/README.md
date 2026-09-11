# SDDx

[English](README.en.md)

## 목적

Superpowers SDD를 현재 Claude Code 또는 Codex 세션이 오케스트레이터로
돌리고, 구현만 Cursor CLI 또는 Grok Build CLI에 넘깁니다.

## 사용할 때와 사용하지 않을 때

구현 계획이 있고 외부 Grok/Cursor implementer로 SDD를 실행할 때 씁니다.

설계·계획 작성, `pre-sdd-review`, 네이티브 서브에이전트 구현에는 쓰지
않습니다.

## 지원 호스트

sddx: Claude Code and Codex supported for local or repository-based use.

지원 호스트 id는 `claude-code`, `codex`입니다. Cursor와 Grok CLI는
구현 worker이지 호스트가 아닙니다. 지금 설치 파일의 실제 실행은
`not_measured`입니다. Claude.ai, Cowork, Skills API 업로드, marketplace
게시는 지원하지 않습니다. 공유 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)을
보세요.

## 설치

저장소를 클론한 뒤 링크 두 개를 겁니다. 첫 링크는 Codex, 둘째는 Claude
Code입니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
```

`$skill-installer`는 공개 GitHub 경로를 가리킵니다. Codex는
`~/.agents/skills/sddx`에서 찾습니다. `install-codex.md`의 세 Codex 전용
명령에는 넣지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/sddx
```

나머지 설치 방법은
[설치](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)를
보세요.

## 첫 호출

명시 호출은 Codex에서 `$sddx`, Claude Code에서 `/sddx`입니다.

```text
$sddx docs/history/plans/example.md
/sddx docs/history/plans/example.md
```

## 예상 결과

argv가 있으면 그 backend로 진행하고, 없으면 이 계획에서 한 번만
backend를 고릅니다. 그다음 Superpowers SDD를 외부 implementer와 네이티브
리뷰어로 실행합니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [CHANGELOG](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/sddx/release.md)
