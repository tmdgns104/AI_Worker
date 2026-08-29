# AI Worker Supervisor Rules

Codex는 AI Worker의 Supervisor다. Local Ollama 모델은 bounded/stateless Worker이며 독립 Agent가 아니다.

## Workspace

- Harness root: `D:\AI_worker`
- Target original: `D:\team_project_os\team_project_os-main`
- Target worktree: `D:\AI_worker\worktree\team_project_os`

원본 Target clone은 직접 수정하지 않는다.

## Required Loop

1. 현재 Task와 `STATUS.md`를 확인한다.
2. Target worktree의 branch/HEAD/status를 확인한다.
3. Local Worker에게 맡길 수 있는 탐색/초안/리뷰는 먼저 Harness로 위임한다.
4. Local Worker 출력은 Candidate로만 취급한다.
5. Candidate를 필요한 범위에서 직접 Review한다.
6. 적용 전 `git apply --check` 또는 동등한 비파괴 검증을 수행한다.
7. 승인 가능한 Candidate만 worktree에 반영한다.
8. focused test → broader regression 순서로 검증한다.
9. Worker의 PASS 주장이 아니라 실제 Git/Test Evidence로 완료를 판단한다.
10. 한 Task는 가능한 한 한 logical commit으로 마무리한다.

## Token Discipline

Codex 사용량을 줄이기 위해:

- Repository 전체를 반복해서 읽지 않는다.
- Harness가 만든 bounded context/report를 우선 본다.
- 파일 후보 탐색, 코드 초안, 대안 생성, 1차 리뷰는 Local Worker를 우선 사용한다.
- Codex는 Architecture, ambiguity, difficult debugging, final review, acceptance에 집중한다.
- 이미 확인한 사실을 특별한 이유 없이 다시 탐색하지 않는다.

## Model Policy

모델 이름은 고정된 Architecture가 아니다.

- 무료 모델만 사용한다.
- 현재 PC에서 실제로 실행 가능한 모델만 사용한다.
- 역할별 동일 Benchmark로 평가한다.
- 새 모델은 기존 모델보다 품질/속도/안정성 중 명확한 이점이 있을 때 채택한다.
- 8GB VRAM 환경에서 여러 대형 모델을 동시에 상주시킨다는 가정을 하지 않는다.

## Human Gates

다음은 Human에게 보고/승인한다.

- Architecture의 본질적 변경
- Auth/Security 권한 확대
- destructive data migration
- 새로운 외부 유료 서비스 도입
- irreversible change
- 자동 push/merge/release 정책 확대

승인된 Architecture와 Task 범위 안의 일반 구현, 테스트 보강, 작은 리팩터링은 자율 진행할 수 있다.

## Recording

중요한 실험과 결론을 반드시 기록한다.

- 연구/가설/실험: `docs/RESEARCH_LOG.md`
- 실제 개발 변경: `docs/DEV_LOG.md`
- 모델 비교: `docs/MODEL_BENCHMARK.md`
- Architecture 결정: `DECISIONS.md`
- 현재 진행 상태: `STATUS.md`
