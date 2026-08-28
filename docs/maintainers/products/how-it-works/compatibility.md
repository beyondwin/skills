# how-it-works 호환성

현재 지원 호스트는 제품 레지스트리의 `codex`, `claude-code`, `grok`, `cursor`입니다. 다른 호스트를 지원한다고 쓰지 마세요.

## 필요한 호스트 능력

- 로컬 Agent Skills 디렉터리 설치와 `SKILL.md` 파일 접근
- GitHub-flavored markdown과 mermaid 소스를 채팅으로 반환하는 능력
- mermaid 렌더러는 필수가 아닙니다. 렌더러가 없어도 홉 목록이 읽혀야 합니다

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill how-it-works`입니다. `tests/products/how-it-works/cases.json`과 `tests/products/how-it-works/test_contract.py`는 형태와 페이로드 계약만 증명합니다. 라이브 모델 품질은 증명하지 않습니다.

## 라이브 증거 경계

라이브 실행은 로컬, 명시적, 선택적이며 비용이 들 수 있습니다. CI가 요구하지 않습니다. 페이로드 계약 통과를 라이브 호출 증거로 설명하지 마세요. 사용자 주제, 압박 트랜스크립트, 비공개 로그는 커밋하지 않습니다.

운영 절차는 [테스트](testing.md)를 따릅니다.

## 새 호스트 지원

새 지원을 레지스트리와 공개 안내에 넣으려면 같은 빌드에서 다음 네 가지 smoke가 통과해야 합니다.

1. 스킬 발견
2. 명시 호출
3. 의도한 암묵 호출과 near-miss 비호출
4. 출력 계약(마크다운, mermaid 소스, 번호 있는 홉 목록)

기록이 없으면 그 호스트는 지원이 아닙니다. 공유 사용자 안내는 [호환성](../../../users/ko/compatibility.md)을 보세요.
