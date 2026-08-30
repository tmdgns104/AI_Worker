# Development Log

AI Worker 자체의 실제 구현 변경과 검증 결과를 기록한다.

---

## 2026-08-29 — D-001 Repository Bootstrap

### Added

- `README.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `DECISIONS.md`
- `STATUS.md`
- `docs/RESEARCH_LOG.md`
- `docs/DEV_LOG.md`

### Direction

`D:\AI_worker`를 Codex Supervisor + Local Worker Harness의 정식 프로젝트 Root로 사용한다.

GitHub `tmdgns104/AI_Worker`는 다음을 함께 보관한다.

- Harness source
- architecture decisions
- model benchmark
- research record
- development record
- reusable prompts/config

실행 중 생성되는 대용량 raw context와 target worktree 전체는 Git에 올리지 않는다. 필요한 Evidence만 선별 보존한다.

### Verification

GitHub initial files created.
Local Windows checkout and runtime verification remain pending.

---

## 2026-08-29 — D-002 Windows Doctor Readiness

### Task

Make the V0.1 environment doctor execute normal Windows command shims and return a
deterministic readiness verdict before Target worktree bootstrap.

### Changed

- Added Windows `.cmd`/`.bat` subprocess preparation with explicit argument quoting.
- Preserved list-form execution for native programs and existing string-command behavior.
- Added Target Git validation, Ollama connectivity/model parsing, configured-role model
  checks, and a final doctor PASS/FAIL verdict.
- Added five unit tests and a durable Task contract.
- Created the isolated Target worktree on `ai/team-project-os-improvement`.

### Reason

The initial doctor crashed on the installed npm `codex.CMD` shim with `WinError 2`, so
the documented bootstrap path could not complete on the actual Windows host.

### Verification

- `python -m unittest discover -s tests -v` — 5/5 PASS
- `python -m py_compile ai_worker.py` — PASS
- `python ai_worker.py doctor` — PASS
- `git diff --check` — PASS
- Worktree branch/HEAD/clean status — PASS
- Original Target status checked; pre-existing untracked ZIP unchanged

### Result

Environment Doctor and Target worktree bootstrap are operational. Architecture is
unchanged. Commit: `fix Windows doctor readiness` (enclosing logical commit).

### Remaining

The model benchmark and first real Target improvement remain unverified.

---

## 2026-08-29 — D-003 Versioned Role Benchmark Harness

### Task

Build and execute Target-grounded Scout, Planner, Coder, Reviewer, and Escalation Coder
benchmarks, then select Evidence-based routing.

### Changed

- Added versioned suite v1/v2, Stable Cases, frozen Target hashes/runtime, and defect
  fixtures.
- Added loopback/digest validation, line-bounded context, raw output, JSONL results,
  latency/runtime metadata, scoring, hard gates, and qualification-aware summaries.
- Added disposable-clone patch apply and exact focused-test execution.
- Added deterministic fenced JSON/diff extraction while retaining strict-format metrics.
- Added 10 benchmark/evaluator tests, bringing the AI Worker suite to 15 tests.
- Updated model routing, temperature, seed, context, Architecture decision, research,
  benchmark, and project status.

### Verification

- AI Worker unit tests — 15/15 PASS
- Python compile — PASS
- Suite/config JSON parsing — PASS
- Doctor with updated roles — PASS
- v1 model run — retained as diagnostic Evidence
- v2 model run — 21/21 requests completed
- v2 Target before/after HEAD/hash/clean gates — PASS
- Escalation disposable apply and exact focused test — PASS
- `git diff --check` — PASS

### Result

Role routing is Evidence-based and explicitly conditional where no model qualified.
Qwen 14B is qualified only for the tested feedback-driven Escalation case. Commit:
`add role-based local model benchmark` (enclosing logical commit).

### Remaining

The first real Target E2E change and broad multi-case Coder qualification remain
UNVERIFIED. Target baseline full discovery currently has one pre-existing test import
failure; this Task did not modify Target code.

---

## 2026-08-29 — D-004 Real Target E2E Validation

### Task

Run a small real `team_project_os` change through the conditional Local Worker pipeline,
measure autonomy and Candidate acceptance, apply only a validated patch, and preserve
the original checkout.

### Changed

- Added the TASK-003 contract and tracked raw/machine Evidence under
  `e2e_results/TASK-003/`.
- Classified the generated `SUPERVISOR_INBOX.md` as ignored local runtime output so a
  normal pipeline run no longer dirties the AI_Worker worktree.
- Used Local Scout discovery to select the existing unittest discovery import failure.
- Ran primary/fallback planning, 7B fast coding, independent Mistral review, and one 14B
  feedback escalation.
- Applied a one-line Supervisor takeover Candidate only after allowlist, parse, secret,
  diff-size, and apply gates passed.
- Committed the validated Target worktree change as `1ecbd8f`; no Target push occurred.
- Updated benchmark external-validity findings, research record, Task result, and status.

### Reason

V0.1 needed real Evidence for whether conditional benchmark routing could complete a
Target change without Codex implementation. The experiment exposed a concrete
escalation generalization failure rather than only producing a successful product diff.

### Verification

- Before focused/full discovery — FAIL with the same known import error
- After focused discovery — 14/14 PASS
- After full discovery — 78/78 PASS
- Final Candidate pre-apply hard gates — PASS
- Target `git diff --check` and clean state after commit — PASS
- Original Target HEAD/status invariant — PASS
- AI_Worker unit tests — 15/15 PASS
- AI_Worker Python compile — PASS
- AI_Worker Doctor — PASS
- Config/suite/E2E JSON parse — 15 files PASS
- AI_Worker `git diff --check` — PASS

### Result

Target improvement PASS; Local-only pipeline acceptance FAIL. First and escalated Local
Candidates were rejected, while the one-line Supervisor Candidate passed. Codex direct
Target edits were recorded as 1 rather than hidden.

### Remaining

TASK-004 must improve and re-qualify the escalation feedback contract using this fixed
failure case before a second, harder Target E2E attempt.

---

## 2026-08-30 — D-005 Escalation Qualification Harness

### Task

Freeze the TASK-003 escalation failure, compare feedback packet variants on two cases,
add deterministic revision/diff gates, and either qualify or reject the 14B route.

### Changed

- Added escalation qualification suites v1/v2 with four frozen slots.
- Added optional old-Candidate prompt inclusion and explicit CLI Target baseline routing.
- Added SHA/normalized revision comparison, added/removed/changed-line metrics, revision
  and diff-size hard gates, and optional test-package setup.
- Added opt-in `git apply --recount` fallback with separate strict/recount metrics and no
  relaxation of path, semantic, size, or exact-test gates.
- Added five focused evaluator tests; suite total rises from 15 to 20 tests.
- Executed and retained actual Local Model raw/results plus a zero-call v2 replay.
- Demoted 14B escalation to research-only and removed it from default Coder fallback.

### Verification

- Gold R001/R002 Candidate calibration — 100/95, all hard gates PASS
- Actual v1 run — 4/4 requests, target before/after invariant PASS
- Strict model qualification — FAIL, 0/4
- v2 recount replay — 1/4; qualification remains FAIL
- Focused evaluator tests — 15/15 PASS after one recorded test-command correction
- Python compile and suite load — PASS
- Final full tests/Doctor/JSON/diff checks — recorded in completion verification

### Result

Harness improvement PASS; model qualification FAIL. The experiment prevents a false
default escalation claim while recovering one format-only patch safely.

### Remaining

Unified diff generation remains unreliable. TASK-005 will test structured exact
replacement output and deterministic patch assembly before considering a new model.
Three ignored TASK-004 disposable directories remain under `state/` because recursive
cleanup was blocked by the execution policy; no tracked or Target state depends on them.

---

## 2026-08-30 — D-006 Structured Edit Harness and Qualification

### Task

Implement and evaluate an exact old/new Candidate contract against direct unified diff
using the frozen TASK-004 cases and the installed 7B/14B Coder models.

### Changed

- Added strict structured Candidate parsing with safe path, non-empty/no-op, unique exact
  preimage, overlap, stale-state, and max-edit validation.
- Added all-precondition-first multi-edit staging and atomic per-file replacement with
  rollback on write failure in disposable clones.
- Added deterministic diff generation, `git diff --check`, clean-clone `git apply
  --check`, reapplication, postimage hash comparison, and exact focused tests.
- Added the frozen direct/structured suite, two structured Gold Candidates, raw JSONL
  Evidence, correctness-layer summaries, and supervisor decision.
- Added focused tests for strict/fenced schema, unsafe path, ambiguity, stale atomicity,
  safe application, generated diff reapplication, and separated summary metrics.
- Recorded ADR-010, routing/status/research/benchmark updates, and proposed TASK-006.

### Verification

- Gold preflight: first run stopped with 0 model calls on CRLF anchor mismatch; retained
- Corrected Gold calibration: 2/2 at score 100, every hard gate PASS
- Actual benchmark: 8/8 requests, retry 0, Target hashes/HEAD/clean before and after PASS
- Model qualification: FAIL; direct 0/4 and structured 0/4 final hard-gate PASS
- Focused Harness tests: 24/24 PASS after one recorded wrong module-address command
- Final full tests/compile/Doctor/JSON/diff and Git checks: recorded in completion evidence

### Result

Harness experiment PASS; structured contract and both models FAIL qualification.
Deterministic assembly recovered two syntactically applicable edit ideas but focused tests
proved both semantically wrong. Operational routing remains unchanged.

### Remaining

TASK-006 should isolate semantic/context and empty-preimage failures using Harness-provided
unique anchors and explicit behavior assertions, without adding a model variable.

---

## 2026-08-30 — D-007 Semantic Anchor Builder and Qualification

### Task

Implement deterministic semantic anchors, compare anchored context with TASK-005 on the
same cases and models, and decide qualification without changing Target code.

### Changed

- Added `semantic_anchor.py` with safe AST symbol extraction, import/test anchors,
  bounded source, duplicate/missing/syntax rejection, and deterministic packets.
- Added semantic ground-truth evaluation and an R002 AST data-flow check that separates
  semantic correctness from schema, preimage, apply, generated diff, and focused test.
- Added semantic-anchor suite v1 plus evaluator-corrected v2, Gold calibration, baseline
  comparison, raw/result persistence, and a zero-model-call replay command.
- Added 11 Anchor Builder/adversarial evaluator tests and benchmark integration tests.
- Executed four Local calls, retained the v1 evaluator false pass, and replayed identical
  raw Evidence under v2 instead of overwriting historical results.
- Recorded ADR-011, updated routing/status/research/benchmark records, and proposed
  TASK-007 without starting it.

### Corrections Retained

- One initial unit assertion expected a class-method signature without source indentation;
  the test oracle was corrected because exact source intentionally preserves indentation.
- Suite v1 term matching falsely accepted 7B R002. Suite v2 added the required AST
  relationship check; replay used zero Local calls and v1 remains diagnostic Evidence.

### Verification

- Gold calibration: R001/R002 score 100, all hard gates PASS
- Actual Local run: 4/4 responses, retry 0, summed latency 45.975 seconds
- Corrected qualification replay: 0/4 hard-gate PASS; both models remain unqualified
- Target frozen baseline HEAD/hash/clean invariant: PASS before and after
- Final unit tests: 42/42 PASS
- Python compile and Doctor: PASS
- JSON/JSONL: 26 files and 8 rows parsed successfully
- High-confidence secret scan and `git diff --check`: PASS
- Target worktree `1ecbd8f` and frozen baseline `3c05219`: clean; original Target has
  only its pre-existing untracked ZIP
- Global `context-engineering` Skill received the validated reusable semantic-anchor
  selection rule; `quick_validate.py` passed under UTF-8 mode

### Result

Harness and experiment PASS; model qualification FAIL. Anchors improved mechanical
application and one 14B case, but context increased 95.7% and no model passed the frozen
multi-case hard gate. Commit: `add semantic anchor qualification experiment` (enclosing
logical commit).

### Remaining

TASK-007 should test a bounded behavior vector on R002 before adding more context or a
new model. Structured edit and semantic-anchor routes remain non-default.
