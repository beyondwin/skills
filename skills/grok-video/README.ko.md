# Grok Video

동영상 생성, 스틸 애니메이션, 클립 연장 요청이면 이 스킬이 켜집니다. `$grok-video`로도 시작합니다.

[English](README.md)

## 목적

Grok Video는 클립 하나를 만듭니다. 주제, 변화, 대사, 인물 사진이 빠졌을 때만 묻습니다. 길이, 해상도, 화면비, 고정 카메라는 채웁니다. 스틸에 고정해서 장면이 다른 샷으로 바뀌지 않게 합니다.

## 사용할 때와 사용하지 않을 때

Grok 동영상이 필요할 때 씁니다.

정지 이미지, 스프라이트 시트, 도표, 파일을 손으로 자르는 작업에는 쓰지 않습니다. 정지 이미지는 image-workbench가 맡습니다.

## 지원 호스트

grok-video: Grok supported; a clip needs the host reference_to_video tool and a way to open the result.

호스트 id는 `grok`입니다. Codex, Claude Code, Cursor는 지원하지 않습니다.

Claude.ai, Cowork, Skills API 업로드, 마켓플레이스 게시는 지원하지 않습니다.
공통 한계는
[호환성](https://github.com/beyondwin/skills/blob/main/docs/users/ko/compatibility.md)에 있습니다.

## 설치

Grok은 로컬 링크를 읽습니다. 공개 경로: https://github.com/beyondwin/skills/tree/main/skills/grok-video. 절차는
[로컬 링크](https://github.com/beyondwin/skills/blob/main/docs/users/ko/install-local.md)에 있습니다.

Codex 설치 명령으로 폴더를 받을 수는 있지만, 실행은 Grok에서만 합니다.

```text
$skill-installer https://github.com/beyondwin/skills/tree/main/skills/grok-video
```

## 첫 호출

평범한 말로 클립을 요청합니다.

```text
노란 머그가 나무 탁자 왼쪽에서 오른쪽으로 움직인다.
```

## 예상 결과

다른 길이나 초안을 말하지 않으면 6초, 720p 영상 하나입니다. 답에는 파일과, 주제가 처음 장면과 맞는지가 있습니다.

## 더 보기

- [안전과 개인정보](https://github.com/beyondwin/skills/blob/main/docs/users/ko/safety-and-privacy.md)
- [검증](https://github.com/beyondwin/skills/blob/main/docs/users/ko/verification.md)
- [변경 이력](CHANGELOG.md)
- [계약](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/contract.md)
- [테스트](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/testing.md)
- [호환성](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/compatibility.md)
- [릴리스](https://github.com/beyondwin/skills/blob/main/docs/maintainers/products/grok-video/release.md)
