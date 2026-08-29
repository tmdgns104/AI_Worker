from __future__ import annotations

import subprocess
import unittest
from unittest import mock

import ai_worker


class PrepareCommandTests(unittest.TestCase):
    def test_native_command_remains_list_form(self):
        command, shell = ai_worker.prepare_command(
            ["git", "--version"], platform_name="nt"
        )

        self.assertEqual(["git", "--version"], command)
        self.assertFalse(shell)

    @mock.patch("ai_worker.shutil.which", return_value=r"C:\Program Files\Codex\codex.CMD")
    def test_windows_cmd_shim_uses_command_processor(self, _which):
        with mock.patch.dict(ai_worker.os.environ, {"COMSPEC": r"C:\Windows\System32\cmd.exe"}):
            command, shell = ai_worker.prepare_command(
                ["codex", "exec", "a task with spaces"], platform_name="nt"
            )

        expected_line = subprocess.list2cmdline(
            [r"C:\Program Files\Codex\codex.CMD", "exec", "a task with spaces"]
        )
        self.assertEqual(
            [r"C:\Windows\System32\cmd.exe", "/d", "/s", "/c", expected_line],
            command,
        )
        self.assertFalse(shell)

    def test_empty_list_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            ai_worker.prepare_command([])


class OllamaModelNamesTests(unittest.TestCase):
    def test_extracts_names_from_table(self):
        output = """NAME              ID          SIZE
qwen3:4b          abc123      2.5 GB
coder:model       def456      4.7 GB
"""

        self.assertEqual(
            {"qwen3:4b", "coder:model"}, ai_worker.ollama_model_names(output)
        )

    def test_empty_output_has_no_models(self):
        self.assertEqual(set(), ai_worker.ollama_model_names(""))


if __name__ == "__main__":
    unittest.main()
