# TASK-004 — Coder Feedback Contract and Escalation Qualification

Status: `IMPLEMENTED AND VERIFIED — MODEL QUALIFICATION FAILED`

## Problem

TASK-003 proved the Target bug fix but failed Local-only E2E autonomy. The 7B fast
Candidate was corrupt and unrelated, and the 14B escalation returned the exact same
7,751-byte patch after receiving corrective feedback. A single synthetic ESC-001 pass
does not justify operational escalation qualification.

## Purpose

Determine whether the failure comes primarily from feedback packet design, old-Candidate
anchoring, missing semantic/minimal-diff gates, or model capability. Re-qualify or reject
the current escalation route using multiple fixed development cases.

## Frozen Evidence Input

- `e2e_results/TASK-003/pipeline/candidate_fast.patch`
- `e2e_results/TASK-003/pipeline/candidate_escalated.patch`
- `e2e_results/TASK-003/pipeline/supervisor_feedback.txt`
- `e2e_results/TASK-003/pipeline/bounded_context.txt`
- `e2e_results/TASK-003/metrics.json`
- TASK-002 `ESC-001` benchmark fixtures and results

## Scope

- Version a real-failure escalation regression case from TASK-003.
- Compare minimal structured failure feedback against the current feedback plus full old
  patch under identical model/runtime settings.
- Add deterministic semantic relevance, byte-identical revision, path, diff-size,
  apply, and exact focused-test gates where justified by the experiment.
- Use at least one additional real-like escalation case before qualification.
- Update routing and Evidence according to hard-gate results.

## Forbidden Scope

- A second Target product change
- Architecture rewrite or new orchestration framework
- New paid service, production action, Target push/merge/release
- Larger-model download without a failed installed-model experiment and explicit hypothesis
- Treating a formatting repair or aggregate score as compensation for failed apply/tests

## Acceptance Criteria

1. TASK-003 failure is reproducible as a stable Case without modifying the Target.
2. Feedback variants use frozen context, runtime, seed, and attempt count.
3. Byte-identical/semantically unchanged revisions are detected deterministically.
4. Every accepted Candidate passes allowed-file, apply, and exact-test hard gates in a
   disposable copy.
5. At least two escalation cases support any qualification claim.
6. Routing, research, benchmark, development, and status records match the evidence.
7. AI_Worker tests, compile, JSON, Doctor, diff check, commit, and push pass.

## Decision Rule

Restore operational 14B escalation qualification only if all tested real-like cases pass
hard gates. Otherwise keep it conditional, test a clearly motivated installed-model
alternative, or route directly to Codex after one bounded failure.

## Frozen Experiment Contract

- Suite: `team-project-os-escalation-qualification-v1`
- Baseline: clean disposable clone at `3c05219d50a51f2bdad8e6671e702e8c5d575e50`
- Model: `qwen2.5-coder:14b-instruct-q3_K_S`, installed digest recorded at run time
- Runtime: loopback Ollama, temperature 0, seed 42, context 8192, timeout 300 s
- Cases: TASK-003 import failure and ESC-001 oversized-message regression
- Variants: identical structured feedback with old patch omitted vs included
- Repetition: 1; retries: 0; fallback: none; four total model calls
- Hard gates: extractable patch, apply, allowed file, required terms, exact focused test,
  changed-line limit, meaningful revision, minimum score 85
- Qualification: all four slots pass every hard gate; missing data never passes

## Actual Execution

- Run: `BENCH-20260830-102723`
- Model calls: 4; retries: 0; fallback: none
- Model digest: `ff7e2b2086f712b6825d425ef5258234de6814b69cf4cf8b52cebcfef5a5396a`
- Summed latency: `79.472 s`; mean latency: `19.87 s`
- Strict v1: `0/4` hard-gate PASS, mean score `21.25`
- Minimal feedback: `0/2`, mean score `5.0`, mean latency `24.058 s`
- Feedback plus old patch: `0/2`, mean score `37.5`, mean latency `15.678 s`
- Target HEAD/hash/clean before and after: PASS

The four raw outputs were replayed without model calls under evaluator v2, which allows
opt-in `git apply --recount` while preserving strict-apply evidence. One Candidate
(`ESC-R002-OLD`) was recovered and passed its exact test at score 95. The other three
still failed semantic, required-term, size, apply, or exact-test gates. Result: `1/4`,
not qualified.

## Result

`TASK PASS — ESCALATION QUALIFICATION FAIL`

- TASK-003 failure is a stable `ESC-R001` Case: PASS
- Second real-like `ESC-R002` Case: PASS
- Frozen feedback variants and zero-retry execution: PASS
- Byte-identical and transport-normalized repeat detection: PASS
- Allowed-file, required-term, changed-line, apply, and exact-test gates: PASS
- Valid Gold calibration: R001 score 100 and R002 score 95, both hard-gate PASS
- Qwen 14B operational qualification: FAIL (`0/4` strict, `1/4` recount replay)
- Default routing updated to Codex takeover after a rejected fast Candidate: PASS
- New model download: not performed; prompt/patch-contract bottleneck is tested next

The initial focused Harness test command incorrectly addressed `tests` as a package and
failed before test execution. It was classified as `TEST_COMMAND_ERROR`; the repository
discovery form then passed. This tool error did not auto-pass any model result.

## Next Task

`TASK-005 — Structured Edit Candidate Experiment` is proposed but not started. Compare
exact old/new snippet output with unified diff output so deterministic Harness assembly
can eliminate hunk-count hallucination while semantic and exact-test gates remain.

## Completion Verification

- AI_Worker tests: 20/20 PASS
- Python compile: PASS
- Doctor: PASS
- Config/suite/run JSON: 11 files PASS
- `git diff --check`: PASS
- Target worktree: clean `1ecbd8f`; original: baseline `3c05219` plus existing zip only
- AI_Worker commit/push: recorded by the enclosing logical commit/history

Ignored disposable directories `state/task004-baseline`, `state/task004-recount`, and
`state/task004-recount-r002-old` remain locally because recursive cleanup was blocked by
the execution policy. They are not tracked and contain no active process.
