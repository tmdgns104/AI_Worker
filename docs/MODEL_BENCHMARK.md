# Model Benchmark

모델 선택은 인상이나 일반 Benchmark 점수보다 **이 프로젝트에서 실제로 필요한 역할 수행 능력**으로 결정한다.

## Hardware Baseline

확인된 대상 PC (`2026-08-29` doctor/bootstrap evidence):

- Windows
- RAM: 32GB
- GPU: NVIDIA GeForce RTX 5070 Laptop GPU
- GPU VRAM: 8151 MiB
- Runtime: Ollama 0.33.1
- Codex CLI: 0.150.1

Host GPU visibility is recorded only as inventory. Model benchmark runs must separately
observe the actual Ollama process and must not infer task acceleration from host presence.

## Installed Models — Initial Inventory

| Model | Size | Initial Role Candidate | Status |
|---|---:|---|---|
| qwen3:4b | 2.5GB | Scout / cheap analysis | V1 FAILED 0/2 |
| qwen2.5-coder:7b | 4.7GB | Coder | V2 FAILED CODE-001 |
| qwen3:8b | 5.2GB | Scout / Planner | V2 CONDITIONAL |
| qwen3.5:9b | 6.6GB | Reviewer / Planner | V2 CONDITIONAL, slow reviewer |
| qwen2.5-coder:14b-instruct-q3_K_S | 6.7GB | Escalation / security review | V2 ESC QUALIFIED |
| mistral-nemo:12b-instruct-2407-q3_K_S | 5.5GB | Regression Reviewer | V2 CONDITIONAL |
| command-r7b:7b-12-2024-q4_K_M | 5.1GB | Scout experiment | V1 FAILED 0/2 |

## Evaluation Dimensions

각 모델을 가능한 한 동일한 Prompt/Context/temperature에서 비교한다.

### Deterministic measurements

- request success/failure
- wall-clock latency
- JSON schema compliance
- unified diff parse/apply-check success
- output length
- repeated-run stability

### Task quality measurements

Codex가 최종 리뷰 시 기록한다.

- instruction following: 0–5
- code correctness: 0–5
- unnecessary change avoidance: 0–5
- repository-context understanding: 0–5
- review defect detection: 0–5
- revision count
- final focused-test result
- final regression result

## Role Selection Rule

가장 큰 모델을 자동 선택하지 않는다.

예:

- 7B Coder가 14B와 동일한 성공률이면 7B를 기본값으로 사용
- 4B Scout가 필요한 파일을 충분히 고르면 Scout는 4B 유지
- Reviewer가 Coder와 같은 실수를 반복하면 다른 계열 모델로 변경
- 대형 모델은 어려운 Task에서만 escalation

## External Free Candidates

현재 설치 모델로 부족한 역할이 확인될 때만 시험한다.

| Candidate | Reason to test | Expected concern |
|---|---|---|
| DeepSeek-Coder-V2 16B | code-specialized alternative | model size > VRAM, RAM offload likely |
| Qwen3-Coder 30B | stronger agentic coding candidate | ~19GB model, slower local inference expected |
| Devstral 24B | software-engineering focused | ~14GB model, RAM offload expected |

다운로드 자체가 채택을 의미하지 않는다.

## Frozen Runtime

- Locality: `http://127.0.0.1:11434` only
- Target: clean `3c05219d50a51f2bdad8e6671e702e8c5d575e50`
- Five source file hashes frozen and checked before/after
- temperature `0.0`, seed `42`, context `8192`
- sequential execution, repetition `1`, retry `0`, fallback `none`
- v2 timeout: 300 seconds per slot

Quantization and immutable Ollama digest are recorded in each run manifest. The 14.8B
Q3 model was observed after execution as `26%/74% CPU/GPU`, confirming partial offload;
host GPU visibility alone was not treated as task acceleration proof.

## BENCH-20260829-160540 — Suite v1 (Diagnostic, not routing authority)

