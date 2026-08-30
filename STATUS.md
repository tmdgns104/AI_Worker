# AI Worker Status

## Current Phase

`V0.1 — Local Coder semantic and contract qualification`

## Current Task

`TASK-005 — Structured Edit Candidate Experiment` — IMPLEMENTED AND VERIFIED;
HARNESS EXPERIMENT PASS, STRUCTURED CONTRACT AND MODEL QUALIFICATION FAIL.

## Previous Task

`TASK-004 — Coder Feedback Contract and Escalation Qualification` — HARNESS
IMPROVEMENT PASS, QWEN 14B QUALIFICATION FAIL.

## Next Task

`TASK-006 — Behavior Assertion and Harness-Provided Anchor Experiment` — PROPOSED /
NOT STARTED. Reuse TASK-005 cases and models while isolating semantic/context failure.

## Current Target

- Original: `D:\team_project_os\team_project_os-main` on `main` at `3c05219`; unchanged
  apart from its pre-existing untracked `team_project_os-main.zip`
- Isolated worktree: `D:\AI_worker\worktree\team_project_os`
- Branch: `ai/team-project-os-improvement`
- Worktree commit: `1ecbd8fa7d7a61e9b721dc115788ec52b1a37394`
- TASK-005 made no Target change or Target push/merge/release

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/revision/path/size/test gates → Codex review/takeover → isolated Target`.

Whole-output fences and opt-in hunk recount may be normalized deterministically, while
strict compliance remains separately measured. Normalization never bypasses semantic,
allowed-file, size, or exact-test gates.

Structured exact edits are implemented as an experimental Candidate contract. The
Harness validates safe allowed paths, exact unique preimages, stale state, and all
preconditions before atomic logical application in a disposable clone. It constructs and
reapplies the diff deterministically, but the route is not operationally qualified.

## Current Worker Routing

- Scout: `qwen3:8b` → `qwen3.5:9b` — CONDITIONAL.
- Planner: `qwen3:8b` → Qwen 14B — UNQUALIFIED without semantic validation.
- Coder: `qwen2.5-coder:7b` — optional reject-only fast Candidate; fallback is `null`.
- Reviewer: Mistral Nemo ordinary / Qwen 14B security — CONDITIONAL, never authoritative.
- Escalation: no qualified default model.
- Qwen 14B escalation: `UNQUALIFIED_RESEARCH_ONLY`; use only in explicit multi-case
  experiments with hard gates.
- Default takeover: Codex after one rejected fast Candidate.
- Structured edit route: `EXPERIMENTAL_NOT_DEFAULT`; both tested models are unqualified.

## Latest Benchmark and Evidence

- Run: `BENCH-20260830-111950`, suite `team-project-os-structured-edit-v1`.
- Runtime: 7B and 14B, temperature 0, seed 42, context 8192, timeout 300 s,
  repetitions 1, retries 0, sequential loopback Ollama.
- Requests: 8/8; summed latency 82.454 s.
- Direct diff: 0/4 hard-gate PASS, 0/4 deterministic apply, 0/4 focused test.
- Structured edit: 0/4 hard-gate PASS, 2/4 deterministic apply/diff generation,
  0/4 semantic/focused test PASS.
- Gold calibration: R001 and R002 both 100, all gates PASS.
- Target baseline HEAD/hash/clean invariants: PASS before and after.
- Diagnostic preflight `BENCH-20260830-111827` stopped before model calls on a
  CRLF-sensitive multi-line Gold anchor; corrected before the evaluated run.

## Bootstrap Status

- Environment doctor: PASS
- Ollama/model inventory: VERIFIED
- Target worktree isolation: VERIFIED
- Role benchmark: DONE
- First real Target improvement: PRODUCT CHANGE VERIFIED
- Local-only E2E implementation: FAILED
- Multi-case escalation qualification: FAILED
- Deterministic fenced diff/recount validation: IMPLEMENTED
- Structured exact edit validation and deterministic diff assembly: IMPLEMENTED
- Structured output operational qualification: FAILED
- Minimal Harness: IN PROGRESS

## Known Problems

- No installed Coder or Escalation model is qualified as a default.
- Unified diff generation frequently produces invalid hunk counts or wrong context.
- Both tested models fenced JSON despite a strict contract, chose wrong R001 import
  semantics, and used an empty R002 preimage.
- Structured assembly removes some serialization failures but does not improve final
  acceptance until semantic and focused-test gates pass.
- Old-patch context can help one regression case and anchor an unrelated edit in another.
- Planner and Reviewer semantic reliability remains conditional.
- `run_task` still invokes Coder after a semantically invalid plan and lacks an automatic
  bounded apply/test state machine.
- Ignored `state/task004-*` disposable directories remain locally after cleanup was
  policy-blocked; they are not tracked and no process is active.

## Next Experiment

Reuse R001/R002 with explicit behavior assertions and deterministic unique anchor
choices. Keep the models, runtime, exact replacement, atomic apply, diff, and test gates
fixed so the experiment isolates semantic/context and empty-preimage failures.

## Acceptance Rule

Local Worker output alone never completes a Task. A best-observed model is not a primary
unless every required hard gate passes across the frozen qualification cases.
