# promptops

프롬프트 운영 도구의 도메인 계층입니다. 저장소, 편집 세션, 모델로 문체를 입히는 일괄 작업을 담습니다.
UI는 이 계층 위에 따로 있습니다.

- Python 3.11+, 표준 라이브러리만 씁니다(외부 패키지 추가 금지).
- 시험: `python3 -m unittest discover -s tests -t .`
- 모델은 시험에서 `promptops.fake_model.FakeModel`로 대신합니다.
- 동시 실행은 `promptops.concurrency.gather_limited`를 씁니다.
