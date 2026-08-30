# Research Log

AI Worker의 가설, 실험, 실패, 관찰 결과를 시간순으로 기록한다.

---

## 2026-08-29 — R-001 Initial Direction

### Question

Codex를 Supervisor로 유지하면서 Local LLM을 사용해 Codex의 반복 작업량을 줄이고 장시간 개발을 지속할 수 있는가?

### Starting Point

현재 PC에 다음 Ollama 모델이 설치되어 있다.

- command-r7b 7B Q4
- mistral-nemo 12B Q3
- qwen2.5-coder 14B Q3
- qwen3.5 9B
- qwen3 8B
- qwen2.5-coder 7B
- qwen3 4B

### Hypothesis

Local 모델에게 native agent 권한을 크게 주는 것보다 Harness가 Repository I/O와 orchestration을 담당하고 모델은 bounded/stateless Candidate 생성에 집중시키는 편이 작은 모델에서 더 안정적일 가능성이 높다.

### Proposed Roles

- Scout: 작은 빠른 모델
- Planner: 일반 reasoning 모델
- Coder: code-specialized 모델
- Reviewer: Coder와 다른 계열 또는 더 강한 일반 모델
- Escalation: 메모리 한계 내의 더 큰 모델
- Supervisor: Codex

### Important Constraint

모델 선택은 고정하지 않는다. 무료이며 현재 PC에서 실용적으로 실행되는 모델 중 실제 Benchmark가 좋은 모델을 사용한다.

### External Candidates To Test Later

- DeepSeek-Coder-V2 Lite/16B 계열
- Qwen3-Coder 30B 계열
- Devstral 24B 계열

이들은 설치 결정이 아니다. 현재 설치 모델 Benchmark에서 필요한 역할이 부족한 경우에만 다운로드/비교한다.

### Next Experiment

동일한 bounded Task packet을 현재 설치 모델들에 전달하여 다음을 측정한다.

- 응답 시간
- output format 준수율
- patch syntax 성공률
- task instruction 준수
- Codex review 결과
- revision 횟수
- 최종 test pass 여부

---

## 2026-08-29 — R-002 Actual Host Bootstrap Evidence

### Hypothesis

The initial Harness can reach the installed tools and create an isolated Target
worktree without changing the original Target working tree.

### Experiment Conditions

- Host: Windows, 32 GB RAM
- GPU: NVIDIA GeForce RTX 5070 Laptop GPU, 8151 MiB VRAM
- Git: 2.50.1.windows.1
- Codex CLI: 0.150.1
- Ollama: 0.33.1
- Target base: `main` at `3c05219d50a51f2bdad8e6671e702e8c5d575e50`

### Observation

The first doctor attempt failed before Ollama validation because Python
`CreateProcess` cannot directly execute the installed npm `codex.CMD` shim. After a
bounded command-preparation fix, doctor reported all tools and six configured role
models available. The seven-model inventory matched the expected host state.

The Target worktree was then created at the configured path on
`ai/team-project-os-improvement`, clean and at the same base HEAD. The original Target
retained its pre-existing untracked ZIP and received no experimental changes.

### Result

PASS after one implementation revision. The failure was classified as
`HARNESS_EXECUTION_FAILURE`, not a model or Target failure.

### Conclusion

Windows script-shim handling is a required deterministic Harness boundary. Environment
readiness and repository isolation are now proven on the actual host.

### Next Experiment

Version and run a role-based model benchmark with real schema and patch hard gates.

---

## 2026-08-29 — R-003 Role Benchmark v1 and Evaluator Failure

### Hypothesis

A fixed Target-grounded suite can distinguish role quality using schema, file recall,
patch apply, focused tests, and known review defects.

### Conditions

Eight Stable Cases, 21 sequential slots, loopback Ollama, temperature 0, seed 42,
8192 context, retry 0, and clean Target `3c05219`. Raw output and JSONL were retained.

### Result

The model execution completed except for one qwen3:8b Reviewer timeout. However, v1
itself failed validation: Planner keyword scoring passed semantically wrong empty-chunk
plans, Scout Gold rejected a valid alternate test location, and the focused test command
could not resolve the Target's test-module import.

### Unexpected Finding

The most dangerous false PASS came from the evaluator rather than the Local Model.
Stronger output schema compliance did not protect against incorrect behavior semantics.

### Conclusion

v1 is diagnostic Evidence only. Preserve it, create v2 instead of rewriting history,
and add multiple-valid-file Gold, explicit behavior assertions/forbidden outcomes,
whole-output fence normalization, exact new-test discovery, and timeout measurement.

---

## 2026-08-29 — R-004 Role Benchmark v2

### Hypothesis

The corrected evaluator will reject semantic false passes while still recovering safe
content from common Markdown fence format failures.

### Conditions

Same Target hashes and generation parameters as v1; 300-second timeout; 21 slots across
five installed models selected by plausible role. Patch candidates were applied only in
disposable clones. An empty disposable `tests/__init__.py` enabled exact test discovery
without changing the Target.

### Result

- All 21 requests completed; summed request latency 714.23 seconds.
- Target before/after invariants: PASS.
- Planner false behavior was correctly rejected in PLAN-001.
- No one-shot Coder qualified.
- Mistral passed ordinary regression review; Qwen 14B passed security review.
- Qwen 14B Escalation passed all gates at 95 points in 24.50 seconds.

### Hardware Observation

Ollama reported the 14B Q3 model at 8.4 GB runtime size with `26%/74% CPU/GPU` and
8192 context after execution. It is practical as sequential escalation, not evidence for
parallel residency or a universal default.

