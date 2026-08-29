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
