# image-workbench 호환성

지금은 레지스트리의 `codex`와 `grok`에서 지원합니다. 다른 프로그램에 비슷한
그림 도구가 있어도 이 제품이 그 프로그램을 지원한다는 뜻은 아닙니다.

## 지원 OS

지원 OS는 macOS뿐입니다. Windows와 Linux는 지원하지 않습니다. CI는 Ubuntu에서
전체 검증을 돌릴 수 있습니다. 그 통과는 Linux 지원이 아니고 macOS 지원
증거도 아닙니다.

## 필요한 호스트 능력

- 로컬 스킬 폴더에 설치되어 `SKILL.md`를 읽을 수 있어야 합니다.
- `brief`와 `audit`은 읽기만 하면 됩니다.
- `generate`와 `edit`는 지금 쓰는 프로그램(호스트)의 그림 도구와, 결과를 열어
  보는 기능이 필요합니다. Codex는 기본 제공 그림 도구, Grok는
  `image_gen`/`image_edit`입니다. 둘 중 하나라도 없으면 만들거나 고친다고
  말하지 마세요.

## 공급자 호출 없는 증거

필수 증거는 `python3 scripts/verify.py --skill image-workbench`입니다.
오프라인 예시(픽스처)는 라우팅, 권한, ImageSpec, 핸드오프, 파일
확인기(inspector) 계약만 증명합니다. 실제 그림 품질, 상업적 사용 허가, 다른
공급자보다 낫다는 것은 증명하지 않습니다.

## 실제 호출 증거의 경계

실제 이미지 호출은 로컬에서, 명시적으로, 선택적으로만 합니다. 비용이 들 수
있고 CI는 요구하지 않습니다. 오프라인 통과를 실제 그림 결과로 바꿔 말하지
마세요. 사용자 이미지, 비공개 참조, 생성 매체, 자격 증명, 공급자 receipt는
커밋하지 않습니다.

Grok 4항목 기본 동작 확인(smoke) 기록은
`tests/products/image-workbench/live/smoke-record.json`에 있습니다. 절차는
[테스트](testing.md)와 `tests/products/image-workbench/live/README.md`를
따릅니다.

## 새 호스트 지원

새 프로그램을 지원한다고 쓰려면 같은 빌드에서 아래 네 가지를 실제로 돌려
통과해야 합니다.

1. 스킬을 찾는다.
2. `$image-workbench` 또는 `/image-workbench`로 부를 수 있다.
3. 프로젝트 이미지를 달라고 하면 켜지고, `kws-image-workbench`는 켜지지 않는다.
4. brief/audit은 파일을 만들지 않고, 승인된 generate/edit는 프로젝트 파일로
   저장된다.

기록이 없으면 그 프로그램은 지원 대상이 아닙니다. 사용자용 공통 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
