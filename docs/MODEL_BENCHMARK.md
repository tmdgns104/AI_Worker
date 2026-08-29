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
