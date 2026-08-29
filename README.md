# AI Worker

> Codex를 Supervisor로 두고 무료 Local LLM을 bounded/stateless Worker로 사용하여 개발 작업을 오래, 안정적으로 수행하기 위한 로컬 AI Engineering Harness.

## 목표

AI Worker의 목적은 **Codex를 대체하는 것**이 아닙니다.
Codex가 모든 탐색·초안·반복 작업을 직접 수행하지 않도록 Local LLM에게 저비용 작업을 위임하고, Codex는 설계 판단·최종 리뷰·실패 분석·승인을 담당합니다.

첫 번째 실제 적용 대상은 다음 Repository입니다.

- Target: `D:\team_project_os\team_project_os-main`
- AI Worker: `D:\AI_worker`
- 작업용 Worktree: `D:\AI_worker\worktree\team_project_os`

## 기본 구조

```text
Human
  ↓
Codex Supervisor
  ├─ Task 선택 / 분해
  ├─ Architecture 판단
  ├─ Candidate 최종 Review
  ├─ Test / Git Evidence 확인
  └─ Commit 승인
       ↓
AI Worker Harness
  ├─ Scout Worker
  ├─ Planner Worker
  ├─ Coder Worker
  ├─ Reviewer Worker
  └─ Escalation Worker
       ↓
Bounded Context + Candidate Patch / Review
       ↓
Git Worktree
       ↓
Tests / Evidence
```

Local Worker에게 Repository filesystem, Git, shell 권한을 직접 주지 않습니다. Harness가 필요한 Context만 읽어 전달하고 Worker는 Candidate만 반환합니다.

## 운영 원칙

1. Local LLM 출력은 항상 **Candidate**입니다.
2. Worker의 `PASS` 자기보고는 신뢰하지 않습니다.
3. 완료는 Git/Test Evidence로 판단합니다.
4. 원본 Repository는 직접 수정하지 않고 Git worktree에서 변경합니다.
5. 큰 작업은 작은 Task로 분해합니다.
6. Codex가 전체 Repository를 반복해서 읽지 않도록 Context를 제한합니다.
7. 모델은 특정 제품에 고정하지 않습니다.
8. 무료이며 현재 PC에서 실사용 가능한 모델만 채택합니다.
9. 모델 교체는 느낌이 아니라 동일 Benchmark 결과로 결정합니다.
10. 연구·실험·실패도 Repository에 기록합니다.

## 현재 모델 후보

현재 설치 모델을 먼저 Benchmark합니다.

- `qwen3:4b`
- `qwen2.5-coder:7b`
- `qwen3:8b`
- `qwen3.5:9b`
- `qwen2.5-coder:14b-instruct-q3_K_S`
- `mistral-nemo:12b-instruct-2407-q3_K_S`
- `command-r7b:7b-12-2024-q4_K_M`

새 무료 모델은 기존 모델보다 실제 결과가 좋아질 가능성이 있을 때만 추가합니다.

## 실행

```powershell
python ai_worker.py doctor
python ai_worker.py bootstrap
python ai_worker.py benchmark
python ai_worker.py status
```

`benchmark`는 loopback Ollama, frozen Target HEAD/file hashes, 역할별 Stable Case,
raw output, JSONL metrics, deterministic schema/patch/test gate를 사용합니다. 모델이
생성한 patch는 Target에 적용하지 않고 disposable clone에서만 검사합니다.

## 기록 구조

```text
AI_Worker/
├─ README.md
├─ PROJECT.md
├─ ARCHITECTURE.md
├─ DECISIONS.md
├─ STATUS.md
├─ AGENTS.md
├─ ai_worker.py
├─ benchmark_runner.py
├─ benchmarks/
│  ├─ suite_v1.json
│  ├─ suite_v2.json
│  └─ fixtures/
├─ benchmark_results/   # 선별 보존하는 machine-readable benchmark Evidence
├─ config/
│  └─ models.json
├─ docs/
│  ├─ RESEARCH_LOG.md
│  ├─ DEV_LOG.md
│  └─ MODEL_BENCHMARK.md
├─ runs/                 # 로컬 실행 결과. 필요한 Evidence만 선별 커밋
├─ tasks/                # 현재/완료 Task 계약과 결과
├─ tests/                # Harness unit/regression tests
└─ worktree/             # GitHub에 올리지 않음
```

## 작업 철학

가장 강한 모델 하나에게 모든 것을 맡기는 구조보다,
**Harness가 deterministic orchestration을 담당하고 모델은 제한된 Context에서 전문 역할만 수행**하도록 만드는 것을 우선합니다.

목표 지표는 단순 생성 속도가 아니라 다음입니다.

- Codex 사용량 감소
- Task 성공률
- Patch 적용 성공률
- Test 통과율
- Regression 발생률
- Human 개입 횟수
- Local inference 시간
- 반복 수정 횟수

실험 결과는 `docs/MODEL_BENCHMARK.md`, 연구 과정은 `docs/RESEARCH_LOG.md`, 실제 개발 변경은 `docs/DEV_LOG.md`에 누적합니다.
