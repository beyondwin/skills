# How It Works

[English](README.en.md)

## 목적

한 기계가 어떻게 동작하는지 설명합니다. 설명 깊이는 넷 중 하나로 고릅니다.

- 그림: 한눈에 보는 전체 모습
- 길: 한 걸음씩 따라가는 흐름
- 뼈대: 내부 구조와 갈림길
- 허점: 어디서 깨지는지

쉬운 비유로 내용을 바꾸지 않습니다. 어린이 말투로 낮추지 않습니다.

## 사용할 때와 사용하지 않을 때

한 기계가 어떻게 도는지, 깊이를 골라 설명할 때 씁니다.

디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명, `/eli5`
대행에는 쓰지 않습니다.

## 지원 호스트

how-it-works: Codex and Claude Code supported for local or repository-based use.

지원 호스트 id는 `codex`, `claude-code`입니다. Grok는 라이브 smoke에서 측정되었고 실패했습니다. Cursor는 실행하지 않아 지원을 주장하지 않습니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공유 한계는 [호환성](../../docs/users/ko/compatibility.md)을 보세요.

## 설치

저장소를 클론한 뒤 링크 두 개를 겁니다. 첫 링크는 Codex, 둘째는 Claude
Code입니다. `ln -s`는 이미 있는 대상을 덮어쓰지 않고 실패합니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works
ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works
```

`$skill-installer`는 공개 GitHub 경로를 가리킵니다. Codex는
`~/.agents/skills/how-it-works`에서 찾습니다. `~/.codex` 복사본을 만들지
마세요.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

나머지 설치 방법은 [설치](../../docs/users/ko/installation.md)를 보세요.

## 첫 호출

명시 호출은 Codex에서 `$how-it-works`, Claude Code에서 `/how-it-works`입니다.

```text
$how-it-works DNS 길
/how-it-works DNS 길
```

## 예상 결과

설명은 이 채팅 답에서 끝납니다. 호스트 페이지, Canvas, 브라우저, URL,
파일, mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 실패가 아닙니다.

필수 여섯 가지는 다음과 같습니다.

1. one-sentence claim
2. Mermaid
3. numbered hop list
4. rung-specific body
5. adjacent slices
6. one next move

골격:

````markdown
# {slice} · {그림|길|뼈대|허점}

## 한 줄 / One sentence

## 지도 / Map

```mermaid
{diagram source}
```

1. **H1** — {what moves or changes}

## 본문 / Body

## 지금 다루지 않은 것 / Adjacent slices

다음 / Next: {exactly one move}
````

## 안전과 개인정보

사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 가져온
URL만 보입니다. 비공개 코퍼스가 아닙니다. 의료·법률·금융 슬라이스는
메커니즘만 설명합니다. 조언이 아닙니다.

자세한 내용은 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를
보세요.

## 검증

모델 없는 검증은 `python3 scripts/verify.py --skill how-it-works`입니다.
오프라인 픽스처는 결정적 계약만 증명합니다. 라이브 호스트 품질을 증명하지
않습니다.

Optional live scoring is pass/fail from observable output in a fresh session.
Calls may use subscription/API quota. Do not use private or user prompts.
Do not commit full responses. Keep temporary files outside the repository
and delete them after scoring. A host that fails the same-build criteria is
unsupported.

공유 증거 한계는 [검증](../../docs/users/ko/verification.md)을 보세요.

## 업데이트와 제거

갱신하거나 지울 때는 설치 대상을 먼저 확인하세요.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

상위 `skills` 폴더나 홈 디렉터리는 지우지 마세요. 자세한 절차는
[설치](../../docs/users/ko/installation.md)를 보세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서
봅니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/how-it-works/contract.md)
- [테스트](../../docs/maintainers/products/how-it-works/testing.md)
- [호환성](../../docs/maintainers/products/how-it-works/compatibility.md)
- [릴리스](../../docs/maintainers/products/how-it-works/release.md)
