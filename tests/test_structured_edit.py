from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from structured_edit import apply_exact_edits, parse_structured_candidate


class StructuredContractTests(unittest.TestCase):
    def test_strict_contract_parses(self):
        raw = json.dumps(
            {"edits": [{"path": "sample.py", "old_text": "old", "new_text": "new"}]}
        )

        payload, valid, strict, errors = parse_structured_candidate(raw)

        self.assertEqual("old", payload["edits"][0]["old_text"])
        self.assertTrue(valid)
        self.assertTrue(strict)
        self.assertEqual([], errors)

    def test_fenced_contract_is_non_strict(self):
        raw = '```json\n{"edits":[{"path":"a","old_text":"x","new_text":"y"}]}\n```'

        _payload, valid, strict, _errors = parse_structured_candidate(raw)

        self.assertTrue(valid)
        self.assertFalse(strict)

    def test_ambiguous_preimage_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.py"
            target.write_text("repeat\nrepeat\n", encoding="utf-8")
            payload = {
                "edits": [
                    {"path": "sample.py", "old_text": "repeat", "new_text": "changed"}
                ]
            }

            result = apply_exact_edits(root, payload, allowed_files=["sample.py"], max_edits=1)

            self.assertFalse(result["preconditions_valid"])
            self.assertEqual([2], result["occurrence_counts"])
            self.assertEqual("repeat\nrepeat\n", target.read_text(encoding="utf-8"))

    def test_stale_multi_edit_is_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.py"
            second = root / "second.py"
            first.write_text("old first\n", encoding="utf-8")
            second.write_text("current second\n", encoding="utf-8")
            payload = {
                "edits": [
                    {"path": "first.py", "old_text": "old first", "new_text": "new first"},
                    {"path": "second.py", "old_text": "stale second", "new_text": "new second"},
                ]
            }

            result = apply_exact_edits(
                root,
                payload,
                allowed_files=["first.py", "second.py"],
                max_edits=2,
            )

            self.assertFalse(result["atomic_application"])
            self.assertEqual("old first\n", first.read_text(encoding="utf-8"))
            self.assertEqual("current second\n", second.read_text(encoding="utf-8"))

    def test_safe_exact_edit_applies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.py"
            target.write_text("before\n", encoding="utf-8")
            payload = {
                "edits": [
                    {"path": "sample.py", "old_text": "before", "new_text": "after"}
                ]
            }

            result = apply_exact_edits(root, payload, allowed_files=["sample.py"], max_edits=1)

            self.assertTrue(result["atomic_application"])
            self.assertTrue(result["stale_state_valid"])
            self.assertEqual("after\n", target.read_text(encoding="utf-8"))

    def test_unsafe_path_and_no_op_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "sample.py"
            target.write_text("same\n", encoding="utf-8")
            unsafe = {
                "edits": [
                    {"path": "../sample.py", "old_text": "same", "new_text": "changed"}
                ]
            }
            no_op = {
                "edits": [
                    {"path": "sample.py", "old_text": "same", "new_text": "same"}
                ]
            }

            unsafe_result = apply_exact_edits(
                root, unsafe, allowed_files=["sample.py"], max_edits=1
            )
            no_op_result = apply_exact_edits(
                root, no_op, allowed_files=["sample.py"], max_edits=1
            )

            self.assertFalse(unsafe_result["path_validation"])
            self.assertFalse(no_op_result["preconditions_valid"])
            self.assertEqual("same\n", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
