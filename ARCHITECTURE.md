# Architecture

## Overview

AI Worker는 **Deterministic Harness + Bounded Stateless Workers + Codex Supervisor** 구조를 사용한다.

```text
Human
  ↓
Codex Supervisor
  ↓ task / acceptance policy
Deterministic Harness
  ├─ Repository Inspector
  ├─ Context Builder
  ├─ Model Router
  ├─ Candidate Validator
  ├─ Evidence Collector
  └─ Run Recorder
       ↓ bounded packet
Local LLM Worker
       ↓ candidate only
Harness
       ↓ candidate + deterministic evidence
Codex Supervisor
       ↓ accepted change only
Target Git Worktree
       ↓
Tests / Git Evidence
```

## Responsibilities

### Codex Supervisor

- 목적과 Task 범위 해석
- Architecture 변경 판단
- Local Worker 결과 최종 Review
- Candidate 적용 여부 결정
- 실패 원인 분석
- Test/Git Evidence를 기반으로 완료 판정
- 필요 시 더 강한 Worker로 escalation

### Harness

- Repository 상태를 deterministic하게 읽음
- 필요한 파일만 Worker Context로 선택
- Worker 호출
- 출력 형식 검증
- `git apply --check` 같은 비파괴 검증
- Test 명령 실행 및 Evidence 수집
- Run 결과 기록
- Retry/Stop 조건 관리

### Local Worker

Local Worker는 직접 Agent가 아니다.

허용:
- 제한된 Context 분석
- 계획 Candidate 생성
- 코드/patch Candidate 생성
- Review Candidate 생성
- 테스트 아이디어 생성

금지:
- filesystem 직접 탐색
- Git 직접 실행
- shell 직접 실행
- 임의의 dependency 설치
- push/merge
- architecture 권한 확대

## Worker Pipeline

기본 경로:

```text
Scout → Planner → Coder → Reviewer → Codex
```

Escalation:

```text
Coder 실패
  ↓
Codex feedback
  ↓
Stronger Coder
  ↓
Independent Reviewer
  ↓
Codex
```

작은 Task에서는 Planner/Reviewer 일부를 생략할 수 있다. Harness는 모든 Task에 동일한 비싼 Pipeline을 강제하지 않는다.

## Model Routing

`team-project-os-role-benchmark-v2` 결과에 따른 초기 운영 routing:

- Scout: `qwen3:8b`; missing required concepts trigger deterministic context expansion,
  then `qwen3.5:9b` fallback or Codex.
- Planner: `qwen3:8b`; schema/file selection never substitutes for behavior-semantic
  validation. 14B is the bounded fallback.
- Coder: `qwen2.5-coder:7b` is only a fast candidate generator. It did not qualify on
  CODE-001 and therefore cannot bypass patch/apply/test gates.
- Reviewer: Mistral Nemo for ordinary regression review; Qwen 14B for filesystem and
  security review. No single tested model passed both reviewer cases.
- Escalation Coder: Qwen 14B after explicit supervisor feedback; qualified on ESC-001.

Routing is qualification-aware rather than model-name authoritative. Conditional or
unqualified routes remain useful only because deterministic validation rejects unsafe
outputs and bounded escalation ends in Codex takeover.

## Context Policy

Local model 성능과 속도를 위해 전체 Repository dump를 금지한다.

Context Builder는 다음 순서로 Context를 만든다.

1. Task text
2. Git snapshot
3. Repository file inventory
4. Scout가 추천한 파일 목록
5. deterministic size limit 적용
6. 필요한 파일 내용
7. 기존 실패 feedback/evidence

기본 제한 예시:

- 최대 파일 8개
- 파일당 18K characters
- 총 Context 약 70K characters 이하
- 실제 값은 모델 Benchmark 후 조정

## Repository Isolation

원본:

`D:\team_project_os\team_project_os-main`

작업:

`D:\AI_worker\worktree\team_project_os`

AI Worker는 Git worktree를 사용한다. Candidate는 worktree에서도 Codex 승인 전 자동 적용하지 않는 것을 기본값으로 한다.

## Evidence

Evidence에는 최소 다음이 포함된다.

- Task
- Base HEAD
- Branch
- Worker model
- selected context files
- Candidate patch
- Reviewer verdict
- `git apply --check`
- 적용 후 `git diff --check`
- focused tests
- regression tests
- final commit SHA

## Safety Boundary

Architecture/Auth/Security/권한 확대, destructive migration, 자동 push/merge는 Human 또는 명시적인 승인 정책 없이는 실행하지 않는다.

단순 구현·리팩터링·테스트 보강은 승인된 Task 범위 안에서 자동 진행할 수 있다.
