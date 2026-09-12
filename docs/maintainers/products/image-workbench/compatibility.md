# image-workbench 호환성

지금은 레지스트리의 `codex`와 `grok`에서 지원합니다. Grok에서 만들거나
고치려면 `image_gen`/`image_edit`와 결과를 열어 보는 기능이 필요합니다.
다른 프로그램에 비슷한 그림 도구가 있어도 이 제품이 그 프로그램을 지원한다는
뜻은 아닙니다.

## 필요한 호스트 능력

- 로컬 스킬 폴더에 설치되어 `SKILL.md`를 읽을 수 있을 것
- `brief`와 `audit`은 읽기만 해도 됩니다
- `generate`와 `edit`는 지금 쓰는 프로그램의 그림 도구와, 결과를 여는 기능이
  필요합니다. Codex는 딸려 있는 그림 도구, Grok는 `image_gen`/`image_edit`입니다.
  없으면 만들거나 고친다고 말하지 마세요

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill image-workbench`입니다.
오프라인 픽스처는 라우팅, 권한, ImageSpec, 핸드오프, inspector 계약만
증명합니다. 라이브 시각 품질, 상업 허가, 다른 공급자 우월은 증명하지
않습니다.

## 라이브 증거 경계

라이브 이미지 호출은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가
요구하지 않습니다. 오프라인 통과를 라이브 시각 결과로 바꾸지 마세요. 사용자
이미지, 비공개 참조, 생성 매체, 자격 증명, receipt는 커밋하지 않습니다.

Grok 4항 smoke 기록은
`tests/products/image-workbench/live/smoke-record.json`에 있습니다. 운영
절차는 [테스트](testing.md)와 `tests/products/image-workbench/live/README.md`를
따릅니다.

## 새 호스트 지원

새 프로그램을 지원한다고 쓰려면 같은 빌드에서 아래 네 가지를 실제로 돌려
통과해야 합니다.

1. 스킬을 찾는다
2. `$image-workbench` 또는 `/image-workbench`로 부른다
3. 프로젝트 이미지를 달라고 하면 켜지고, `kws-image-workbench`는 켜지지 않는다
4. brief/audit은 파일을 만들지 않고, 승인된 generate/edit는 프로젝트 파일로
   저장된다

기록이 없으면 그 프로그램은 지원이 아닙니다. 공유 사용자 안내는
[호환성](../../../users/ko/compatibility.md)을 보세요.
