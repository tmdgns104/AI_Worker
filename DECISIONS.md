# Architecture Decisions

## ADR-001 — Codex remains the Supervisor

**Status:** ACCEPTED

Local LLM은 Codex를 대체하는 최종 권위가 아니다. Codex가 Task acceptance, architecture 판단, difficult debugging, final review를 담당한다.

### Reason

작은 Local LLM에게 전체 Agent 권한과 최종 판단을 동시에 주면 tool misuse, context drift, false PASS가 실제 Repository 변경으로 이어질 위험이 크다.

---

## ADR-002 — Local models are bounded/stateless Workers

**Status:** ACCEPTED

Worker는 Harness가 제공한 제한 Context를 받아 Candidate만 생성한다.

직접 filesystem/Git/shell/network 권한을 기본 제공하지 않는다.

### Reason

작은 모델은 tool loop보다 bounded generation에서 더 예측 가능하며 Harness가 orchestration과 validation을 deterministic하게 담당할 수 있다.

---

## ADR-003 — Use an isolated Git worktree for target changes

**Status:** ACCEPTED

`D:\team_project_os\team_project_os-main`은 원본으로 유지하고, 실제 변경은 `D:\AI_worker\worktree\team_project_os`에서 진행한다.

### Reason

실험 실패와 Candidate 오류를 원본 작업 디렉터리에서 격리하기 위함이다.

---

## ADR-004 — Model selection is benchmark-driven and replaceable

**Status:** ACCEPTED

특정 Qwen/Mistral 모델을 Architecture에 고정하지 않는다.

조건:

- 무료
- 로컬 실행 가능
- 현재 PC에서 실용적인 속도/메모리
- 역할별 Benchmark에서 유효한 결과

새 모델은 동일 Task set으로 기존 역할 모델과 비교한 뒤 채택한다.

---

## ADR-005 — Sequential model execution on the current PC

**Status:** ACCEPTED

초기 V1에서는 큰 Local 모델 여러 개의 병렬 상주를 전제로 하지 않는다.

### Reason

8GB급 GPU 환경에서는 VRAM 경쟁과 모델 swap 비용 때문에 병렬화보다 순차 역할 교대가 안정적이다.

---

## ADR-006 — Evidence over self-report

**Status:** ACCEPTED

Worker가 PASS라고 말해도 완료로 판단하지 않는다.

완료 근거는 가능한 경우 다음 순서로 둔다.

1. deterministic format/schema validation
2. `git apply --check`
3. `git diff --check`
4. focused tests
5. regression tests
6. Git status/commit evidence
7. Codex final review

---

## ADR-007 — Research records are first-class project artifacts

**Status:** ACCEPTED

성공한 코드만 보존하지 않는다. 실패한 Prompt, 모델별 차이, Context 크기, inference 시간, 수정 횟수도 연구 자료로 기록한다.

### Reason

AI Worker의 핵심 자산은 단일 Harness 코드뿐 아니라 어떤 모델/Context/Orchestration 조합이 실제 개발에서 잘 작동했는지에 대한 누적 Evidence이기 때문이다.

---

## ADR-008 — Qualification-aware routing with deterministic repair

**Status:** ACCEPTED

Role routing records `QUALIFIED`, `CONDITIONAL`, and `UNQUALIFIED_FAST_ATTEMPT` instead
of assigning a false PASS to the best available model. Whole-output Markdown fences may
be deterministically extracted while strict-format compliance remains a separate metric.
Every patch still requires apply, allowed-file, and focused-test gates.

Reviewer routing may depend on defect type when the benchmark proves complementary
strengths. One bounded feedback escalation is allowed before Codex takeover.

### Reason

Benchmark v1 exposed an evaluator false pass and a broken test command. Benchmark v2
then showed that no installed model universally qualified for Scout, Planner, Coder, or
Reviewer, while Qwen 14B did qualify as feedback-driven Escalation Coder. Pretending the
highest unqualified score is a safe default would violate ADR-006.

---

## ADR-009 — Escalation qualification requires multiple cases; recount is opt-in

**Status:** ACCEPTED

A Local escalation model is not a default route until it passes every hard gate on at
least two representative cases. One benchmark pass is case-scoped evidence only. After
TASK-004, Qwen 14B remains installed as a research Candidate but is removed from the
default Coder fallback because it passed 0/4 strict and 1/4 recount-normalized slots.

The Harness may opt into `git apply --recount` only after standard apply fails and only
for an extractable patch. It records strict and recounted apply separately, then still
requires allowed paths, semantic required terms, diff-size bounds, and exact focused
tests. Recount success cannot compensate for a semantic or test failure.

### Reason

TASK-004 found one logically correct Candidate whose only defect was malformed hunk
counts; deterministic recount plus exact tests recovered it. Three other Candidates still
failed context, requirement, size, or test gates. This supports narrow repair while
rejecting both false qualification and blanket patch rewriting.

---

## ADR-010 - Structured exact edits remain experimental until semantic qualification

**Status:** ACCEPTED

The Harness may parse bounded exact `path`/`old_text`/`new_text` Candidates, validate all
preconditions before writing, apply them atomically in a disposable clone, and construct
the unified diff deterministically. This contract is not a default Coder route until
multiple representative cases pass strict schema, semantic, apply, and exact-test gates.

TASK-005 produced zero final hard-gate passes for both direct diff and structured output.
Structured output did improve deterministic application from 0/4 to 2/4, proving that
serialization is one bottleneck, but both applied edits were semantically wrong and the
other two used an empty preimage. Operational routing therefore remains unchanged.

### Reason

Deterministic assembly can safely separate a useful edit idea from patch syntax, but it
must not convert an invalid contract or incorrect behavior into a PASS. Keeping the path
experimental preserves this diagnostic value without weakening ADR-006 or ADR-009.

---

## ADR-011 - Semantic anchors are research context, not a qualified route

**Status:** ACCEPTED

The Harness may identify an edit target with a safe path, AST symbol/signature, exact
source/preimage, bounded imports, a related test symbol, and explicit behavioral
invariants. Line numbers are never the primary identity. Anchor packets remain an
experimental context contract until a model passes all frozen semantic, strict-schema,
application, generated-diff, size, and focused-test gates across representative cases.

When an evaluator defect is found after inference, preserve the original run as
diagnostic Evidence, version the evaluator/suite, and replay the immutable raw output
without new model calls. Never silently relabel the old result.

TASK-006 improved anchored deterministic apply/diff to 2/2 per model and produced one
14B semantic/test success, but strict output and final hard-gate success were 0/4. Mean
context increased 95.7%. Routing therefore remains unchanged: 7B is reject-only, there
is no qualified Local escalation, and 14B/semantic anchors are research-only.

### Reason

Deterministic structural identity can remove target/preimage ambiguity, but it cannot
substitute for behavior/data-flow understanding or strict contract compliance. The
versioned replay rule prevents evaluator fixes from rewriting historical Evidence.
