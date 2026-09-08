# beyondwin-skills catalog

`beyondwin-skills`는 따로 버전을 매기는 Codex 플러그인 묶음입니다. 스킬
제품 규칙을 소유하지 않습니다. 이미 공개된 스킬 버전을 받아 플러그인으로
묶습니다.

마지막 공개 카탈로그는 `beyondwin-skills` `2.0.0`입니다. 그 릴리스는 공개
`v2.0.0`의 `image-workbench`와 `korean-writing-editor` 설치 파일만
고정(lock)합니다. 지금 `skills/` 개발과, 아직 묶음에 없는 `how-it-works`,
`pre-sdd-review`는 카탈로그 소스가 아닙니다.

지원되는 카탈로그 아티팩트는 공개된 플러그인 ZIP뿐입니다. 저장소 루트는 개별
스킬을 설치하는 곳입니다. 플러그인 정보는
`plugin/.codex-plugin/plugin.json`에 있고, 카탈로그를 만들 때 ZIP 루트로
복사됩니다. `catalog.lock.json`은 카탈로그가 채택한 고정 스킬 릴리스를
기록합니다.

고정 목록 채택과 받은 파일 확인은
[카탈로그 릴리스](../docs/maintainers/repository/catalog.md)를 보세요.
