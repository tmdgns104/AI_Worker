from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from semantic_anchor import (
    AnchorError,
    build_anchor_packet,
    evaluate_semantic_candidate,
    extract_symbol_anchor,
)


class SemanticAnchorBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def anchor(self, symbol: str, **overrides):
        arguments = {
            "repository": self.root,
            "path": "sample.py",
            "symbol": symbol,
            "anchor_id": "A1",
            "role": "target",
            "max_source_chars": 1000,
        }
        arguments.update(overrides)
        return extract_symbol_anchor(**arguments)

    def test_extracts_function_async_method_and_nested_symbol(self):
        self.write(
            "sample.py",
            "def outer(x):\n"
            "    def nested():\n"
            "        return x\n"
            "    return nested()\n\n"
            "class Service:\n"
            "    async def run(self, value):\n"
            "        return value\n",
        )

        function = self.anchor("outer")
        nested = self.anchor("outer.nested")
        method = self.anchor("Service.run")

        self.assertEqual("function", function["kind"])
        self.assertEqual("outer.nested", nested["symbol"])
        self.assertEqual("async_method", method["kind"])
        self.assertEqual("    async def run(self, value):", method["signature"])

    def test_duplicate_bare_symbol_is_rejected(self):
        self.write(
            "sample.py",
            "class One:\n    def run(self):\n        pass\n\n"
            "class Two:\n    def run(self):\n        pass\n",
        )

        with self.assertRaisesRegex(AnchorError, "ambiguous"):
            self.anchor("run")

    def test_missing_symbol_syntax_error_budget_and_unsafe_path_are_rejected(self):
        self.write("sample.py", "def present():\n    return 'long value'\n")
        with self.assertRaisesRegex(AnchorError, "missing"):
            self.anchor("missing")
        with self.assertRaisesRegex(AnchorError, "exceeds"):
            self.anchor("present", max_source_chars=5)
        self.write("broken.py", "def broken(:\n")
        with self.assertRaisesRegex(AnchorError, "syntax error"):
            self.anchor("broken", path="broken.py")
        with self.assertRaisesRegex(AnchorError, "unsafe"):
            self.anchor("present", path="../sample.py")

    def test_packet_is_deterministic_and_extracts_import_and_test(self):
        self.write(
            "sample.py",
            "from sibling import Fixture, TOKEN\n\n"
            "class Tests:\n"
            "    def test_behavior(self):\n"
            "        self.assertTrue(True)\n",
        )
        case = {
            "semantic_anchor": {
                "anchor_type": "ast_symbol_and_import",
                "behavior_contract": {"expected": "preserve behavior"},
                "specs": [
                    {
                        "type": "import",
                        "path": "sample.py",
                        "module": "sibling",
                        "names": ["Fixture", "TOKEN"],
                        "anchor_id": "EDIT",
                        "role": "edit_target",
                    },
                    {
                        "type": "symbol",
                        "path": "sample.py",
                        "symbol": "Tests.test_behavior",
                        "anchor_id": "TEST",
                        "role": "related_test",
                        "max_source_chars": 500,
                    },
                ],
            }
        }

        first = build_anchor_packet(case, self.root)
        second = build_anchor_packet(case, self.root)

        self.assertEqual(first, second)
        self.assertEqual("from sibling import Fixture, TOKEN", first["anchors"][0]["preimage"])
        self.assertEqual("method", first["anchors"][1]["kind"])


class SemanticEvaluatorAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.truth = {
            "expected_changed_files": ["app/target.py"],
            "target_terms": ["target_symbol"],
            "required_terms": ["return correct"],
            "forbidden_terms": ["return wrong", "except Exception"],
        }

    def payload(self, path="app/target.py", text="target_symbol\nreturn correct"):
        return {"edits": [{"path": path, "old_text": "old", "new_text": text}]}

    def test_gold_semantics_pass(self):
        result = evaluate_semantic_candidate(self.truth, self.payload())
        self.assertTrue(result["semantic_correct"])

    def test_correct_symbol_wrong_behavior_fails(self):
        result = evaluate_semantic_candidate(
            self.truth, self.payload(text="target_symbol\nreturn wrong")
        )
        self.assertIn("WRONG_BEHAVIOR", result["semantic_failure_reason"])

    def test_wrong_symbol_and_incomplete_fix_fail(self):
        result = evaluate_semantic_candidate(self.truth, self.payload(text="return something"))
        self.assertIn("WRONG_TARGET_SYMBOL", result["semantic_failure_reason"])
        self.assertIn("INCOMPLETE_FIX", result["semantic_failure_reason"])

    def test_unrelated_or_test_only_change_fails(self):
        result = evaluate_semantic_candidate(self.truth, self.payload(path="tests/test_target.py"))
        self.assertIn("UNRELATED_CHANGE", result["semantic_failure_reason"])
        self.assertIn("WRONG_TARGET_SYMBOL", result["semantic_failure_reason"])

    def test_overbroad_exception_fails(self):
        result = evaluate_semantic_candidate(
            self.truth,
            self.payload(text="target_symbol\ntry:\n    return correct\nexcept Exception:\n    pass"),
        )
        self.assertIn("WRONG_BEHAVIOR", result["semantic_failure_reason"])

    def test_progress_check_rejects_cursor_that_excludes_first_message(self):
        truth = {
            "expected_changed_files": ["tests/test.py"],
            "target_terms": ["test_progress", "select_message_chunk"],
            "required_terms": ["total, 1"],
            "forbidden_terms": [],
            "semantic_check": "first_oversized_progress_test",
            "semantic_function": "test_progress",
        }
        new_text = (
            "    def test_progress(self):\n"
            "        messages = [ConversationMessage(1, 'user', 'x' * 20, '')]\n"
            "        selected, total = select_message_chunk(\n"
            "            messages, after_cursor=1, max_characters=10\n"
            "        )\n"
            "        self.assertEqual(total, 1)\n"
        )

        result = evaluate_semantic_candidate(
            truth,
            {"edits": [{"path": "tests/test.py", "old_text": "anchor", "new_text": new_text}]},
        )

        self.assertFalse(result["semantic_correct"])
        self.assertIn("MISUNDERSTOOD_DATA_FLOW", result["semantic_failure_reason"])

    def test_progress_check_accepts_one_eligible_oversized_message(self):
        truth = {
            "expected_changed_files": ["tests/test.py"],
            "target_terms": ["test_progress", "select_message_chunk"],
            "required_terms": ["total, 1"],
            "forbidden_terms": [],
            "semantic_check": "first_oversized_progress_test",
            "semantic_function": "test_progress",
        }
        new_text = (
            "    def test_progress(self):\n"
            "        messages = [ConversationMessage(1, 'user', 'x' * 20, '')]\n"
            "        selected, total = select_message_chunk(\n"
            "            messages, after_cursor=0, max_characters=10\n"
            "        )\n"
            "        self.assertEqual(total, 1)\n"
        )

        result = evaluate_semantic_candidate(
            truth,
            {"edits": [{"path": "tests/test.py", "old_text": "anchor", "new_text": new_text}]},
        )

        self.assertTrue(result["semantic_correct"])


if __name__ == "__main__":
    unittest.main()
