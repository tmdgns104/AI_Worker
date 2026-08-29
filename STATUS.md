# AI Worker Status

## Current Phase

`V0.1 — Bootstrap / Local Worker Harness`

## Current Task

`TASK-001 — Windows Doctor Readiness` — IMPLEMENTED AND VERIFIED

## Previous Task

Repository bootstrap and initial bounded worker harness — DONE upstream.

## Next Task

Replace the synthetic single-prompt benchmark with a small, versioned role benchmark
suite, then run the installed models under identical bounded conditions.

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
- Research/Development logging structure: DONE
- Minimal Harness: IN PROGRESS
- Local `D:\AI_worker` checkout: VERIFIED at `c1fe1f665ad7b3f5d6c8500480839426331a7a10`
- Environment doctor: PASS
- Ollama connectivity: VERIFIED (`0.33.1`, seven installed models)
- Git worktree bootstrap: VERIFIED
- First model benchmark: NOT STARTED
- First real `team_project_os` improvement Task: NOT STARTED

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/test validation → Codex final review → isolated Target worktree`.

No Architecture change was required for TASK-001.

## Current Worker Routing

- Scout: `qwen3:4b`
- Planner: `qwen3:8b`
- Coder: `qwen2.5-coder:7b`
- Reviewer: `qwen3.5:9b`
- Escalation Coder: `qwen2.5-coder:14b-instruct-q3_K_S`
- Alternate Reviewer: `mistral-nemo:12b-instruct-2407-q3_K_S`

All routes remain provisional until the role benchmark suite passes.

## Latest Evidence

- `python ai_worker.py doctor`: PASS
- Windows `codex.CMD` invocation: PASS (`codex-cli 0.150.1`)
- `python -m unittest discover -s tests -v`: 5/5 PASS
- `python -m py_compile ai_worker.py`: PASS
- Target worktree: clean `ai/team-project-os-improvement` at
  `3c05219d50a51f2bdad8e6671e702e8c5d575e50`
- Original Target remained on `main`; its pre-existing untracked
  `team_project_os-main.zip` was not modified.

## Known Problems

- The current benchmark is a synthetic JSON/file-selection smoke test, not yet the
  required role-based development benchmark.
- `run_task` has no bounded automatic retry state machine or focused-test execution.
- No real Target candidate has yet passed apply, test, and Codex acceptance.

## Next Experiment

Run a versioned benchmark packet for Scout, Planner, Coder, and Reviewer with hard
schema/patch gates, latency, context size, and retained raw Evidence.

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
