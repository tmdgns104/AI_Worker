# TASK-001 — Windows Doctor Readiness

## Problem

`python ai_worker.py doctor` crashes when `codex` resolves to the normal Windows
`codex.CMD` shim. The current doctor also prints inventory without producing a
deterministic readiness verdict for the Target repository, Ollama, and configured
role models.

## Requirements

- Execute Windows `.cmd` and `.bat` shims safely from list-form subprocess calls.
- Keep native executable calls in list form without a shell.
- Verify that the configured Target exists and is a Git worktree.
- Verify Ollama command connectivity and every configured role model.
- Allow the Target worktree to be absent before `bootstrap`.
- Report a clear PASS/FAIL verdict and non-zero exit on failed hard gates.

## Architecture Impact

None. This is a deterministic Harness implementation fix within the accepted
environment-doctor and repository-inspector responsibilities.

## Exclusions

- Model quality benchmarking.
- Target repository code changes.
- Local Worker prompt or routing changes.
- Target push, merge, or release.

## Acceptance Evidence

- `python -m unittest discover -s tests`
- `python -m py_compile ai_worker.py`
- `python ai_worker.py doctor`
- `git diff --check`

## Result

`COMPLETED — 2026-08-29`

- Unit tests: 5/5 PASS.
- Actual Windows doctor: PASS, including `codex.CMD`, Target Git, Ollama, and all
  configured role models.
- Target worktree: clean `ai/team-project-os-improvement` at the configured base HEAD.
- Original Target working tree: unchanged except for its pre-existing untracked ZIP.
