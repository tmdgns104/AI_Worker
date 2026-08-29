# TASK-004 — Coder Feedback Contract and Escalation Qualification

Status: `PROPOSED / NOT STARTED`

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
