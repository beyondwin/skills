# sddx 릴리스

이 문서는 SDDx의 독립 패키징 절차를 소유합니다. 버전 원본은
`skills/sddx/release.toml`입니다. `SKILL.md` `metadata.version`은 검증된
복제 값입니다. 사람이 체감하는 이력은 같은 디렉터리의 `CHANGELOG.md`입니다.

공개 sddx 릴리스는 아직 없습니다. 이 제품은 통합 `v2.0.0` GitHub Release와
불변 카탈로그 lock에 포함되지 않았습니다. 현재 독립 버전은 `release.toml`이
소유하며 현재 버전은 `1.1.1`입니다.

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

제품 태그는 `sddx-v<version>`입니다. 태그와 Draft는 명시적 출시 작업입니다.
로컬 빌드의 부수 효과가 아닙니다.

설치 파일이 바뀌면 `release.toml`과 `SKILL.md` 버전 결정과 제품 CHANGELOG
항목이 같은 변경에 있어야 합니다. 초판은 태그를 만들지 않습니다.

## 실패 복구

- 로컬 검증 실패: 파일, 버전, CHANGELOG 또는 테스트를 고치고 다시 검증합니다.
- 패키징 실패: 새 출력 디렉터리에서 다시 빌드합니다. 부분 결과를 재사용하지 않습니다.
- 이 제품 실패: 다른 제품의 버전, 태그, Release와 카탈로그 lock을 바꾸지 않습니다.

이 명령은 태그 또는 GitHub Release를 만들지 않습니다.
