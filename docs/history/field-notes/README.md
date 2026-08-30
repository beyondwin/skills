# 현장 관찰 기록 / Field notes

이 디렉터리는 제품을 실제 작업에 적용하며 확인한 시점 고정 관찰과 개선 후보를
보관합니다. 현재 제품 계약이나 승인된 변경을 정의하지 않습니다.

Field notes are point-in-time observations from real product use. They do not
define the current contract or authorize a product change.

## 기록 원칙

- 관찰한 제품 버전과 날짜를 적고, 가능하면 source commit이나 계약 fingerprint를
  함께 남깁니다.
- 현재 계약, 관찰 사실, 해석, 개선 후보를 구분합니다.
- 원문 prompt, 전체 reviewer 응답, command output, 절대 경로, 계정 정보,
  환경 변수와 credential을 저장하지 않습니다.
- 한 사례에서 확인하지 못한 빈도나 일반성을 주장하지 않습니다.
- 채택된 변경은 해당 제품의 `SKILL.md`, maintainer contract, test와
  `CHANGELOG.md`에서 별도로 관리합니다.
