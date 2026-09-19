# sddx 릴리스

이 문서는 SDDx의 독립 패키징 절차를 소유합니다. 버전 원본은
`skills/sddx/release.toml`입니다. `SKILL.md` `metadata.version`은 검증된
복제 값입니다. 사람이 체감하는 이력은 같은 디렉터리의 `CHANGELOG.md`입니다.

공개 sddx 릴리스는 아직 없습니다. 이 제품은 통합 `v2.0.0` GitHub Release와
불변 카탈로그 lock에 포함되지 않았습니다. 지금 개발 중인 독립 버전은
`4.0.1`이며 `release.toml`이 원본입니다. 태그와 아티팩트는 없습니다.

`4.0.1` 변경은 CHANGELOG의 `## 4.0.1 - 2026-09-19`에 있습니다. 공개 태그를
만들 때 이 절을 확정하고 새 빈 `Unreleased` 절을 엽니다.
`release.toml`, `SKILL.md` `metadata.version`,
`.claude-plugin/plugin.json`의 `version`은 항상 같은 값이어야 합니다.

`2.0.0`은 그 이전 MAJOR입니다. Cursor backend의 필수 CLI 기능과 기본 실행
계약이 바뀌었습니다. `--auto-review`, `--sandbox`, 구조화 출력 형식을
선언하지 않는 기존 Cursor CLI는 `--force`/`--yolo` 일괄 승인으로 물러나지
않고 `available: false`, `reason: missing_flags`로 차단됩니다. 공개 태그가
아직 없는 제품이어도 개발 버전의 계약 변경을 숨기지 않습니다. 판단 기준은
[`docs/maintainers/repository/versioning.md`](../../repository/versioning.md)의
스킬 SemVer 표입니다.

`1.0.2`와 `1.0.3`은 태그와 아티팩트 없이 main에만 올라간 개발 단계 버전이며
출시되지 않았습니다. 두 버전의 변경은 `1.1.0`에 포함됩니다. 유지보수 문서의
`1.0.2`·`1.0.3` 절은 그 시점의 측정 기록이므로 번호를 그대로 둡니다.

## 검사, 빌드, 다운로드

공통 check / build / verify-download 명령은
[`docs/maintainers/repository/release.md`](../../repository/release.md)를
보세요. 제품 검사는 `python3 scripts/release.py check --product sddx`입니다.

`python3 scripts/release.py check --product sddx`는 오프라인 검사이므로 Claude
Code가 `agents/claude-code/` 정의를 계속 싣는지는 확인하지 못합니다. 릴리스마다
[`testing.md`](testing.md)의 `리뷰어 effort 증거` 절에 있는 라이브 확인을 수동으로
실행하고, 실패하면 릴리스를 멈춥니다.

XHigh 리뷰어 정의가 Claude Code에 실제로 실리는지는 공개 태그 전에 확인할
절차입니다. `4.0.1`에서 로딩을 확인했고 상태는 `measured`입니다. 적용된
effort는 이 절차의 대상이 아닙니다. 확인 없이 공개 릴리스 완료를 선언하지
않습니다. 이 명령은 제품 소유 경로와 공용 릴리스 코드의 작업 트리가 깨끗할
때만 통과하므로 변경을 커밋한 뒤 실행합니다.

제품 태그는 `sddx-v<version>`입니다. 태그와 Draft는 명시적 출시 작업입니다.
로컬 빌드의 부수 효과가 아닙니다.

설치 파일이 바뀌면 `release.toml`과 `SKILL.md` 버전 결정과 제품 CHANGELOG
항목이 같은 변경에 있어야 합니다. 초판은 태그를 만들지 않습니다.

## 실패 복구

- 로컬 검증 실패: 파일, 버전, CHANGELOG 또는 테스트를 고치고 다시 검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지 않습니다.
- 이 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지 않습니다.

이 명령은 태그 또는 GitHub Release를 만들지 않습니다.
