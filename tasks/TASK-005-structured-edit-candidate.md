# TASK-005 — Structured Edit Candidate Experiment

Status: `IMPLEMENTED AND VERIFIED - EXPERIMENT PASS, MODEL QUALIFICATION FAIL`

## Problem

TASK-004 produced three standard-apply failures out of four. Deterministic recount
recovered one semantically correct patch, but only 1/4 Candidates passed all gates.
Unified-diff hunk construction is consuming model capability and hiding whether an edit
idea itself is useful.

## Purpose

Compare unified diff output with a bounded structured edit contract in which the Worker
returns an allowed path plus exact old/new snippets and the Harness constructs the patch.

## Scope

- Reuse TASK-004 R001/R002 context, model, seed, and hard gates.
- Define strict JSON edits with exact-match and uniqueness requirements.
- Reject missing, ambiguous, repeated, invented-path, oversized, or no-op replacements.
- Construct diffs deterministically only after validation.
- Apply and test only in disposable clones.
- Compare schema validity, edit assembly, apply, exact test, latency, and final acceptance.

## Forbidden Scope

- Target product changes
- Automatic production apply or Target push
- Fuzzy matching or LLM-authored shell commands
- New model download before the output-contract experiment is evaluated
- Architecture rewrite or new orchestration framework

## Acceptance Rule

Adopt structured edits only if they improve hard-gate pass rate without weakening exact
match, allowed-path, changed-line, apply, or exact-test requirements.

## Frozen Experiment Contract

- Suite: `team-project-os-structured-edit-v1`
- Evidence: `BENCH-20260830-111950`
- Diagnostic preflight: `BENCH-20260830-111827`, zero model calls
- Baseline: clean disposable Target clone at `3c05219`
- Cases: TASK-004 R001 import correction and R002 first-message progress regression
- Contracts: direct unified diff and strict JSON `path`/`old_text`/`new_text`
- Models: Qwen Coder 7B Q4_K_M and Qwen Coder 14B Q3_K_S
- Runtime: loopback Ollama, temperature 0, seed 42, context 8192, timeout 300 s
- Execution: sequential, one repetition, retry 0, fallback none; eight calls
- Structured hard gates: strict schema, safe allowed path, non-empty exact preimage,
  unique occurrence, all preconditions before application, atomic logical edit,
  changed-line limit, required semantics, deterministic diff check and clean-clone
  reapply, postimage match, exact focused test, score at least 85
- Missing measurements never pass; model self-report is ignored.

The first Gold preflight exposed a CRLF-sensitive multi-line Gold anchor and stopped
before any model call. The Gold Candidate was corrected before the evaluated run to use
the smallest unique single-line preimage and matching CRLF new text. Both structured
Gold Candidates then scored 100 with every hard gate passing.

## Actual Result

`TASK PASS - STRUCTURED CONTRACT AND BOTH MODELS UNQUALIFIED`

| Model | Contract | Hard gates | Semantic | Deterministic apply | Generated diff | Focused test | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen Coder 7B | direct diff | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 7.55 s |
| Qwen Coder 7B | structured | 0/2 | 0/2 | 1/2 | 1/2 | 0/2 | 2.49 s |
| Qwen Coder 14B | direct diff | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 22.08 s |
| Qwen Coder 14B | structured | 0/2 | 0/2 | 1/2 | 1/2 | 0/2 | 9.10 s |

- All 8 requests completed; summed Local latency was `82.454 s`; retries were `0`.
- Direct diff remained corrupt or semantically wrong in all four slots.
- Both R001 structured Candidates selected a unique exact preimage, applied atomically,
  and produced a clean re-applicable Harness diff, but changed the import to the wrong
  relative form and failed focused discovery.
- Both R002 structured Candidates returned fenced JSON with empty `old_text`; the exact
  preimage contract rejected them before writing. Their proposed tests also asserted
  total `2`, contrary to the required total `1`.
- Strict structured schema compliance was `0/4`; deterministic fenced JSON extraction
  was diagnostic only and did not satisfy the strict hard gate.
- Structured final hard-gate rate was `0/4`, equal to direct diff `0/4`; therefore the
  output contract is not adopted as an operational default.

## Routing Decision

```text
Coder:      qwen2.5-coder:7b reject-only fast Candidate -> deterministic gates -> Codex
Escalation: no qualified default
Qwen 14B:   UNQUALIFIED_RESEARCH_ONLY
Structured edit: EXPERIMENTAL_NOT_DEFAULT
```

Structured assembly remains useful Harness capability because it separated two valid
applications from semantic failure, but it cannot compensate for wrong behavior or an
invalid/empty preimage.

## Completion Evidence

- Separate machine Evidence and raw outputs: PASS
- Gold evaluator calibration: PASS, 2/2 at score 100
- Actual 7B/14B execution: PASS, 8/8 requests
- Direct/structured numerical comparison: PASS
- Schema/path/preimage/ambiguity/stale/atomic/diff/test gates: PASS
- Model qualification: FAIL for both models
- Target baseline/worktree/original non-pollution: PASS
- AI_Worker tests, compile, Doctor, JSON, diff check: recorded by final verification
- AI_Worker commit and GitHub push: recorded by the enclosing logical commit/history

## Next Task

`TASK-006 - Behavior Assertion and Harness-Provided Anchor Experiment` is proposed but
not started. Keep structured output, provide deterministic unique anchor choices and
explicit behavior assertions, then measure whether semantics improve without letting the
model choose an empty or ambiguous preimage. Do not change model and prompt variables in
the same first experiment.
