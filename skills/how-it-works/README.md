# How It Works

[English](README.en.md)

## 목적

한 기계가 어떻게 동작하는지 설명합니다. 설명 깊이는 넷 중 하나로 고릅니다.

- 그림: 한눈에 보는 전체 모습
- 길: 한 걸음씩 따라가는 흐름
- 뼈대: 내부 구조와 갈림길
- 허점: 어디서 깨지는지

쉬운 비유로 내용을 바꾸지 않고, 어린이 말투로 낮추지 않습니다.

## 사용할 때와 사용하지 않을 때

한 기계가 어떻게 도는지, 깊이를 골라 설명할 때 씁니다.

디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명, `/eli5` 대행에는 쓰지 않습니다.

## 지원 호스트

how-it-works: Codex and Claude Code supported for local or repository-based use.

지원 호스트 id는 `codex`, `claude-code`입니다. Grok와 Cursor는 이 빌드의 라이브 smoke가 통과하지 않아 지원하지 않습니다. Claude.ai, Cowork, Skills API 업로드, marketplace 게시는 지원하지 않습니다. 공유 한계는 [호환성](../../docs/users/ko/compatibility.md)을 따릅니다.

## 설치

가장 짧은 저장소 설치는 클론 후 링크 두 개입니다. 첫 링크는 Codex가 쓰고, 둘째는 Claude Code가 씁니다. `ln -s`는 이미 있는 대상을 덮어쓰지 않고 실패합니다.

```bash
git clone https://github.com/beyondwin/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.claude/skills
ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works
ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works
```

`$skill-installer`는 공개 GitHub 경로를 가리킵니다. Codex는 `~/.agents/skills/how-it-works`에서 발견합니다. `~/.codex` 복사본을 만들지 마세요. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/how-it-works
```

공유 설치·갱신·제거는 [설치](../../docs/users/ko/installation.md)를 따릅니다.

## 첫 호출

명시 호출은 Codex에서 `$how-it-works`, Claude Code에서 `/how-it-works`입니다.

```text
$how-it-works DNS 길
/how-it-works DNS 길
```

## 예상 결과

설명은 이 채팅 답에서 끝납니다. 호스트 페이지, Canvas, 브라우저, URL, 파일, mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 실패가 아닙니다.

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

이 저장소는 텔레메트리를 넣지 않습니다. 사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 가져온 URL만 보이며, 비공개 코퍼스가 아닙니다. 의료·법률·금융 슬라이스는 메커니즘만 설명하고 조언이 아닙니다.

자세한 경계는 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를 따릅니다.

## 검증

공급자 없는 검증은 `python3 scripts/verify.py --skill how-it-works`입니다. 오프라인 픽스처는 결정적 계약만 증명하며 라이브 호스트 품질을 증명하지 않습니다.

공유 증거 한계는 [검증](../../docs/users/ko/verification.md)을 따릅니다.

## 업데이트와 제거

갱신·제거 전에 정확한 설치 대상을 확인하세요. 경로가 이 스킬 이름과 일치하는지, 심볼릭 링크인지, `SKILL.md`의 `name`과 `metadata.version`이 기대한 값인지 확인하세요. 확인 없이 기존 설치를 바꾸지 마세요.

```bash
ls -ld ~/.agents/skills/how-it-works ~/.claude/skills/how-it-works
unlink ~/.agents/skills/how-it-works
unlink ~/.claude/skills/how-it-works
```

상위 `skills` 디렉터리나 홈 디렉터리를 지우지 마세요. 현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서 확인합니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/how-it-works/contract.md)
- [테스트](../../docs/maintainers/products/how-it-works/testing.md)
- [호환성](../../docs/maintainers/products/how-it-works/compatibility.md)
- [릴리스](../../docs/maintainers/products/how-it-works/release.md)
