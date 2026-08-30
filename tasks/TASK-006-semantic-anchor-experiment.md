# TASK-006 - Semantic Anchor Experiment

Status: `IMPLEMENTED AND VERIFIED — ANCHOR PARTIAL IMPROVEMENT, NO QUALIFIED CODER`

## Problem

TASK-005 proved that deterministic structured-edit assembly can eliminate unified-diff
serialization failure, but both tested models still failed semantics and strict contract
compliance. R001 chose the wrong relative import; R002 used an empty preimage and encoded
the wrong total.

## Purpose

Test whether a bounded packet of explicit behavior assertions plus Harness-selected
unique anchor choices improves structured Candidate semantics without changing models,
hard gates, or Target state.

## Scope

- Reuse TASK-005 R001/R002, 7B/14B, runtime, Gold, and hard gates.
- Deterministically enumerate small unique anchor snippets from allowed context.
- Require the Worker to select an anchor ID and provide replacement text; line numbers
  remain non-authoritative.
- Keep exact preimage, atomic application, generated diff, and exact-test gates.
- Compare against TASK-005 structured results with no retries.

## Forbidden Scope

- Target product changes, new model download, fuzzy matching, architecture rewrite,
  automatic Target apply, or weakening any semantic/test gate.

## Frozen Experiment Contract

- Suite: `team-project-os-semantic-anchor-v1`
- Baseline: TASK-005 structured slots from `BENCH-20260830-111950`; no baseline rerun
- Anchored cases: R001 discovery import and R002 first-message progress regression
- Models: Qwen Coder 7B Q4_K_M and Qwen Coder 14B Q3_K_S
- Runtime: loopback Ollama, temperature 0, seed 42, context 8192, timeout 300 seconds,
  sequential execution, repetition 1, retry 0, fallback none; four new calls
- Output: TASK-005 exact structured edit JSON; structured output remains experimental
- Independent variable: deterministic AST/import anchors plus explicit behavior contract
- Anchor identity: path + AST/import identity + exact signature/preimage; never line number
- Anchor depth: target/edit anchor and at most one directly related test/production symbol
- Gold: unchanged TASK-005 R001/R002 structured Gold Candidates

### Non-compensable hard gates

1. hidden semantic ground truth passes
2. strict structured JSON contract passes
3. safe allowed path and exact unique non-empty preimage pass
4. all preconditions pass before atomic logical application
5. changed files equal the allowed scope
6. deterministic diff check, clean-clone apply, and postimage equality pass
7. changed-line limit passes
8. exact focused test passes
9. score is at least 85

The semantic evaluator independently checks expected files, target terms, required
behavior terms, and forbidden behavior. Its failure taxonomy includes
`WRONG_TARGET_SYMBOL`, `WRONG_BEHAVIOR`, `INCOMPLETE_FIX`, and `UNRELATED_CHANGE`.
Mechanical or focused-test success cannot compensate for semantic failure.

## Comparison Metrics

- semantic, strict contract, deterministic apply, generated diff, focused test, hard PASS
- latency and bounded context characters
- per-model anchored-minus-baseline context delta and percentage
- raw Candidate, model digest/quantization, retry, and Target before/after invariants

## Actual Execution

- Actual model run: `BENCH-20260830-115232`, suite v1, four calls
- Corrected evaluator replay: `REPLAY-20260830-115613`, suite v2, zero calls
- Requests: 4/4; retries: 0; summed inference latency: 45.975 seconds
- Gold calibration: R001/R002 score 100, every hard gate PASS
- Target baseline HEAD/hash/clean invariants: PASS before and after
- Mean context: 3,034.5 baseline chars → 5,938.5 anchored chars, +95.7%
- R001 context: 929 → 2,214 chars, +138.32%
- R002 context: 5,140 → 9,663 chars, +88.0%

Suite v1 term matching falsely marked 7B R002 semantic PASS even though
`after_cursor=1` excluded the only cursor-1 message and the focused test failed. That
run remains diagnostic Evidence. Suite v2 added a deterministic AST data-flow check and
replayed the identical raw with no model calls; no v1 result was silently relabeled.

## Final Comparison

| Model | Context | Semantic | Strict contract | Apply/diff | Focused test | Hard PASS | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|
| 7B | TASK-005 bounded | 0/2 | 0/2 | 1/2 | 0/2 | 0/2 | 2.491 s |
| 7B | semantic anchor | 0/2 | 0/2 | 2/2 | 0/2 | 0/2 | 4.838 s |
| 14B | TASK-005 bounded | 0/2 | 0/2 | 1/2 | 0/2 | 0/2 | 9.103 s |
| 14B | semantic anchor | 1/2 | 0/2 | 2/2 | 1/2 | 0/2 | 18.150 s |

### Failure slices

- 7B R001 ignored the no-relative-prefix contract and repeated the wrong relative import.
- 7B R002 used the correct anchor/preimage and required assertion strings, but
  `after_cursor=1` excluded the only message. v2 classifies `MISUNDERSTOOD_DATA_FLOW`.
- 14B R001 generated the correct semantic edit and passed focused discovery. Its fenced
  JSON violated the pre-frozen strict contract, so the 85-point Candidate did not PASS.
- 14B R002 used two messages and asserted total 2, violating the explicit one-message,
  total-1 behavior. It failed semantic and focused-test gates.
- Every output used Markdown fences; strict structured compliance remained 0/4.

## Qualification and Routing

`TASK PASS — MODEL QUALIFICATION FAIL`

```text
7B:              UNQUALIFIED
14B:             UNQUALIFIED_RESEARCH_ONLY
Semantic Anchor: PARTIAL_RESEARCH_EVIDENCE_NOT_DEFAULT
Default Coder:   7B reject-only Candidate -> deterministic gates -> Codex
Escalation:      no qualified default
```

Anchor identity improved mechanical success for both models and semantic/test success for
one 14B case, but doubled mean context and did not produce a model that passed both cases.
No Target change, new model, retry, or gate relaxation occurred.

## Completion Evidence

1. Anchor contract and AST/import Builder — PASS
2. Builder tests for function/async/method/nested/duplicate/missing/syntax/budget/path — PASS
3. Adversarial semantic evaluator tests — PASS
4. TASK-005 baseline versus anchored comparison — PASS
5. Actual 7B and 14B execution — PASS
6. Semantic/apply/diff/test/latency/context measurements — PASS
7. Qualification decision — PASS; both models FAIL qualification
8. Target before/after non-pollution — PASS
9. AI_Worker unit tests — PASS, 42/42
10. Python compile — PASS
11. Doctor — PASS
12. JSON/JSONL parse — PASS, 26 files and 8 JSONL rows checked
13. High-confidence secret scan — PASS, 0 matches
14. `git diff --check` — PASS
15. Original Target, worktree, and frozen baseline protection — PASS; worktree `1ecbd8f`
    clean, frozen baseline `3c05219` clean, original only has the pre-existing ZIP
16. Global `context-engineering` Skill update and UTF-8 validator — PASS
17. Commit and GitHub push — recorded by the enclosing logical commit/history

## Next Task

`TASK-007 — Behavior-Vector Task Decomposition Experiment` is proposed but not started.
Keep models, Anchor Builder, exact-edit gates, and R002 fixed; separate behavior-scenario
construction from code generation so the Coder receives a deterministic data vector
(eligible cursors, cursor boundary, content length, limit, expected selection, total)
without receiving answer code. Do not add a new model in the same first experiment.
