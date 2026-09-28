# 안전과 개인정보

[English](../en/safety-and-privacy.md) · [설치](installation.md) · [검증](verification.md)

이 프로젝트는 텔레메트리를 넣지 않습니다. 사용 기록을 어디에도 보내지 않습니다. 필수 CI와 `python3 scripts/verify.py`는 자격 증명을 쓰지 않고, 모델을 부르지 않고, 아무것도 올리지 않습니다. 선택 설치기 `npx skills add beyondwin/skills --skill korean-writing-editor`는 제3자 도구이며 자체 정책을 따릅니다.

제품 안내: [`korean-writing-editor`](../../../skills/korean-writing-editor/README.ko.md), [`image-workbench`](../../../skills/image-workbench/README.ko.md), [`how-it-works`](../../../skills/how-it-works/README.ko.md), [`pre-sdd-review`](../../../skills/pre-sdd-review/README.ko.md), [`sddx`](../../../skills/sddx/README.ko.md), [`waygent`](../../../skills/waygent/README.ko.md).

## 한국어 원문

`korean-writing-editor`는 사용자의 글을 픽스처, 로그, 말투 프로필로 저장하지 않고, 비공식 맞춤법 서비스로 보내지 않습니다. 사실 확인은 요청할 때만 합니다. 공개 픽스처는 자유롭게 나눠도 되는 합성 예시입니다. 개인 대화나 비공개 원고는 커밋하지 마세요.

## 설명 주제

`how-it-works`는 Codex에서도 Claude Code에서도 사용자 주제를 픽스처나 로그로 저장하지 않습니다. 인용은 그 턴에서 볼 수 있는 URL이며, 비공개 자료 모음이 아닙니다. 의료·법률·금융 슬라이스(설명 범위)는 작동 방식만 설명하며 조언이 아닙니다.

## 이미지 참조와 동의

`image-workbench`에서 입력 이미지마다 역할은 하나입니다. `edit_target`, `subject_reference`, `style_reference`, `compositing_input` 중 하나입니다. 참조 이미지가 있다고 사람, 상표, 보호된 작업을 복제할 권리가 생기지 않습니다. 인물·상표·예시 이미지의 consent(동의)를 모르면 작업을 보류합니다. 비공개 참조, 프롬프트, 생성 결과는 Git 픽스처로 저장하지 마세요.

## SDD 전 문서 검토

`pre-sdd-review`는 로컬 설계, 구현 계획, 참조된 ADR, 저장소 파일을 읽습니다. 기본 모드에서는 확인된 설계, 계획, 공유 파일 원장만 수정합니다. 저장소 소유 테스트는 사용자 문서를 전송하거나 지속 저장하거나 픽스처로 수집하지 않습니다. 이 제품은 텔레메트리나 업로드 경로를 추가하지 않습니다. 라이브 처리와 보존은 Codex 호스트의 데이터 제어를 따릅니다. 명시적인 외부 요청 없이는 구현이나 SDD를 시작하지 않습니다.

선택 기록기 `evidence/evidence.py`는 따로 설치하지 않으며 Python 표준 라이브러리만 씁니다. run마다 record 하나를 `~/.pre-sdd-review/runs/`에 씁니다. 폴더를 바꾸려면 절대 경로로 `PRE_SDD_REVIEW_HOME`을 지정합니다. 명령은 [기록기 README](../../../skills/pre-sdd-review/evidence/README.md)를 보세요.

record에는 저장소 상대 경로, 디렉터리 이름, 해시, 열거값, 정수, 시각, 짧게 바꿔 쓴 요약(paraphrase)만 넣습니다. source 원문, 절대 경로, prompt, provider transcript, command output, credential, 환경 변수 값은 넣지 마세요. 짧게 제한된 note·consequence·fix에도 넣지 마세요. 기록기는 자동 비밀 탐지를 약속하지 않습니다.

기록은 선택이며 실행 기록(receipt) 오류는 의미 판정(semantic verdict)을 바꾸지 않습니다. schema 4 기록은 정규화한 Git 디렉터리와 checkout 루트에서 로컬 비공개 32-byte `.identity-salt`를 사용한 HMAC-SHA-256으로 `repo_key`를 만듭니다. 원시 절대 identity 경로와 salt는 출력하거나 기록하지 않습니다. 결속은 checkout·evidence home·salt에 속합니다. 별도 clone/worktree, checkout 경로 이동, 다른 evidence home, salt 유실은 새 run이 필요합니다. 표시 이름만으로 identity를 판단하지 않습니다. 6.0.0 전 기록기가 쓴 schema 2·3 기록은 읽지 않습니다. 모든 명령이 `schema-unsupported`로 거절하며, 그 기록의 checkout 결속은 추정하지 않습니다.

원자적 로컬 저장은 협력하는 client 사이의 일관성을 제공할 뿐, 악의적인 로컬 변조를 막는 서명된 audit log가 아닙니다.

`outcome` label(`good`, `false-ready`, `noisy`, `abandoned`)은 SDD나 구현이 끝난 뒤 사람이나 SDD 워커가 남기는 관찰이며, 다시 기록해 정정할 수 있습니다. label은 자기개선 evidence이고, 객관적 품질 판정이나 감사 등급 증거가 아닙니다. 로그를 읽는 것은 에이전트의 일입니다. `summary`가 돌려주는 JSON의 anomalies와 chains에 run_id가 붙어 있습니다.

## 외부 SDD 구현

`sddx`로 실제 구현을 돌리면 워커(Cursor Agent 또는 Grok Build)가 과제와
worktree 내용을 Cursor 또는 xAI에 보내며, 그 CLI의 데이터 정책을 따릅니다.
호스트는 자기 비밀 값을 워커 프롬프트에 넣지 않습니다. 기본 `verify.py`와
CI는 Cursor나 Grok CLI를 부르지 않습니다. 워커 대화, 자격 증명, 공급자 실행
기록(receipt)은 커밋하지 마세요.

## 과제별 서브에이전트 구현

`waygent`는 호스트(Claude Code, Codex, Cursor Agent 또는 Grok Build) 안에서 서브에이전트를
띄웁니다. 과제 내용과 저장소 파일은 그 호스트의 모델 공급자에게 가며, 그 호스트의
데이터 정책을 따릅니다. 진행 기록과 리뷰 기록은 저장소 최상위 `.waygent/`에 남고,
그 폴더의 `.gitignore`가 커밋되지 않게 막습니다. 기본 `verify.py`와 CI는 모델을
부르지 않습니다.

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
