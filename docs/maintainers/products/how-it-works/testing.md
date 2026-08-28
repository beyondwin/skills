# how-it-works 테스트

`tests/products/how-it-works/cases.json`과 `tests/products/how-it-works/test_contract.py`에서 다섯 형태 케이스를 정직하게 유지하세요. 사용자 주제, 압박 트랜스크립트, 비공개 로그를 Git 픽스처로 커밋하지 마세요.

## 결정적 픽스처

- `gate-dump-01`은 질문이 필요하고 첫 턴에 mermaid가 없습니다.
- `html-01`은 mermaid가 필요하고 HTML 태그(`<html`, `<style`, `<div`)를 금지합니다. 이 형태 픽스처는 채팅 출력의 금지 문자열을 잠급니다. 기본 산출이 게시된 페이지라는 계약을 채팅 전용으로 되돌리지 않습니다.
- `type-cmp-01`은 표와 권고가 필요하고 동점이 아닙니다.
- `scope-01`은 조각 선택지가 필요하고 OSI dump가 아닙니다.
- `ko-gloss-01`은 `rebase` 용어 설명이 필요하고 `여러분` / `답니다`를 금지합니다.

페이로드 계약 통과는 파일 정체성과 금지 문자열만 증명합니다. 라이브 모델 품질을 증명하지 않습니다. 이 스킬 호출에서 `/eli5`를 다루지 마세요.

## 명령

```bash
python3 scripts/verify.py --skill how-it-works
python3 scripts/verify.py
python3 -m unittest discover -s tests/products/how-it-works -p 'test_contract.py'
git diff --check
```

페이로드 계약을 라이브 호출 증거로 설명하지 마세요. 라이브 실행은 선택이며 CI가 요구하지 않습니다.
