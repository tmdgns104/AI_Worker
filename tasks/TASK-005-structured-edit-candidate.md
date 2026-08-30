# TASK-005 — Structured Edit Candidate Experiment

Status: `PROPOSED / NOT STARTED`

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
