# AI Worker Status

## Current Phase

`V0.1 — Local Coder semantic and contract qualification`

## Current Task

`TASK-006 — Semantic Anchor Experiment` — IMPLEMENTED AND VERIFIED; HARNESS
EXPERIMENT PASS, ANCHOR PARTIAL IMPROVEMENT, MODEL QUALIFICATION FAIL.

## Previous Task

`TASK-005 — Structured Edit Candidate Experiment` — HARNESS EXPERIMENT PASS,
STRUCTURED CONTRACT AND MODEL QUALIFICATION FAIL.

## Next Task

`TASK-007 — Behavior-Vector Task Decomposition Experiment` — PROPOSED / NOT STARTED.
Reuse R002, models, anchors, transport, and hard gates while isolating data-flow
decomposition from model and output-contract changes.

## Current Target

- Original: `D:\team_project_os\team_project_os-main` on `main` at `3c05219`; unchanged
  apart from its pre-existing untracked `team_project_os-main.zip`
- Isolated worktree: `D:\AI_worker\worktree\team_project_os`
- Branch: `ai/team-project-os-improvement`
- Worktree commit: `1ecbd8fa7d7a61e9b721dc115788ec52b1a37394`
- TASK-006 made no Target change or Target push/merge/release

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/revision/path/size/test gates → Codex review/takeover → isolated Target`.

Whole-output fences and opt-in hunk recount may be normalized deterministically, while
strict compliance remains separately measured. Normalization never bypasses semantic,
allowed-file, size, or exact-test gates.

Structured exact edits and Semantic Anchors are experimental contracts. The Harness
validates safe paths, AST symbol identity, exact unique preimages, stale state, and all
preconditions before atomic logical application in a disposable clone. It constructs and
reapplies the diff deterministically. A versioned evaluator replay may reinterpret
immutable raw output after an evaluator defect, but never overwrites the original run.

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
- Semantic Anchor route: `PARTIAL_RESEARCH_EVIDENCE_NOT_DEFAULT`; no anchored model is
  qualified.

## Latest Benchmark and Evidence

- Actual run: `BENCH-20260830-115232`, suite `team-project-os-semantic-anchor-v1`.
- Corrected evaluator replay: `REPLAY-20260830-115613`, suite v2, zero model calls.
- Runtime: 7B and 14B, temperature 0, seed 42, context 8192, timeout 300 s,
  repetitions 1, retries 0, sequential loopback Ollama.
- Requests: 4/4; summed latency 45.975 s.
- TASK-005 baseline: each model 0/2 semantic, 1/2 deterministic apply/diff, 0/2 test.
- Anchored 7B: 0/2 semantic, 2/2 apply/diff, 0/2 test, 0/2 hard-gate PASS.
- Anchored 14B: 1/2 semantic, 2/2 apply/diff, 1/2 test, 0/2 hard-gate PASS.
- Strict JSON: 0/4 because every model response was fenced.
- Mean context: 3,034.5 baseline to 5,938.5 anchored characters, +95.7%.
- Gold calibration: R001 and R002 both 100, all gates PASS.
- Target baseline HEAD/hash/clean invariants: PASS before and after.
- Suite v1 falsely accepted 7B R002 semantics. Suite v2 added an AST data-flow check and
  replayed the same raw without new inference; v1 remains diagnostic Evidence.
- Final verification: 42/42 tests, compile, Doctor, JSON/JSONL, secret scan, Target
  invariants, and `git diff --check` PASS.

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
- Deterministic AST/import/test Semantic Anchor Builder: IMPLEMENTED
- Semantic Anchor operational qualification: FAILED; partial research evidence only
- Minimal Harness: IN PROGRESS

## Known Problems

- No installed Coder or Escalation model is qualified as a default.
- Unified diff generation frequently produces invalid hunk counts or wrong context.
- Both anchored models fenced JSON despite a strict contract.
- 7B still chose wrong R001 import semantics; both models misunderstood R002 cursor
  data flow despite explicit anchors and behavior assertions.
- Semantic Anchors nearly doubled mean context and improved only one 14B semantic/test
  case; no installed Coder passes the frozen multi-case hard gate.
- Old-patch context can help one regression case and anchor an unrelated edit in another.
- Planner and Reviewer semantic reliability remains conditional.
- `run_task` still invokes Coder after a semantically invalid plan and lacks an automatic
  bounded apply/test state machine.
- Ignored `state/task004-*` disposable directories remain locally after cleanup was
  policy-blocked; they are not tracked and no process is active.

## Next Experiment

Reuse R002 with a bounded Harness-produced behavior vector: eligible cursors,
after-cursor boundary, content length, character limit, expected selected cursors, and
expected total. Keep models, anchors, exact replacement, and gates fixed; do not provide
answer code or add a model variable.

## Acceptance Rule

Local Worker output alone never completes a Task. A best-observed model is not a primary
unless every required hard gate passes across the frozen qualification cases.
