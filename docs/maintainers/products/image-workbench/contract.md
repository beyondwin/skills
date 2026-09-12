# image-workbench 계약

route(어디로 보내는지), authorization(언제 만들어도 되는지), ImageSpec(작업
메모), rubric(채점표), inspector(파일 확인기), 테스트 예시, 버전을 함께
유지하세요. 공개 설치 안내는 제품 `README.md`/`README.en.md`와 `docs/users/`에
있습니다. 만들거나 고칠 때는 Codex 안 그림 도구 또는 Grok `image_gen`/
`image_edit`만 씁니다. 대화 창에만 있는 미리보기 경로는 프로젝트 최종 파일이
아닙니다. 오프라인 예시의 `builtin_imagegen`은 “지금 쓰는 프로그램의 그림
도구를 호출한다”는 뜻입니다.

## 트리거와 기본값

이 프로젝트에 넣을 비트맵이 필요할 때 켭니다. 명시 호출은
`$image-workbench` 또는 `/image-workbench`입니다. 예전 `kws-` 이름은
잘못 친 호출이며 아무 일도 하지 않습니다. 재미로 한 장만 그리는 일은 프로그램
기본 그림 기능을 따릅니다.

모드는 행동 전에 하나만 고릅니다: `brief`, `generate`, `edit`, `audit`.
`brief`와 `audit`, 비교, 진단은 읽기 전용입니다. 생성을 승인하지 않습니다.
분명한 `generate` 또는 `edit` 요청만 이미지 호출을 승인합니다.

## 출력과 라우팅

아이콘, 화면 UI, 정확한 레이아웃, SVG는 그림 생성이 아니라 코드/벡터 쪽으로
보냅니다(route). 정확한 글자, 로고, 차트도 통째로 그리지 말고 결정적 또는
혼합 경로를 씁니다. 다이어그램은 SVG, Mermaid, HTML, canvas 쪽으로 보냅니다.

실행 전에 `ImageSpec`을 만듭니다. 입력 그림마다 역할을 하나만 붙입니다.
역할은 `edit_target`, `subject_reference`, `style_reference`,
`compositing_input`입니다.

프로젝트에 넣을 최종 파일은 스킬 폴더에서
`python3 scripts/inspect_asset.py <path>`로 형식과 크기를 봅니다. 이 숫자는
눈으로 보는 검사를 대체하지 않습니다.

inspector는 입력 이미지와 같은 파일을 결과로 쓰지 않습니다. 바로가기나
하드 링크도 같습니다. 입력 그림은 그대로 둡니다. 이미 있는 별도 JSON 보고서는
갱신할 수 있습니다.

이 검사는 PNG·JPEG·WebP의 기본 구조만 봅니다. 그림이 좋거나 권리가 있다는
증명이 아닙니다. 최종 후보는 반드시 엽니다.

오프라인 평가기는 brief·audit·아무 일도 안 하는 경로에서 그림을 만들거나
새 파일로 저장하거나 덮어쓰는 것을 거절합니다. 교체가 허용되어도 읽기 전용
모드의 authorization은 커지지 않습니다.

## 안전과 권리

참조 이미지는 사람, 상표, 보호된 작업을 복제할 권리를 주지 않습니다.
라이선스가 코드 사용 조건이 되어도 프롬프트, 갤러리, 예시 이미지의 권리를
자동으로 주지 않습니다. 인물·상표·예시 이미지의 동의가 불명확하면 멈춥니다. 이
상태는 `hold`입니다. 사용자 이미지, 비공개 참조, 생성 매체, 자격 증명,
receipt를 픽스처로 커밋하지 않습니다.

## 함께 고칠 파일

trigger, mode, 또는 authorization이 바뀌면 `skills/image-workbench/SKILL.md`,
긍정 픽스처, 잘못 친 이름 픽스처, 제품 README와 공유 공개 안내를 같은 변경에서
고칩니다. `brief`/`audit`의 읽기 전용 경계와 generate/edit의 명시 승인을
픽스처로 다시 확인하세요.

ImageSpec, 입력 역할, route 변경은 스킬,
[ImageSpec 참조](../../../../skills/image-workbench/references/image-spec.md),
픽스처를 맞춥니다. 수락 기준이 바뀌면 같은 변경에서
[품질 루브릭](../../../../skills/image-workbench/references/quality-rubric.md)을
고칩니다. 상태나 핸드오프 변경은 루브릭, 평가기, 픽스처, 공개 안내를 함께
고칩니다.

공급자 또는 출처 주장은 직접 권위 locator, 확인 날짜, 채택 아이디어, 거절
경계가 필요합니다. 런타임 동작을 자동으로 바꾸지 않습니다. 새 외부 저장소를
쓰려면 그 리비전의 불변 커밋, 그 리비전에서 읽은 라이선스 파일, 재사용 경계를
[sources.md](../../../../skills/image-workbench/references/sources.md)에
기록합니다.
