# Architecture Decisions

## ADR-001 — Codex remains the Supervisor

**Status:** ACCEPTED

Local LLM은 Codex를 대체하는 최종 권위가 아니다. Codex가 Task acceptance, architecture 판단, difficult debugging, final review를 담당한다.

### Reason

작은 Local LLM에게 전체 Agent 권한과 최종 판단을 동시에 주면 tool misuse, context drift, false PASS가 실제 Repository 변경으로 이어질 위험이 크다.

---

## ADR-002 — Local models are bounded/stateless Workers

**Status:** ACCEPTED

Worker는 Harness가 제공한 제한 Context를 받아 Candidate만 생성한다.

직접 filesystem/Git/shell/network 권한을 기본 제공하지 않는다.

### Reason

작은 모델은 tool loop보다 bounded generation에서 더 예측 가능하며 Harness가 orchestration과 validation을 deterministic하게 담당할 수 있다.

---

## ADR-003 — Use an isolated Git worktree for target changes

**Status:** ACCEPTED

`D:\team_project_os\team_project_os-main`은 원본으로 유지하고, 실제 변경은 `D:\AI_worker\worktree\team_project_os`에서 진행한다.

### Reason

실험 실패와 Candidate 오류를 원본 작업 디렉터리에서 격리하기 위함이다.

---

## ADR-004 — Model selection is benchmark-driven and replaceable

**Status:** ACCEPTED

특정 Qwen/Mistral 모델을 Architecture에 고정하지 않는다.

조건:

- 무료
- 로컬 실행 가능
- 현재 PC에서 실용적인 속도/메모리
- 역할별 Benchmark에서 유효한 결과

새 모델은 동일 Task set으로 기존 역할 모델과 비교한 뒤 채택한다.

---

## ADR-005 — Sequential model execution on the current PC

**Status:** ACCEPTED

초기 V1에서는 큰 Local 모델 여러 개의 병렬 상주를 전제로 하지 않는다.

### Reason

8GB급 GPU 환경에서는 VRAM 경쟁과 모델 swap 비용 때문에 병렬화보다 순차 역할 교대가 안정적이다.

---

## ADR-006 — Evidence over self-report

**Status:** ACCEPTED

Worker가 PASS라고 말해도 완료로 판단하지 않는다.

완료 근거는 가능한 경우 다음 순서로 둔다.

1. deterministic format/schema validation
2. `git apply --check`
3. `git diff --check`
4. focused tests
5. regression tests
6. Git status/commit evidence
7. Codex final review

---

## ADR-007 — Research records are first-class project artifacts

**Status:** ACCEPTED

성공한 코드만 보존하지 않는다. 실패한 Prompt, 모델별 차이, Context 크기, inference 시간, 수정 횟수도 연구 자료로 기록한다.

### Reason

AI Worker의 핵심 자산은 단일 Harness 코드뿐 아니라 어떤 모델/Context/Orchestration 조합이 실제 개발에서 잘 작동했는지에 대한 누적 Evidence이기 때문이다.
