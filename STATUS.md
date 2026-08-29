# AI Worker Status

## Current Phase

`V0.1 — Real E2E qualification`

## Current Task

`TASK-003 — Real Target E2E Pipeline Validation` — EXPERIMENT COMPLETED;
TARGET CHANGE PASS, LOCAL-ONLY PIPELINE ACCEPTANCE FAIL.

## Previous Task

`TASK-002 — Role-based Local Development Benchmark` — IMPLEMENTED AND VERIFIED.

## Next Task

`TASK-004 — Coder feedback contract and escalation regression qualification`.
Freeze the TASK-003 failure, improve semantic/minimal-diff gates and feedback packet
design, then require multiple escalation cases before restoring qualification.

## Current Target

- Original: `D:\team_project_os\team_project_os-main` on `main` at `3c05219`; unchanged
  apart from its pre-existing untracked `team_project_os-main.zip`
- Isolated worktree: `D:\AI_worker\worktree\team_project_os`
- Branch: `ai/team-project-os-improvement`
- Current worktree commit: `1ecbd8fa7d7a61e9b721dc115788ec52b1a37394`
- Worktree status: clean; Target push/merge/release not performed

## Current Architecture

`Codex Supervisor → deterministic Python Harness → bounded/stateless Ollama Workers
→ schema/patch/test validation → Codex final review/takeover → isolated Target worktree`.

TASK-003 required Codex takeover after both Local Coder Candidates failed. Architecture
is unchanged; the evidence narrows qualification claims rather than authorizing a rewrite.

## Current Worker Routing

- Scout: `qwen3:8b` → `qwen3.5:9b` — CONDITIONAL; real E2E file selection passed.
- Planner: `qwen3:8b` → `qwen2.5-coder:14b-instruct-q3_K_S` — UNQUALIFIED without
  independent semantic validation; both failed the TASK-003 plan.
- Coder: `qwen2.5-coder:7b` — reject-only fast Candidate; never auto-apply.
- Reviewer: Mistral Nemo ordinary regression / 14B security — CONDITIONAL and never
  authoritative; TASK-003 observed a false accept and a false revise from Mistral.
- Escalation: `qwen2.5-coder:14b-instruct-q3_K_S` — benchmark-qualified only on ESC-001;
  real E2E qualification FAILED after it repeated the fast Candidate verbatim.
- Codex takeover remains required after one bounded escalation failure.

## Latest Benchmark and E2E Evidence

- Role benchmark: `BENCH-20260829-163009`, v2, 21/21 calls, 714.23 s summed latency.
- Real E2E Evidence: `e2e_results/TASK-003/`.
- Local calls: 8; summed latency: 412.492 s; Target pipeline time: 752.320 s;
  total time through final verification: 994.164 s.
- First Candidate Acceptance: false; Escalated Candidate Acceptance: false.
- Codex material interventions: 2 / 5 functional Local stages = 40%.
- Codex direct Target code edits: 1.
- Final Target diff: one file, `+1/-1`.
- Focused Target discovery: before import failure; after 14/14 PASS.
- Full Target discovery: before 65 tests + import error; after 78/78 PASS.
- Original Target non-pollution and worktree-clean-after-commit gates: PASS.
- AI_Worker: 15/15 tests, compile, Doctor, 15 JSON files, and diff check PASS.

## Bootstrap Status

- Environment doctor: PASS
- Ollama/model inventory: VERIFIED
- Target worktree isolation: VERIFIED
- Role-based benchmark: DONE
- First real Target improvement: PRODUCT CHANGE VERIFIED
- Local-only end-to-end implementation: FAILED, Evidence retained
- Minimal Harness: IN PROGRESS

## Known Problems

- `run_task` invokes Coder even when Planner semantics conflict with the traceback.
- `revise` passed a large failed Candidate and feedback to 14B; the model repeated the
  failed patch verbatim after 192.46 s.
- Planner schema validity does not imply behavioral correctness.
- Reviewer output can be schema-invalid false accept or schema-valid false revise.
- One synthetic ESC-001 success is insufficient escalation qualification.
- `run_task` still lacks an automatic bounded state machine and focused-test execution.

## Next Experiment

Compare a minimal structured failure packet against the current full-old-patch packet on
the fixed TASK-003 case and at least one additional real-like case. Add deterministic
semantic relevance/minimal-diff gates, then select or reject 14B escalation based on
apply and exact-test Evidence.

## Acceptance Rule

Local Worker output alone never completes a Task. Completion requires deterministic
Evidence and Codex acceptance. Product-change PASS does not imply pipeline-autonomy PASS.
