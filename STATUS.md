# AI Worker Status

## Current Phase

`V0.1 — Local Coder contract qualification`

## Current Task

`TASK-004 — Coder Feedback Contract and Escalation Qualification` — IMPLEMENTED AND
VERIFIED; HARNESS IMPROVEMENT PASS, QWEN 14B QUALIFICATION FAIL.

## Previous Task

`TASK-003 — Real Target E2E Pipeline Validation` — TARGET CHANGE PASS, LOCAL-ONLY
PIPELINE ACCEPTANCE FAIL.

## Next Task

`TASK-005 — Structured Edit Candidate Experiment` — PROPOSED / NOT STARTED.
Compare exact old/new snippet output with unified diff output on the same frozen cases.

## Current Target

- Original: `D:\team_project_os\team_project_os-main` on `main` at `3c05219`; unchanged
  apart from its pre-existing untracked `team_project_os-main.zip`
- Isolated worktree: `D:\AI_worker\worktree\team_project_os`
- Branch: `ai/team-project-os-improvement`
- Worktree commit: `1ecbd8fa7d7a61e9b721dc115788ec52b1a37394`
- TASK-004 made no Target change or Target push/merge/release

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/revision/path/size/test gates → Codex review/takeover → isolated Target`.

Whole-output fences and opt-in hunk recount may be normalized deterministically, while
strict compliance remains separately measured. Normalization never bypasses semantic,
allowed-file, size, or exact-test gates.

## Current Worker Routing

- Scout: `qwen3:8b` → `qwen3.5:9b` — CONDITIONAL.
- Planner: `qwen3:8b` → Qwen 14B — UNQUALIFIED without semantic validation.
- Coder: `qwen2.5-coder:7b` — optional reject-only fast Candidate; fallback is `null`.
- Reviewer: Mistral Nemo ordinary / Qwen 14B security — CONDITIONAL, never authoritative.
- Escalation: no qualified default model.
- Qwen 14B escalation: `UNQUALIFIED_RESEARCH_ONLY`; use only in explicit multi-case
  experiments with hard gates.
- Default takeover: Codex after one rejected fast Candidate.

## Latest Benchmark and Evidence

- Run: `BENCH-20260830-102723`, suite v1, four actual Qwen 14B calls.
- Runtime: temperature 0, seed 42, context 8192, timeout 300 s, retries 0.
- Strict result: 0/4 hard-gate PASS, mean score 21.25, summed latency 79.472 s.
- Minimal feedback: 0/2; feedback plus old patch: 0/2.
- Suite v2 zero-call recount replay: 1/4 PASS; model remains unqualified.
- Gold calibration: R001 100 and R002 95, all gates PASS.
- Target baseline HEAD/hash/clean invariants: PASS before and after.
- Ollama execution observation: Qwen 14B runtime 8.4 GB, 26%/74% CPU/GPU, context 8192.

## Bootstrap Status

- Environment doctor: PASS
- Ollama/model inventory: VERIFIED
- Target worktree isolation: VERIFIED
- Role benchmark: DONE
- First real Target improvement: PRODUCT CHANGE VERIFIED
- Local-only E2E implementation: FAILED
- Multi-case escalation qualification: FAILED
- Deterministic fenced diff/recount validation: IMPLEMENTED
- Minimal Harness: IN PROGRESS

## Known Problems

- No installed Coder or Escalation model is qualified as a default.
- Unified diff generation frequently produces invalid hunk counts or wrong context.
- Old-patch context can help one regression case and anchor an unrelated edit in another.
- Planner and Reviewer semantic reliability remains conditional.
- `run_task` still invokes Coder after a semantically invalid plan and lacks an automatic
  bounded apply/test state machine.
- Ignored `state/task004-*` disposable directories remain locally after cleanup was
  policy-blocked; they are not tracked and no process is active.

## Next Experiment

Use strict JSON exact replacements (`path`, `old`, `new`) on R001/R002. The Harness must
require one unique exact old-snippet match, allowed paths, no-op rejection, changed-line
bounds, disposable apply, and exact tests before comparing with unified diff acceptance.

## Acceptance Rule

Local Worker output alone never completes a Task. A best-observed model is not a primary
unless every required hard gate passes across the frozen qualification cases.
