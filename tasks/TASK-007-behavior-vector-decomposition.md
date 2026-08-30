# TASK-007 — Behavior-Vector Task Decomposition Experiment

Status: `PROPOSED / NOT STARTED`

## Problem

TASK-006 improved exact application to 2/2 per model and produced one correct 14B case,
but both models misunderstood the R002 cursor/data-flow scenario. Mean context nearly
doubled, so adding more unstructured source is not justified.

## Purpose

Test whether separating deterministic behavior-scenario construction from structured code
generation resolves R002 data-flow mistakes without changing models or weakening gates.

## Scope

- Reuse R002, 7B/14B, Semantic Anchor Builder, exact-edit transport, runtime, and tests.
- Harness provides a bounded behavior vector: eligible cursors, after-cursor boundary,
  content length, character limit, expected selected cursors, and expected total.
- The vector states behavior, not Python implementation or replacement code.
- Compare anchored-only TASK-006 raw with anchored-plus-vector Candidates.
- Preserve strict schema, semantic AST check, exact preimage, apply/diff, and test gates.

## Forbidden Scope

- New model download, Target product change, answer code in the vector, fuzzy matching,
  retry, gate relaxation, or architecture rewrite.
