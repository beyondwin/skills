# beyondwin-skills catalog

`beyondwin-skills`는 따로 버전을 매기는 Codex 플러그인 카탈로그입니다. 스킬 제품 계약을 소유하지 않습니다. 이미 공개된 스킬 버전을 받아 플러그인 번들로 묶습니다.

마지막 공개 카탈로그는 `beyondwin-skills` `2.0.0`입니다. 그 릴리스는 공개 `v2.0.0`의 `image-workbench`와 `korean-writing-editor` standalone 페이로드를 lock합니다. 현재 `skills/` 개발, 미공개 `how-it-works`와 `pre-sdd-review`는 카탈로그 소스가 아닙니다.

This catalog's contract is: only released plugin ZIPs are supported catalog artifacts; the repository root is for individual skill installs. Plugin metadata for catalog builds lives at `plugin/.codex-plugin/plugin.json` and is copied to the plugin ZIP root at catalog release time. `catalog.lock.json` records the immutable skill releases the catalog adopted.
