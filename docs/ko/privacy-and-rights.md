# 개인정보와 권리

[English](../en/privacy-and-rights.md) · [시작하기](getting-started.md) · [평가](evaluation.md)

이 프로젝트 자체는 텔레메트리 없음입니다. 필수 CI와 `python3 scripts/verify.py`는 자격 증명, 모델 호출, 원격 업로드를 하지 않습니다. 선택적 제3자 설치기 `npx skills add beyondwin/skills --skill korean-writing-editor`는 제3자이며 자체 정책을 따릅니다.

## 한국어 원문

`korean-writing-editor`는 사용자가 준 글을 픽스처, 로그, 말투 프로필로 저장하지 않습니다. 비공식 맞춤법 웹 서비스로 보내지 않고, 따로 요청하지 않으면 사실을 찾아오지 않습니다. 공개 픽스처는 재배포 가능한 합성 예시입니다. 개인 대화나 비공개 원고는 커밋하지 마세요.

## 이미지 참조와 동의

`image-workbench`에서 입력 이미지는 역할이 하나입니다: `edit_target`, `subject_reference`, `style_reference`, 또는 `compositing_input`. 참조 이미지는 사람, 상표, 보호된 작업을 복제할 권리를 주지 않습니다. 인물·상표·예시 이미지의 consent가 불명하면 보류합니다. 비공개 참조, 프롬프트, 생성 결과는 Git 픽스처로 저장하지 않습니다.

## hash, provenance, consent, 권리

다음 증거 유형은 서로 다릅니다. 하나만으로 ownership, consent, truth, 상업적 이용 허가(rights)를 증명하지 않습니다.

| 증거 | 의미 | 증명하지 않는 것 |
| --- | --- | --- |
| 저장소 코드와 Apache-2.0 | 이 스킬 코드의 라이선스 | 출력물 소유나 참조 이미지 권리 |
| 출력 hash (SHA-256) | 바이트 동일성 | 출처, 동의, 상업 허가 |
| source URL | 자료를 읽은 위치 | 재사용 권리 |
| C2PA 또는 기타 provenance 메타데이터 | 선언된 출처 주장 | 진실, 동의, 상업 허가 |

규범 출처와 pin은 각 스킬 `references/sources.md`에 있습니다. 외부 프로젝트의 license file은 그 코드 조건일 수 있으나 prompt·gallery·example image 권리를 자동으로 주지 않습니다.

취약점은 [SECURITY.md](../../SECURITY.md)의 비공개 보고 경로를 따릅니다.
