# AI Worker Status

## Current Phase

`V0.1 — Bootstrap / Local Worker Harness`

## Current Task

`TASK-002 — Role-based Local Development Benchmark` — IMPLEMENTED AND VERIFIED

## Previous Task

`TASK-001 — Windows Doctor Readiness` — IMPLEMENTED AND VERIFIED.

## Next Task

Run one small real `team_project_os` improvement through Scout → Planner → Coder →
Reviewer → Codex using the conditional routing and hard gates proven here.

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
- Local `D:\AI_worker` checkout: VERIFIED (clean baseline before TASK-002)
- Environment doctor: PASS
- Ollama connectivity: VERIFIED (`0.33.1`, seven installed models)
- Git worktree bootstrap: VERIFIED
- First model benchmark: DONE (`BENCH-20260829-163009`, v2, 21 slots)
- First real `team_project_os` improvement Task: NOT STARTED

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/test validation → Codex final review → isolated Target worktree`.

No Architecture change was required for TASK-001.

## Current Worker Routing

- Scout: `qwen3:8b` → `qwen3.5:9b` — CONDITIONAL; deterministic path/context gate.
- Planner: `qwen3:8b` → `qwen2.5-coder:14b-instruct-q3_K_S` — CONDITIONAL;
  behavior semantics require independent validation.
- Coder: `qwen2.5-coder:7b` fast candidate → 14B feedback escalation —
  UNQUALIFIED one-shot; never auto-apply.
- Reviewer: `mistral-nemo:12b-instruct-2407-q3_K_S` for ordinary regression review;
  14B for filesystem/security review — CONDITIONAL SPLIT.
- Escalation Coder: `qwen2.5-coder:14b-instruct-q3_K_S` — QUALIFIED on ESC-001.

No single installed model qualified across every tested case for Scout, Planner, Coder,
or Reviewer. Hard gates and Codex takeover remain mandatory.

## Latest Evidence

- `python ai_worker.py doctor`: PASS
- Windows `codex.CMD` invocation: PASS (`codex-cli 0.150.1`)
- `python -m unittest discover -s tests -v`: 5/5 PASS
- `python -m py_compile ai_worker.py`: PASS
- Target worktree: clean `ai/team-project-os-improvement` at
  `3c05219d50a51f2bdad8e6671e702e8c5d575e50`
- Original Target remained on `main`; its pre-existing untracked
  `team_project_os-main.zip` was not modified.
- Benchmark v1: 21 slots retained; exposed a Planner false pass and invalid focused-test
  command, so it is diagnostic only.
- Benchmark v2: 21/21 requests completed, 714.23 seconds summed request latency.
- Escalation 14B: 95 points, `git apply --check` PASS, exact focused test PASS.
- Target before/after: clean at `3c05219`; five source hashes unchanged.
- AI Worker unit tests: 15/15 PASS.

## Known Problems

- `run_task` has no bounded automatic retry state machine or focused-test execution.
- No real Target candidate has yet passed apply, test, and Codex acceptance.
- One-shot Coder has no qualified installed model on CODE-001.
- Target baseline `python -m unittest discover -s tests` currently has a pre-existing
  import failure for `tests.test_conversation_import_v016`; benchmark focused testing
  uses a disposable `tests/__init__.py` and an exact test name.

## Next Experiment

Use the conditional routing in one small read-first Target E2E Task. Measure candidate
acceptance, revision/escalation count, Codex intervention, and focused/regression time.

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
