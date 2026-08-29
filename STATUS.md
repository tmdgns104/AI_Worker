# AI Worker Status

## Current Phase

`V0.1 — Bootstrap / Local Worker Harness`

## Current Goal

Codex Supervisor가 Local Ollama Worker를 이용해 `team_project_os`의 실제 개선 Task를 수행할 수 있는 최소 Harness를 구축하고 검증한다.

## Current Target

- Repository: `D:\team_project_os\team_project_os-main`
- Isolated worktree: `D:\AI_worker\worktree\team_project_os`

## Current Model Inventory

사용자 PC에서 확인된 모델:

- `command-r7b:7b-12-2024-q4_K_M`
- `mistral-nemo:12b-instruct-2407-q3_K_S`
- `qwen2.5-coder:14b-instruct-q3_K_S`
- `qwen3.5:9b`
- `qwen3:8b`
- `qwen2.5-coder:7b`
- `qwen3:4b`

## Bootstrap Status

- GitHub Repository initialized: DONE
- Project definition: DONE
- Architecture baseline: DONE
- Codex Supervisor rules: DONE
- Research/Development logging structure: IN PROGRESS
- Minimal Harness: IN PROGRESS
- Local `D:\AI_worker` checkout: NOT VERIFIED
- Ollama connectivity: NOT VERIFIED
- Git worktree bootstrap: NOT VERIFIED
- First model benchmark: NOT STARTED
- First real `team_project_os` improvement Task: NOT STARTED

## First Validation Sequence

1. Clone/pull `AI_Worker` into `D:\AI_worker`.
2. Run environment doctor.
3. Create isolated target worktree.
4. Benchmark installed models with identical bounded tasks.
5. Select initial role routing.
6. Run one small real `team_project_os` improvement Task.
7. Codex reviews Candidate.
8. Apply only approved patch.
9. Verify with Git/Test Evidence.
10. Record results.

## Acceptance Rule

Local Worker output alone never completes a Task.
Completion requires deterministic Evidence and Codex acceptance.
