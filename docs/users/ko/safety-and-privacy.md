# 안전과 개인정보

[English](../en/safety-and-privacy.md) · [설치](installation.md) · [검증](verification.md)

이 프로젝트는 텔레메트리를 넣지 않습니다. 사용 기록을 어디에도 보내지 않습니다. 필수 CI와 `python3 scripts/verify.py`는 자격 증명을 쓰지 않고, 모델을 부르지 않고, 아무것도 올리지 않습니다. 선택 설치기 `npx skills add beyondwin/skills --skill korean-writing-editor`는 제3자 도구이며 자체 정책을 따릅니다.

제품 안내: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md), [`image-workbench`](../../../skills/image-workbench/README.ko.md), [`how-it-works`](../../../skills/how-it-works/README.ko.md).

## 한국어 원문

`korean-writing-editor`는 사용자의 글을 픽스처, 로그, 말투 프로필로 저장하지 않고, 비공식 맞춤법 서비스로 보내지 않습니다. 사실 확인은 요청할 때만 합니다. 공개 픽스처는 자유롭게 나눠도 되는 합성 예시입니다. 개인 대화나 비공개 원고는 커밋하지 마세요.

## 설명 주제

`how-it-works`는 Codex에서도 Claude Code에서도 사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 볼 수 있는 URL이며, 비공개 자료 모음이 아닙니다. 의료·법률·금융 슬라이스(설명 범위)는 작동 방식만 설명하며 조언이 아닙니다.

## 이미지 참조와 동의

`image-workbench`에서 입력 이미지마다 역할은 하나입니다. `edit_target`, `subject_reference`, `style_reference`, `compositing_input` 중 하나입니다. 참조 이미지가 있다고 사람, 상표, 보호된 작업을 복제할 권리가 생기지 않습니다. 인물·상표·예시 이미지의 consent(동의)를 모르면 작업을 보류합니다. 비공개 참조, 프롬프트, 생성 결과는 Git 픽스처로 저장하지 마세요.

## 이해관계가 큰 요청

법률·의료·금융처럼 이해관계가 큰 한국어 글은 기계적 `correct` 또는 `diagnose`가 기본입니다. `how-it-works`의 해당 슬라이스는 작동 방식만 설명합니다. `image-workbench`는 권리나 개인정보를 모르면 보류합니다.

## hash, provenance, consent, 권리

hash는 바이트가 같은지, provenance는 어디서 왔다고 적혀 있는지, consent는 사람의 동의가 있는지, rights는 다시 써도 되는지를 말합니다. 서로 다른 것이며, 어느 하나만으로 소유, consent, 사실, 상업 이용 권리(rights)를 증명하지 않습니다.

| 증거 | 의미 | 증명하지 않는 것 |
| --- | --- | --- |
| 저장소 코드와 Apache-2.0 | 이 스킬 코드의 라이선스 | 출력물 소유나 참조 이미지 권리 |
| 출력 hash (SHA-256) | 바이트 동일성 | 출처, 동의, 상업 허가 |
| source URL | 자료를 읽은 위치 | 재사용 권리 |
| C2PA 또는 기타 provenance 메타데이터 | 선언된 출처 주장 | 진실, 동의, 상업 허가 |

출처 위치와 pin은 각 스킬의 `references/sources.md`에 있습니다. 외부 프로젝트의 라이선스는 그 코드에만 적용되며, prompt·gallery·example image에 대한 권리를 주지 않습니다.

취약점은 [SECURITY.md](../../../SECURITY.md)의 비공개 보고 경로로 알려 주세요.
