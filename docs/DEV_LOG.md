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