### Conclusion

The useful pattern is not “largest model wins.” A fast candidate plus deterministic
rejection and one explicit-feedback 14B escalation succeeded where one-shot 14B coding
failed. Reviewer specialization also outperformed a universal reviewer assumption.

### Next Experiment

Run one small real Target change E2E and measure first-candidate acceptance, escalation,
Codex correction, focused/regression time, and final diff quality.

---

## 2026-08-29 — R-005 Real Target E2E External-Validity Test

### Hypothesis

The TASK-002 conditional routing can finish one small real Target change without Codex
writing Target code, and the 14B escalation behavior observed in ESC-001 generalizes to
a production-like failure packet.

### Conditions

- Target: isolated `ai/team-project-os-improvement` worktree at `3c05219`
- Improvement: repair the existing blocker-test import failure under standard unittest
  discovery; one allowed test file; no production or dependency changes
- Locality: loopback Ollama, temperature 0, seed 42, sequential workers
- Pipeline: two Scout calls including discovery, primary/fallback Planner, 7B Coder,
  Mistral review, one feedback-driven 14B escalation, and final Mistral review
- Retry: zero same-prompt retries; one permitted escalation
- Before/after identical focused and full discovery commands

### Result

- Target change: PASS; focused 14/14 and full 78/78 tests passed after one `+1/-1`
  import correction committed as `1ecbd8f`.
- Pipeline autonomy: FAIL. Both Local Coder Candidates failed apply and correctness
  gates. The 14B escalation returned the 7B 7,751-byte patch verbatim after 192.46 s.
- Planner: qwen3:8b ignored the traceback; the 14B fallback identified the import but
  proposed fixture removal/reimplementation and omitted validation.
- Reviewer: Mistral first violated schema and falsely claimed tests passed, then returned
  strict JSON but falsely revised the final correct one-line patch.
- Codex direct code edits: 1; material interventions: 2; Intervention Rate: 40%.
- Eight Local calls consumed 412.492 s summed latency; task wall time through Target
  commit was 752.320 s.

### Unexpected Findings

The benchmark-qualified ESC-001 behavior did not generalize even to a smaller patch.
More feedback text and the full prior Candidate did not improve the result; the model
anchored on and repeated the failed patch. Reviewer schema compliance also did not
predict correct adjudication.

### Conclusion

TASK-002 was directionally useful for Scout and reject-only fast Coder routing, but one
synthetic escalation pass was insufficient qualification. Operationally, 14B escalation
must be treated as conditional until it passes multiple fixed real-failure cases. The
Harness should reject semantically irrelevant plans before Coder invocation and should
test feedback packet ordering/content instead of simply adding more context.

### Next Experiment

TASK-004 will freeze this failure as an escalation regression case, compare minimal
failure feedback against feedback plus the full prior patch, add semantic/minimal-diff
gates, and re-qualify the escalation route before attempting a harder Target change.

---

## 2026-08-30 — R-006 Escalation Packet and Patch-Normalization Experiment

### Hypothesis

Qwen 14B may recover TASK-003 when given a smaller structured failure packet without the
large rejected patch. If hunk-count formatting is the remaining issue, narrow recount
normalization plus exact tests may safely recover otherwise correct Candidates.

### Conditions

- Suite v1: two fixed cases, each with minimal-feedback and feedback-plus-old-patch
  variants; four sequential calls
- Model: `qwen2.5-coder:14b-instruct-q3_K_S`, digest `ff7e2b...a5396a`, Q3_K_S
- Runtime: loopback Ollama, temperature 0, seed 42, context 8192, timeout 300 s,
  repetition 1, retry 0
- Baseline: disposable clean clone at `3c05219`; model had no repository tools
- Hard gates: patch extraction, apply, allowed path, required terms, exact focused test,
  changed-line bound, meaningful revision, score 85
- Gold calibration: known correct R001/R002 patches passed at 100/95 before generation

### Result

- Strict v1: 4/4 requests completed, 79.472 s summed latency, 0/4 hard-gate PASS,
  mean score 21.25.
- Minimal feedback: 0/2, mean score 5.0, mean latency 24.058 s.
- Old patch included: 0/2, mean score 37.5, mean latency 15.678 s.
- Ollama observed 8.4 GB runtime with 26%/74% CPU/GPU and 8192 context.
- Opt-in recount v2 replay reused the same raw with zero calls and recovered R002-OLD;
  it applied, changed only the allowed test file, and passed the exact test at score 95.
- Final v2 replay: 1/4 hard-gate PASS; model remained unqualified.

### Failure Slices

- R001 minimal: relative import plus wrong hunk context; recount could not apply it.
- R001 old-patch: applied but changed an unrelated import and left the failure intact.
- R002 minimal: recount applied, but it omitted the required test name, exceeded the
  diff limit, and failed the exact test.
- R002 old-patch: correct semantics but malformed hunk counts; recount and exact test
  safely recovered it.

### Conclusion

Removing the old Candidate did not improve success. Including it improved mean score and
produced the only recoverable Candidate, but also anchored an unrelated R001 edit, so no
single packet is a safe default. The larger bottleneck is unreliable unified-diff
construction plus inconsistent semantics, not context size alone. Qwen 14B is removed
from default escalation and retained only as an unqualified research Candidate.

### Next Experiment

Compare strict structured edits (`path`, exact `old`, exact `new`) against unified diff
on the same cases. Let the Harness construct the diff deterministically, reject ambiguous
or repeated snippets, and preserve apply/path/size/exact-test gates.
