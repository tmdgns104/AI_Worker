# Model Benchmark

모델 선택은 인상이나 일반 Benchmark 점수보다 **이 프로젝트에서 실제로 필요한 역할 수행 능력**으로 결정한다.

## Hardware Baseline

초기 대상 PC:

- Windows
- RAM: 32GB
- GPU VRAM: 8GB class
- Runtime: Ollama

정확한 GPU/CPU/Ollama version은 첫 `doctor` 실행에서 Evidence로 기록한다.

## Installed Models — Initial Inventory

| Model | Size | Initial Role Candidate | Status |
|---|---:|---|---|
| qwen3:4b | 2.5GB | Scout / cheap analysis | NOT TESTED |
| qwen2.5-coder:7b | 4.7GB | Coder | NOT TESTED |
| qwen3:8b | 5.2GB | Planner | NOT TESTED |
| qwen3.5:9b | 6.6GB | Reviewer / Planner | NOT TESTED |
| qwen2.5-coder:14b-instruct-q3_K_S | 6.7GB | Escalation Coder | NOT TESTED |
| mistral-nemo:12b-instruct-2407-q3_K_S | 5.5GB | Alternate Reviewer | NOT TESTED |
| command-r7b:7b-12-2024-q4_K_M | 5.1GB | Search/Synthesis experiment | NOT TESTED |

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

## Benchmark Runs

아직 없음.

첫 Run부터 아래 형식을 추가한다.

```text
BENCH-YYYYMMDD-NNN
Task set:
Model:
Quantization:
Context:
Latency:
Format PASS/FAIL:
Patch check PASS/FAIL:
Codex quality score:
Notes:
Decision:
```
