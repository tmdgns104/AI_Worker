from __future__ import annotations

import json
from pathlib import Path
import unittest

import benchmark_runner


ROOT = Path(__file__).resolve().parents[1]


class SuiteValidationTests(unittest.TestCase):
    def test_versioned_suite_is_valid(self):
        suite = benchmark_runner.load_suite(ROOT / "benchmarks" / "suite_v2.json")

        self.assertEqual("team-project-os-role-benchmark-v2", suite["suite_id"])
        self.assertEqual(8, len(suite["cases"]))
        self.assertEqual(300, suite["runtime"]["timeout_seconds"])
        self.assertEqual(["qwen3:8b", "qwen3.5:9b"], suite["candidates"]["scout"])

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


if __name__ == "__main__":
    unittest.main()
