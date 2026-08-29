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
