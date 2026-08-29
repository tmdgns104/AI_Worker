# TASK-002 — Role-based Local Development Benchmark

## Problem

The current `benchmark` command is a synthetic single prompt. It cannot support
evidence-based routing because it has no versioned cases, frozen runtime, role-specific
metrics, patch/test execution, intentionally defective review candidates, or stable
machine-readable results.

## Outcome Contract

- Build a versioned benchmark suite grounded in Target `team_project_os` source at a
  fixed commit and file hashes.
- Evaluate bounded Scout, Planner, Coder, Reviewer, and Escalation Coder roles.
- Compare only plausible installed candidates for each role, sequentially.
- Preserve raw model output and deterministic per-slot results.
- Apply generated patches only in disposable local clones and run focused tests there.
- Keep the configured Target worktree clean and unchanged.
- Recommend primary/fallback routing from hard-gate, quality, latency, and reliability
  Evidence; do not assume the existing routing is correct.

## Frozen Evaluation Policy

- Suite: `team-project-os-role-benchmark-v1`.
- Provider/locality: Ollama over the configured loopback HTTP endpoint only.
- Target baseline: `3c05219d50a51f2bdad8e6671e702e8c5d575e50`.
- Temperature: `0.0`; seed: `42`; repetitions: `1`; retries: `0`.
- Execution: one model request at a time; no fallback substitution.
- Timeout: 600 seconds per slot.
- Raw output, model digest/quantization, latency, prompt/output counts when available,
  and post-request `ollama ps` observation are retained.
- Missing data never auto-passes. A failed request remains a failed evaluated slot.

## Dataset

The suite contains stable cases with fixed tasks, allowed line-bounded context, Gold
files/issues, scoring rules, and deterministic checks:

- `SCOUT-001`, `SCOUT-002`
- `PLAN-001`, `PLAN-002`
- `CODE-001`
- `REVIEW-001`, `REVIEW-002`
- `ESC-001`

The cases use the actual Target inventory and source ranges. Coder/Escalation patches
are checked and tested only in disposable clones.

## Hard Gates

- All roles: request success and exact required output contract.
- Scout/Planner: no invented paths; required file/architecture constraints satisfied.
- Coder/Escalation: unified diff, `git apply --check`, only allowed files, expected
  regression-test properties, and focused tests PASS.
- Reviewer: valid issue schema, correct verdict, minimum Gold issue recall, and no
  critical Gold issue missed.
- Target baseline hashes and clean status must match before and after the run.

## Score Policy

Scores are deterministic, 0–100, and role-specific. Hard gates are non-compensable.
Role recommendation orders candidates by:

1. all hard gates / hard-gate pass rate;
2. mean score;
3. lower mean latency.

Minimum scores: Scout 75, Planner 70, Coder 80, Reviewer 70, Escalation 85.

## Architecture Impact

None. The change adds the versioned benchmark/evaluator/run-recorder responsibility
already assigned to the deterministic Harness. No model receives tools or repository
write access.

## Exclusions

- Target product changes.
- New model downloads unless installed candidates demonstrate a clear role gap.
- Automatic Target patch acceptance, merge, push, or release.
- Full model-by-role matrix.
- Replacing the existing bounded worker pipeline architecture.

## Acceptance Evidence

- Multiple installed models executed in every role category.
- `benchmark_results/<run-id>/results.jsonl` and `summary.json` retained.
- Target worktree baseline and clean status PASS before and after.
- Unit tests, Python compile, and `git diff --check` PASS.
- Role routing and required project records updated.
- One logical AI_Worker commit pushed to GitHub.

## Result

`COMPLETED — 2026-08-29`

- v1 and v2 actual Local Model runs retained with 42 total evaluated slots.
- v1 evaluator defects were preserved and corrected in a new v2 dataset.
- v2 completed 21/21 requests with machine-readable raw/JSONL/summary Evidence.
- Target HEAD/hash/clean invariants passed before and after both runs.
- Qwen 14B Escalation: 95 points, apply PASS, exact focused test PASS.
- Other roles are explicitly conditional or unqualified; no false PASS was assigned.
- AI Worker tests: 15/15 PASS; compile/doctor/JSON/diff checks PASS.
- Target product files were not modified.
