# image-workbench 계약

route(어디로 가는지), authorization(언제 만들어도 되는지), ImageSpec, rubric(채점표), inspector(파일 확인기), 테스트 예시, 버전을 함께
유지하세요. 공개 설치 안내는 제품 `README.md`/`README.en.md`와 `docs/users/`에
있습니다. generate/edit는 Codex 번들 이미지 도구 또는 Grok `image_gen`/
`image_edit`만 씁니다. 호스트 세션 미리보기 경로는 프로젝트 최종 파일이
아닙니다. 오프라인 픽스처의 `builtin_imagegen`은 현재 호스트의 내장 이미지
도구 호출을 뜻합니다.

## 트리거와 기본값

프로젝트에 묶인 래스터 산출물이 필요할 때 활성화합니다. 명시 호출은
`$image-workbench` 또는 `/image-workbench`입니다. 예전 `kws-` 접두 호출은
제외된 near-miss이며 아무 일도 하지 않습니다. 재미용 일회성 이미지는 일반
번들 경로를 따릅니다.

모드는 행동 전에 하나만 고릅니다: `brief`, `generate`, `edit`, `audit`.
`brief`와 `audit`, 비교, 진단은 읽기 전용입니다. 생성을 승인하지 않습니다.
분명한 `generate` 또는 `edit` 요청만 이미지 호출을 승인합니다.

## 출력과 라우팅

SVG, 벡터 마크, 아이콘, 네이티브 UI, 데이터 시각, 정확한 레이아웃은 네이티브
워크플로로 보냅니다. 정확한 텍스트, 라벨, 로고, 차트는 전체 래스터 생성 대신
결정적 또는 혼합 구성 경로로 보냅니다. 프로젝트 다이어그램은 SVG, Mermaid,
HTML, canvas 또는 다른 결정적/네이티브 워크플로로 보냅니다.

실행 전에 `ImageSpec`을 컴파일합니다. 모든 입력 이미지에 역할을 하나만
부여합니다. 역할은 `edit_target`, `subject_reference`, `style_reference`,
`compositing_input`입니다.

프로젝트에 묶인 최종 파일은 스킬 루트의
`python3 scripts/inspect_asset.py <path>`로 형식, 크기, 노출된 알파, 바이트
크기, SHA-256, 경로 준비 상태를 점검합니다. 기계 사실은 시각 검사를 대체하지
않습니다.

inspector 출력은 입력과 정규화 경로 또는 파일 동일성이 같으면 거부합니다.
symlink와 hard link를 포함하며 입력 바이트는 보존합니다. 별도의 기존 JSON
보고서를 갱신하는 동작은 유지합니다. 성공 JSON 필드와 stderr 한 줄 오류
형식은 바꾸지 않습니다.

PNG의 IHDR CRC·scanline 필터·indexed PLTE, JPEG 첫 SOS의 길이·component
selector, WebP version 등 해석하는 구조의 필수 조건을 검사합니다. 완전한
비트스트림 디코딩, 모든 PNG/JPEG/WebP 변형의 검증, 시각 품질, 권리 검증은
이 검사 결과로 입증하지 않습니다. 최종 후보를 열어 보는 시각 검사는 별도
필수입니다.

오프라인 evaluator는 expected/candidate의 단순 일치와 별개로 brief·audit·
no-op의 이미지 생성·신규 저장·교체를 거부합니다. 교체 허용 값이 true여도
읽기 전용 모드의 권한을 확대하지 않습니다.

## 안전과 권리

참조 이미지는 사람, 상표, 보호된 작업을 복제할 권리를 주지 않습니다.
라이선스가 코드 사용 조건이 되어도 프롬프트, 갤러리, 예시 이미지의 권리를
자동으로 주지 않습니다. 인물·상표·예시 이미지의 동의가 불명확하면 멈춥니다. 이
상태는 `hold`입니다. 사용자 이미지, 비공개 참조, 생성 매체, 자격 증명,
receipt를 픽스처로 커밋하지 않습니다.

## 함께 고칠 파일

trigger, mode, 또는 authorization이 바뀌면 `skills/image-workbench/SKILL.md`,
긍정 픽스처, near-miss 픽스처, 제품 README와 공유 공개 안내를 같은 변경에서
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