- 21 slots; 20 requests completed; summed measured latency 625.21 seconds.
- One qwen3:8b Reviewer request timed out at the then-frozen 600-second limit.
- Planner appeared to pass 4/4, but raw output asserted the wrong empty-chunk behavior.
- The focused test command could not import `tests.test_conversation_import_v016`.
- Conclusion: v1 contained evaluator/test-harness defects. Results and raw output are
  retained, but routing decisions must not use its apparent Planner PASS.

## BENCH-20260829-163009 — Suite v2

- 21/21 requests completed; summed request latency 714.23 seconds.
- Target HEAD, clean state, and frozen file hashes matched before and after.
- Full machine Evidence: `benchmark_results/BENCH-20260829-163009/`.

| Role | Model | Hard gates | Mean score | Mean latency | Decision |
|---|---|---:|---:|---:|---|
| Scout | qwen3:8b Q4 | 1/2 | 64.38 | 20.89s | conditional primary |
| Scout | qwen3.5:9b Q4 | 0/2 | 56.04 | 22.99s | fallback only |
| Planner | qwen3:8b Q4 | 1/2 | 85.00 | 35.67s | conditional primary |
| Planner | qwen3.5:9b Q4 | 1/2 | 87.50 | 72.36s | too slow for equal gate rate |
| Planner | qwen2.5-coder 14B Q3 | 1/2 | 85.00 | 22.10s | fallback; fenced JSON |
| Coder | qwen2.5-coder 7B Q4 | 0/1 | 25.00 | 12.26s | unqualified fast attempt |
| Coder | qwen3.5:9b Q4 | 0/1 | 25.00 | 26.18s | not selected |
| Coder | qwen2.5-coder 14B Q3 | 0/1 | 10.00 | 37.26s | not selected one-shot |
| Reviewer | Mistral Nemo 12B Q3 | 1/2 | 62.09 | 10.77s | regression primary |
| Reviewer | qwen2.5-coder 14B Q3 | 1/2 | 45.62 | 19.58s | security primary |
| Reviewer | qwen3.5:9b Q4 | 0/2 | 63.34 | 89.42s | slow, incomplete recall |
| Escalation | qwen2.5-coder 14B Q3 | 1/1 | 95.00 | 24.50s | QUALIFIED |
| Escalation | qwen3.5:9b Q4 | 0/1 | 30.00 | 26.45s | failed apply |

### Failure slices

- Scout security case: models selected test files but omitted the authoritative provider.
- Planner chunk case: two models explicitly asserted an empty selection; 14B remained
  ambiguous. File/schema compliance did not imply behavioral correctness.
- Coder: fenced or malformed diff, wrong hunk placement, nested undiscoverable test, or
  unrelated edit prevented apply/test qualification.
- Reviewer: Mistral detected ordinary regression/test omission but missed critical file
  read; 14B detected every security issue but accepted the ordinary regression patch.
- Escalation: explicit supervisor feedback transformed the 14B result into an applicable,
  exact-test-passing patch. The same model failed as a one-shot Coder.

## Selected Routing

```text
Scout:       qwen3:8b -> qwen3.5:9b -> Codex (conditional)
Planner:     qwen3:8b -> qwen2.5-coder:14b -> Codex (semantic gate)
Coder:       qwen2.5-coder:7b fast candidate -> 14B feedback escalation -> Codex
Reviewer:    Mistral Nemo ordinary regression / Qwen 14B filesystem-security
Escalation:  qwen2.5-coder:14b (qualified on ESC-001)
```

No new model was downloaded. The installed 14B feedback path demonstrated a useful
capability before an external-model hypothesis became necessary. Broader qualification
requires more cases and the real Target E2E Task.

## TASK-003 Real E2E External Validity

The first real Target run changed the operational interpretation of TASK-002 without
rewriting its historical benchmark result.

| Role | Real E2E observation | Operational decision |
|---|---|---|
| Scout qwen3:8b | Selected the exact failing file twice; no invented path | Conditional route supported for this case |
| Planner qwen3:8b | Strict JSON but wrong root cause/plan | Semantic gate remains mandatory |
| Planner 14B fallback | Found the import but expanded to fixture reimplementation and omitted tests | Fallback remains unqualified |
| Coder 7B | Corrupt, unrelated, behavior-breaking patch | Reject-only fast attempt confirmed |
| Reviewer Mistral | Initial false ACCEPT; final false REVISE | Never authoritative; schema and deterministic gates required |
| Escalation 14B | Repeated the failed 7B patch verbatim after 192.46 s | ESC-001 qualification did not generalize; operationally conditional |

