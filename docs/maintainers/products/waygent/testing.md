# waygent 테스트

이 문서는 waygent를 무엇으로 검사하는지 적습니다. 모든 필수 검사는 공급자 호출과
자격 증명 없이 돕니다. 오프라인 통과를 실제 모델 품질이나 호스트 실행 증거로
넓히지 않습니다.

픽스처 경로는 `tests/products/waygent/`입니다.

## 공급자 없는 증거

필수 증거는 `python3 scripts/verify.py --skill waygent`입니다. 단계는
`product-contract`, `waygent-contract`, `python-compile`입니다.

`tests/products/waygent/test_contract.py`가 잠그는 것은 다음과 같습니다.

- `validate_product` 통과, frontmatter `name`·`license`·`metadata.version`과
  `release.toml` 일치
- description의 `/waygent` 게이트와 가까운 요청 제외(`/sddx`,
  `subagent-driven-development`, 브레인스토밍·스펙, 작은 수정 하나)
- `.waygent/` 기록 위치와 `.gitignore` `*`, `Waygent-Task:` 트레일러
- 재리뷰 없음, 최종 리뷰 한 번, `main`·`master` 커밋 금지, 같은 모델·더 싼 모델 금지,
  한 등급 위(`one tier up`)는 최종 리뷰와 재시도에만
- `SKILL.md` 140줄 미만

검사는 문구 몇 개만 봅니다. `SKILL.md`가 아직 바뀌는 중이라 digest나 전체 문장을
고정하지 않습니다.

## 명령

```bash
python3 scripts/verify.py --skill waygent
python3 -m unittest discover -s tests/products/waygent -p 'test_*.py'
```

## 라이브 측정

라이브 측정은 기본 검증에 들어가지 않습니다. 과제, 숨긴 테스트, 드라이버는
[waygent 설계와 실측](../../../research/2026-09-waygent-eval/README.md)에 있고, 호스트별 기록은
[호환성](compatibility.md)에 적습니다. 설치 파일의 동작 규칙이 바뀌면 그 하네스로 다시 잽니다.
