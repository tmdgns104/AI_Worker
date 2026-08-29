# AI Worker Project

## Problem

고성능 Cloud AI/Codex가 Repository 탐색, 반복 수정, 초안 작성, 리뷰까지 모두 직접 수행하면 품질은 높지만 사용량과 Context 비용이 커지고 장시간 개발 시 지속성이 떨어진다.

반대로 Local LLM에게 Agent 권한을 모두 주면 작은 모델의 판단 오류, Tool 사용 실패, Context 오염, 무한 반복이 실제 Repository에 직접 영향을 줄 수 있다.

## Goal

Codex를 Supervisor로 유지하면서 Local LLM을 bounded/stateless Worker로 사용해 다음을 달성한다.

- Codex 사용량 절감
- 장시간 작업 지속성 향상
- Local LLM의 장점을 안전하게 활용
- 결과 품질은 Git/Test Evidence로 보증
- Worker/모델을 쉽게 교체 가능한 구조
- 연구와 개발 과정을 재현 가능한 기록으로 축적

## First Target

`D:\team_project_os\team_project_os-main`

AI Worker 자체와 Target Repository는 분리한다.

- AI Worker: orchestration, prompts, model routing, benchmark, evidence
- Target Repository: 실제 제품 코드와 제품 Source of Truth

## Non-goals

초기 단계에서는 다음을 목표로 하지 않는다.

- Local LLM에게 unrestricted shell/filesystem/Git 권한 제공
- Codex 완전 제거
- 여러 대 GPU 분산 추론
- Cloud inference 필수화
- 모델 파인튜닝
- 자동 push/merge/release

## Success Criteria

V1 성공 기준:

1. `team_project_os`의 실제 Task를 Local Worker가 Candidate로 생성할 수 있다.
2. Codex가 전체 Repository를 직접 읽지 않고 Candidate + Evidence 중심으로 검토할 수 있다.
3. Worker의 잘못된 Patch가 자동으로 원본에 적용되지 않는다.
4. 실패 시 bounded revision 또는 다른 모델로 escalation할 수 있다.
5. 동일 Benchmark로 모델별 품질/속도/안정성을 비교할 수 있다.
6. 모든 중요한 실험과 Architecture 결정이 Git에 남는다.
