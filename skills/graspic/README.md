# graspic

[English](README.en.md)

## 이 스킬이 해결하는 문제

한 기계가 어떻게 동작하는지 설명합니다. 설명 깊이는 넷 중 하나로 고릅니다.

- 그림: 한눈에 보는 전체 모습
- 길: 한 걸음씩 따라가는 흐름
- 뼈대: 내부 구조와 갈림길
- 허점: 어디서 깨지는지

쉬운 비유로 내용을 바꾸지 않고, 어린이 말투로 낮추지 않습니다.

## 사용해야 할 때와 사용하지 말아야 할 때

한 기계가 어떻게 도는지, 깊이를 골라 설명할 때 씁니다.

디버깅, 구현, 리뷰, 번역, 한 줄 사실 조회, 어린이 말투 설명, `/eli5` 대행에는 쓰지 않습니다.

## 1분 설치와 첫 호출

기본 경로는 Codex `$skill-installer`와 공개 GitHub 스킬 경로입니다. 대상 디렉터리가 이미 있으면 설치기는 중단하며, 기존 설치를 자동으로 바꾸지 않습니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic
```

설치 후 다음 턴에서 명시 호출합니다.

```text
$graspic DNS 길
```

공유 설치·갱신·제거는 [설치](../../docs/users/ko/installation.md)를 따릅니다.

## 주요 흐름

설명하기 전에 주제를 정하고, 그림·길·뼈대·허점 중 깊이를 고르고, 언어를 정합니다. 결과는 채팅이 아니라 브라우저에서 여는 페이지입니다. 그림은 mermaid로 그립니다. 터미널 창에만 설명을 남기지 않습니다.

## 안전과 개인정보

이 저장소는 텔레메트리를 넣지 않습니다. 사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 가져온 URL만 보이며, 비공개 코퍼스가 아닙니다. 의료·법률·금융 슬라이스는 메커니즘만 설명하고 조언이 아닙니다.

자세한 경계는 [안전과 개인정보](../../docs/users/ko/safety-and-privacy.md)를 따릅니다.

## 호환성과 검증 수준

graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.

공유 지원 문장과 호스트 한계는 [호환성](../../docs/users/ko/compatibility.md)을 따릅니다. 증거 한계는 [검증](../../docs/users/ko/verification.md)을 따릅니다.

## 갱신과 버전 확인

갱신 전에 설치 대상을 확인하세요. 경로가 이 스킬 이름과 일치하는지, 실제 디렉터리인지, `SKILL.md`의 `name`과 `metadata.version`이 기대한 값인지 확인하세요. 확인 없이 기존 설치를 바꾸지 마세요.

현재 버전은 `SKILL.md`의 `metadata.version`과 [CHANGELOG](CHANGELOG.md)에서 확인합니다.

## 변경 이력과 관리자 문서

- [CHANGELOG](CHANGELOG.md)
- [계약](../../docs/maintainers/products/graspic/contract.md)
- [테스트](../../docs/maintainers/products/graspic/testing.md)
- [릴리스](../../docs/maintainers/products/graspic/release.md)
