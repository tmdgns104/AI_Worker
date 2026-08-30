from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import benchmark_runner


ROOT = Path(__file__).resolve().parents[1]


class SuiteValidationTests(unittest.TestCase):
    def test_versioned_suite_is_valid(self):
        suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "suite_v2.json")

        self.assertEqual("team-project-os-role-benchmark-v2", suite["suite_id"])
        self.assertEqual(8, len(suite["cases"]))
        self.assertEqual(300, suite["runtime"]["timeout_seconds"])
        self.assertEqual(["qwen3:8b", "qwen3.5:9b"], suite["candidates"]["scout"])

    def test_escalation_qualification_suite_is_valid(self):
        suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "escalation_suite_v1.json")

        self.assertEqual("team-project-os-escalation-qualification-v1", suite["suite_id"])
        self.assertEqual(4, len(suite["cases"]))
        self.assertEqual(
            {"minimal_feedback", "feedback_with_old_patch"},
            {case["feedback_variant"] for case in suite["cases"]},
        )

        corrected = benchmark_runner.load_suite(
            ROOT / "benchmarks" / "escalation_suite_v2.json"
        )
        self.assertTrue(all(case["allow_recount"] for case in corrected["cases"]))

    def test_structured_edit_suite_is_frozen_and_valid(self):
        suite = benchmark_runner.load_suite(
            ROOT / "benchmarks" / "structured_edit_suite_v1.json"
        )

        self.assertEqual("team-project-os-structured-edit-v1", suite["suite_id"])
        self.assertEqual(4, len(suite["cases"]))
        self.assertEqual(
            {"direct_diff", "structured_edit"},
            {case["output_contract"] for case in suite["cases"]},
        )
        self.assertEqual(
            ["qwen2.5-coder:7b", "qwen2.5-coder:14b-instruct-q3_K_S"],
            suite["candidates"]["coder"],
        )

    def test_duplicate_case_ids_are_rejected(self):
        suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "suite_v2.json")
        suite["cases"][1]["case_id"] = suite["cases"][0]["case_id"]

        with self.assertRaisesRegex(ValueError, "unique"):
            benchmark_runner.validate_suite(suite)

    def test_non_loopback_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "loopback"):
            benchmark_runner.require_loopback("https://example.com")


class DeterministicEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "suite_v2.json")
        self.files = [
            "app/conversation_import.py",
            "app/conversation_providers.py",
            "tests/test_v016_blocker_regressions.py",
            "tests/test_conversation_import_v016.py",
        ]

    def case(self, case_id):
        return next(case for case in self.suite["cases"] if case["case_id"] == case_id)

    def test_scout_gold_selection_passes(self):
        case = self.case("SCOUT-001")
        raw = json.dumps(
            {
                "files": [
                    "app/conversation_import.py",
                    "tests/test_v016_blocker_regressions.py",
                ],
                "reason": "source and focused regression",
            }
        )

        result = benchmark_runner.evaluate_scout(case, raw, self.files, 75)

        self.assertEqual(1.0, result["relevant_file_recall"])
        self.assertTrue(benchmark_runner.all_hard_gates_pass(result))

    def test_scout_invented_path_fails_hard_gate(self):
        case = self.case("SCOUT-001")
        raw = json.dumps({"files": ["invented.py"], "reason": "guess"})

        result = benchmark_runner.evaluate_scout(case, raw, self.files, 75)

        self.assertEqual(1, result["hallucination_count"])
        self.assertFalse(benchmark_runner.all_hard_gates_pass(result))

    def test_reviewer_gold_issues_score_full(self):
        case = self.case("REVIEW-001")
        raw = json.dumps(
            {
                "verdict": "REVISE",
                "issues": [
                    {
                        "id": "EMPTY_CHUNK_PROGRESS_REGRESSION",
                        "severity": "high",
                        "evidence": "the selected guard was removed",
                        "advice": "preserve first-message progress",
                    },
                    {
                        "id": "MISSING_REGRESSION_TEST",
                        "severity": "medium",
                        "evidence": "no test file changed",
                        "advice": "add the oversized-first-message test",
                    },
                ],
                "summary": "The change regresses progress and lacks coverage.",
            }
        )

        result = benchmark_runner.evaluate_reviewer(case, raw, 70)

        self.assertEqual(100.0, result["score"])
        self.assertTrue(benchmark_runner.all_hard_gates_pass(result))

    def test_markdown_json_is_extractable_but_not_strict(self):
        payload = {"files": [], "reason": "none"}
        parsed, valid, strict = benchmark_runner.json_contract(
            f"```json\n{json.dumps(payload)}\n```", "scout"
        )

        self.assertEqual(payload, parsed)
        self.assertTrue(valid)
        self.assertFalse(strict)

    def test_planner_wrong_empty_chunk_semantics_fail(self):
        case = self.case("PLAN-001")
        raw = json.dumps(
            {
                "summary": "Exclude the oversized first message.",
                "steps": ["Return an empty selection"],
                "files_to_change": ["tests/test_v016_blocker_regressions.py"],
                "tests": ["assert selected=[]"],
                "risks": [],
                "constraints": ["test-only", "focused unittest"],
                "behavior_assertions": ["selected=[]", "total remains 1"],
            }
        )

        result = benchmark_runner.evaluate_planner(case, raw, self.files, 70)

        self.assertIn("selected=[]", result["forbidden_behavior"])
        self.assertFalse(benchmark_runner.all_hard_gates_pass(result))

    def test_fenced_patch_is_extractable_but_not_strict(self):
        raw = "```diff\ndiff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n```"

        patch, strict, extractable = benchmark_runner.extract_patch(raw)

        self.assertTrue(patch.startswith("diff --git"))
        self.assertFalse(strict)
        self.assertTrue(extractable)

    def test_revision_evidence_detects_transport_normalized_repeat(self):
        old = "```diff\ndiff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n```\n"
        candidate = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"

        evidence = benchmark_runner.patch_revision_evidence(candidate, old)

        self.assertFalse(evidence["byte_identical_to_old"])
        self.assertTrue(evidence["semantically_unchanged_from_old"])

    def test_patch_size_counts_added_and_removed_lines(self):
        case = {"max_added_lines": 1, "max_changed_lines": 2}
        candidate = (
            "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        )

        evidence = benchmark_runner.patch_size_evidence(case, candidate)

        self.assertEqual(1, evidence["added_lines"])
        self.assertEqual(1, evidence["removed_lines"])
        self.assertEqual(2, evidence["changed_lines"])
        self.assertTrue(evidence["within_limit"])

    def test_opt_in_recount_repairs_only_hunk_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            benchmark_runner.run_cmd(["git", "init", "--quiet"], cwd=target, check=True)
            benchmark_runner.run_cmd(
                ["git", "config", "user.email", "benchmark@example.invalid"],
                cwd=target,
                check=True,
            )
            benchmark_runner.run_cmd(
                ["git", "config", "user.name", "Benchmark"], cwd=target, check=True
            )
            (target / "sample.py").write_text("old\n", encoding="utf-8")
            benchmark_runner.run_cmd(["git", "add", "sample.py"], cwd=target, check=True)
            benchmark_runner.run_cmd(
                ["git", "commit", "--quiet", "-m", "baseline"], cwd=target, check=True
            )
            case = {
                "allowed_files": ["sample.py"],
                "required_patch_terms": ["new"],
                "test_command": [
                    "python",
                    "-c",
                    "from pathlib import Path; assert Path('sample.py').read_text() == 'new\\n'",
                ],
                "max_added_lines": 1,
                "max_changed_lines": 2,
                "allow_recount": True,
                "ensure_test_package": False,
            }
            malformed_counts = (
                "```diff\n"
                "diff --git a/sample.py b/sample.py\n"
                "--- a/sample.py\n"
                "+++ b/sample.py\n"
                "@@ -1,2 +1,2 @@\n"
                "-old\n"
                "+new\n"
                "```"
            )

            result = benchmark_runner.evaluate_patch(case, malformed_counts, target, 85)

        self.assertFalse(result["git_apply_strict"])
        self.assertTrue(result["git_apply_recount"])
        self.assertTrue(result["format_recounted"])
        self.assertTrue(benchmark_runner.all_hard_gates_pass(result))

    def test_structured_edit_builds_and_reapplies_deterministic_diff(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            benchmark_runner.run_cmd(["git", "init", "--quiet"], cwd=target, check=True)
            benchmark_runner.run_cmd(
                ["git", "config", "user.email", "benchmark@example.invalid"],
                cwd=target,
                check=True,
            )
            benchmark_runner.run_cmd(
                ["git", "config", "user.name", "Benchmark"], cwd=target, check=True
            )
            (target / "sample.py").write_text("old\n", encoding="utf-8")
            benchmark_runner.run_cmd(["git", "add", "sample.py"], cwd=target, check=True)
            benchmark_runner.run_cmd(
                ["git", "commit", "--quiet", "-m", "baseline"], cwd=target, check=True
            )
            case = {
                "allowed_files": ["sample.py"],
                "required_patch_terms": ["new"],
                "test_command": [
                    "python",
                    "-c",
                    "from pathlib import Path; assert Path('sample.py').read_text() == 'new\\n'",
                ],
                "max_added_lines": 1,
                "max_changed_lines": 2,
                "max_edits": 1,
                "ensure_test_package": False,
            }
            raw = json.dumps(
                {
                    "edits": [
                        {"path": "sample.py", "old_text": "old", "new_text": "new"}
                    ]
                }
            )

            result = benchmark_runner.evaluate_structured_edit(case, raw, target, 85)

        self.assertTrue(result["structured_contract_correctness"])
        self.assertTrue(result["deterministic_application_correctness"])
        self.assertTrue(result["generated_diff_correctness"])
        self.assertTrue(result["focused_test_correctness"])
        self.assertTrue(benchmark_runner.all_hard_gates_pass(result))

    def test_minimal_escalation_prompt_omits_old_patch(self):
        suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "escalation_suite_v1.json")
        case = next(case for case in suite["cases"] if case["case_id"] == "ESC-R001-MIN")

        with patch.object(benchmark_runner, "render_context", return_value="bounded context"):
            _system, user, context_chars = benchmark_runner.build_prompt(case, "escalation_coder", ROOT, [])

        self.assertNotIn("OLD FAILED PATCH", user)
        self.assertIn("SUPERVISOR FEEDBACK", user)
        self.assertEqual(len("bounded context") + len(case["feedback"]), context_chars)

    def test_unqualified_model_is_not_reported_as_primary(self):
        result = {
            "role": "coder",
            "model": "candidate-model",
            "request_success": True,
            "score": 25,
            "latency_seconds": 1.0,
            "hard_gates": {"git_apply_check": False},
        }

        summary = benchmark_runner.summarize_results(self.suite, [result])

        recommendation = summary["recommendations"]["coder"]
        self.assertIsNone(recommendation["primary"])
        self.assertEqual("candidate-model", recommendation["best_observed"])

    def test_contract_summary_keeps_correctness_layers_separate(self):
        result = {
            "role": "coder",
            "model": "candidate-model",
            "candidate_format": "structured_edit",
            "request_success": True,
            "score": 90,
            "latency_seconds": 1.0,
            "semantic_correctness": True,
            "structured_contract_correctness": True,
            "deterministic_application_correctness": True,
            "generated_diff_correctness": True,
            "focused_test_correctness": True,
            "hard_gates": {"all": True},
        }

        summary = benchmark_runner.summarize_results(self.suite, [result])

        contract = summary["contract_comparison"][0]
        self.assertEqual(1, contract["semantic_passes"])
        self.assertEqual(1, contract["contract_passes"])
        self.assertEqual(1, contract["generated_diff_passes"])
        self.assertTrue(contract["qualified"])


if __name__ == "__main__":
    unittest.main()
