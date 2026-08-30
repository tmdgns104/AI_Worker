# TASK-006 - Behavior Assertion and Harness-Provided Anchor Experiment

Status: `PROPOSED / NOT STARTED`

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
