# TASK-003 — Real Target E2E Pipeline Validation

## Purpose

Verify that the bounded Local Worker pipeline can complete one real Target change while
Codex remains the Supervisor rather than the implementation worker.

## Target

- Worktree: `D:\AI_worker\worktree\team_project_os`
- Branch: `ai/team-project-os-improvement`
- Baseline: `3c05219d50a51f2bdad8e6671e702e8c5d575e50`
- Original checkout: `D:\team_project_os\team_project_os-main` — read-only for this Task

## Selected Improvement

Make standard `unittest` discovery load and execute
`tests/test_v016_blocker_regressions.py` instead of failing while importing
`tests.test_conversation_import_v016`. Preserve production behavior and the existing
test semantics.

The primary Local Scout selected this failure as its first small, real-value candidate.
Before-change Evidence confirms that both focused discovery and the CI full-discovery
command fail with the same `ModuleNotFoundError`.

## Allowed Files

- `tests/test_v016_blocker_regressions.py`

The two relevant existing test modules may be supplied as bounded read-only context, but
only the file above may be changed.

## Forbidden Scope

- Production application or bridge code
- `.github/workflows/ci.yml`
- Dependency or configuration changes
- Test package/layout restructuring
- Architecture, authentication, security, database, deployment, merge, release, or push
- Unrelated cleanup or refactoring

## Acceptance Criteria

1. Primary Scout, Planner, fast Coder, and independent Reviewer actually run locally.
2. Failed first Candidate, if any, is classified and passed with bounded feedback to at
   most one 14B escalation attempt.
3. Final Candidate changes only the allowed file and passes patch/path/secret/diff gates.
4. Focused discovery executes the real blocker regression tests and passes.
5. Full Python unittest discovery passes with no new regression.
6. Codex performs only focused final review; Target direct code edits by Codex remain 0.
7. The Target worktree change is committed; the Target is not pushed.
8. The original checkout remains unchanged apart from its pre-existing untracked zip.
9. Stage metrics and raw Evidence are retained under `e2e_results/TASK-003/`.
10. AI_Worker records, tests, compile, doctor, diff check, commit, and push pass.

## Verification

- Before/after: `python -m unittest discover -s tests -p test_v016_blocker_regressions.py -v`
- Before/after: `python -m unittest discover -s tests -v`
- `git apply --check` before application
- Allowed-path, patch parse, unexpected-file, secret scan, and diff-size sanity gates
- Target `git diff --check`, changed-file inspection, original/worktree status and HEAD
- AI_Worker unit tests, Python compile, JSON validation, `git diff --check`, doctor

## Expected Routing

```text
Scout: qwen3:8b -> qwen3.5:9b fallback
Planner: qwen3:8b -> qwen2.5-coder:14b fallback
Coder: qwen2.5-coder:7b candidate-only
Reviewer: mistral-nemo:12b-instruct-2407-q3_K_S
Escalation: qwen2.5-coder:14b-instruct-q3_K_S
Codex: deterministic/semantic gates and focused final review
```

## Actual Routing

```text
Discovery Scout: qwen3:8b — PASS, no fallback
Pipeline Scout: qwen3:8b — PASS, one relevant file, no fallback
Planner: qwen3:8b — semantic FAIL
Planner fallback: qwen2.5-coder:14b — semantic FAIL / scope expansion
Fast Coder: qwen2.5-coder:7b — rejected, corrupt and incorrect patch
Initial Reviewer: Mistral Nemo — invalid schema and false ACCEPT
Escalation: qwen2.5-coder:14b — rejected, repeated the first bad patch verbatim
Final Reviewer: Mistral Nemo — valid schema but false REVISE
Codex takeover: one-line Candidate — deterministic gates and tests PASS
```

## Human/Codex Intervention

- Human implementation choices requested: `0`
- Codex material interventions: `2`
- Codex direct Target code edits: `1`
- Codex Intervention Rate: `40%` — 2 material interventions / 5 functional Local
  stages (Scout, Planner, Coder, Reviewer, Escalation)
- Material intervention definition: Codex changes a Local Worker implementation decision
  or supplies corrective content needed for the next Local stage. Routine hard-gate
  execution and final approval are Supervisor duties and are counted separately.
- Intervention Rate denominator: completed Local stages; numerator: material Codex
  interventions.

## Final Evidence

`EXPERIMENT COMPLETED — TASK ACCEPTANCE FAIL`

- Target improvement: **PASS**
- Pipeline completion without Codex implementation: **FAIL**
- First Candidate Acceptance: `false`
- Escalated Candidate Acceptance: `false`
- Supervisor Candidate Acceptance: `true`
- Local Worker calls: `8`; summed model latency: `412.492 s`
- Target task wall time through commit: `752.320 s`
- Total task time through final verification: `994.164 s`
- Retry count: `0`; escalation count: `1`; Local Candidates: `2`
- `git apply --check` failures: `2`
- Final diff: one file, `+1/-1`
- Focused discovery before: FAIL import; after: **14/14 PASS**
- Full discovery before: 65 tests + 1 import error; after: **78/78 PASS**
- Target commit: `1ecbd8fa7d7a61e9b721dc115788ec52b1a37394`
- Target push/merge/release: not performed
- Original checkout: baseline HEAD retained; only its pre-existing untracked zip remains
- Machine Evidence: `e2e_results/TASK-003/`

The experiment does not satisfy Acceptance Criterion 6 because Codex supplied the final
one-line Candidate. All deterministic Target gates passed, but Local-only E2E autonomy
is a verified failure rather than `UNVERIFIED`.

## Completion Checklist

1. Real Target Task selection — PASS
2. Scout / Planner / Coder / Reviewer execution — PASS (quality failures retained)
3. Required escalation execution — PASS (Candidate rejected)
4. Deterministic validation and Target apply — PASS
5. Focused test and regression — PASS
6. Original checkout non-pollution — PASS
7. Target worktree commit — PASS; no Target push
8. Metrics and raw Evidence — PASS
9. Research, development, benchmark, and status records — PASS
10. AI_Worker tests 15/15, compile, Doctor, 15 JSON files, diff check — PASS
11. AI_Worker commit and GitHub push — recorded by the enclosing logical commit/history

## Next Task

`TASK-004 — Coder feedback contract and escalation regression qualification`

Use this real failure as a fixed case. Diagnose why `revise` repeated the 7B Candidate
verbatim, add a semantic/minimal-diff gate before expensive review, and require multiple
realistic escalation cases before restoring an operational qualification claim. Do not
start TASK-004 as part of this Task.