Target tests passed only after a one-line Codex takeover Candidate. Therefore the current
route remains:

```text
Scout:       qwen3:8b -> qwen3.5:9b -> Codex (conditional)
Planner:     qwen3:8b -> 14B -> Codex (both Local plans require semantic validation)
Coder:       7B reject-only candidate -> 14B conditional escalation -> Codex
Reviewer:    Mistral ordinary / 14B security, never authoritative
Escalation:  benchmark-qualified on ESC-001 only; real E2E qualification FAILED
```

No external model is downloaded yet. The next highest-value experiment is to fix the
feedback/evaluation contract and run multiple frozen escalation cases before attributing
the failure to insufficient model capacity.

## BENCH-20260830-102723 — Escalation Qualification

Frozen runtime: Qwen 14B Q3_K_S, digest `ff7e2b...a5396a`, temperature 0, seed 42,
8192 context, timeout 300 s, repetition 1, retry 0, sequential loopback Ollama.

| Case | Packet | Score | Latency | Strict apply | Exact test | Hard PASS |
|---|---|---:|---:|---|---|---|
| ESC-R001-MIN | minimal feedback | 10 | 21.194s | FAIL | not run | FAIL |
| ESC-R001-OLD | feedback + old patch | 50 | 12.809s | PASS | FAIL | FAIL |
| ESC-R002-MIN | minimal feedback | 0 | 26.922s | FAIL | not run | FAIL |
| ESC-R002-OLD | feedback + old patch | 25 | 18.547s | FAIL | not run | FAIL |

Strict result: `0/4`, mean score 21.25, mean latency 19.87 s. The Target baseline
HEAD, hashes, and clean state passed before and after.

Evaluator v2 replayed the exact raw with no model calls and opt-in hunk recount. It
recovered ESC-R002-OLD, which changed only the test file and passed the exact test at 95.
Final replay result: `1/4`; still not qualified.

### Updated Routing

```text
Coder:       qwen2.5-coder:7b optional fast Candidate -> deterministic gates -> Codex
Escalation:  no qualified default
Research:    qwen2.5-coder:14b may be tested only under multi-case hard gates
Reviewer:    unchanged conditional split; never authoritative
```

No model was downloaded. The next experiment targets output-contract reliability before
introducing another model variable.

## BENCH-20260830-111950 — Structured Edit Contract

Frozen runtime: clean disposable Target at `3c05219`, Qwen Coder 7B Q4_K_M and 14B
Q3_K_S, temperature 0, seed 42, context 8192, timeout 300 s, repetition 1, retry 0,
sequential loopback Ollama. Both structured Gold Candidates passed every gate at 100.

| Model | Contract | Hard PASS | Semantic | Deterministic apply | Generated diff | Focused test | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|
| Qwen Coder 7B | direct diff | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 7.55 s |
| Qwen Coder 7B | structured edit | 0/2 | 0/2 | 1/2 | 1/2 | 0/2 | 2.49 s |
| Qwen Coder 14B | direct diff | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 | 22.08 s |
| Qwen Coder 14B | structured edit | 0/2 | 0/2 | 1/2 | 1/2 | 0/2 | 9.10 s |

Structured output improved serialization/application but not final quality. Both models
returned fenced JSON, chose wrong relative-import semantics in R001, and used an empty
preimage with wrong total semantics in R002. There is no qualified Coder or escalation
model, and no new model was downloaded.

### Routing after TASK-005

```text
Coder:          qwen2.5-coder:7b optional reject-only Candidate -> hard gates -> Codex
Escalation:     no qualified default
Qwen 14B:       UNQUALIFIED_RESEARCH_ONLY
Structured edit: EXPERIMENTAL_NOT_DEFAULT
Reviewer:       unchanged conditional split; never authoritative
```

The next comparison changes context/anchor selection while holding models and gates fixed.
