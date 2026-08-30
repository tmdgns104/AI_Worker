from __future__ import annotations

from collections import defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import tempfile
import time
import urllib.parse
import urllib.request

from ai_worker import ROOT, ollama_chat_detailed, run_cmd
from semantic_anchor import build_anchor_packet, evaluate_semantic_candidate
from structured_edit import apply_exact_edits, parse_structured_candidate


ROLE_ORDER = ["scout", "planner", "coder", "reviewer", "escalation_coder"]
JSON_CONTRACTS = {
    "scout": {"files": list, "reason": str},
    "planner": {
        "summary": str,
        "steps": list,
        "files_to_change": list,
        "tests": list,
        "risks": list,
        "constraints": list,
        "behavior_assertions": list,
    },
    "reviewer": {"verdict": str, "issues": list, "summary": str},
}
ISSUE_TAXONOMY = {
    "EMPTY_CHUNK_PROGRESS_REGRESSION": "chunk can be empty and stall cursor progress",
    "MISSING_REGRESSION_TEST": "behavior change lacks focused regression coverage",
    "ARBITRARY_FILE_READ": "caller-controlled path bypasses provider inventory",
    "UNRELATED_CACHE_CHANGE": "cache behavior changes outside the request",
    "MISSING_SECURITY_TEST": "security boundary change lacks regression coverage",
    "API_BREAK": "public interface compatibility is broken",
    "STYLE_ONLY": "non-blocking style concern only",
}


def load_suite(path: Path) -> dict:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("extends"):
        base = load_suite(path.parent / suite["extends"])
        base["suite_id"] = suite["suite_id"]
        base["schema_version"] = suite["schema_version"]
        for section in ("runtime", "minimum_scores", "candidates"):
            base[section].update(suite.get(section, {}))
        overrides = suite.get("case_overrides", {})
        for case in base["cases"]:
            case.update(overrides.get(case["case_id"], {}))
        suite = base
    validate_suite(suite)
    return suite


def validate_suite(suite: dict) -> None:
    required = {"suite_id", "schema_version", "source", "runtime", "candidates", "cases"}
    missing = sorted(required - set(suite))
    if missing:
        raise ValueError(f"suite missing keys: {missing}")
    case_ids = [case.get("case_id") for case in suite["cases"]]
    if None in case_ids or len(case_ids) != len(set(case_ids)):
        raise ValueError("case IDs must be present and unique")
    unknown_roles = sorted({case.get("role") for case in suite["cases"]} - set(ROLE_ORDER))
    if unknown_roles:
        raise ValueError(f"unknown case roles: {unknown_roles}")
    runtime = suite["runtime"]
    if runtime.get("retries") != 0 or runtime.get("repetitions") != 1:
        raise ValueError("v1 benchmark freezes retries=0 and repetitions=1")
    for case in suite["cases"]:
        output_contract = case.get("output_contract", "direct_diff")
        if output_contract not in {"direct_diff", "structured_edit"}:
            raise ValueError(f"unknown output contract: {output_contract}")
        if output_contract == "structured_edit":
            required = {"gold_candidate", "max_edits"}
            missing_case_keys = sorted(required - set(case))
            if missing_case_keys:
                raise ValueError(
                    f"structured case {case['case_id']} missing keys: {missing_case_keys}"
                )
        if case.get("context_mode") == "semantic_anchor":
            required = {"semantic_anchor", "semantic_ground_truth"}
            missing_case_keys = sorted(required - set(case))
            if missing_case_keys:
                raise ValueError(
                    f"anchored case {case['case_id']} missing keys: {missing_case_keys}"
                )


def require_loopback(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError(f"benchmark requires loopback HTTP Ollama, got {url}")


def read_ollama_inventory(url: str) -> dict[str, dict]:
    require_loopback(url)
    request = urllib.request.Request(url.rstrip("/") + "/api/tags")
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    inventory = {}
    for item in payload.get("models", []):
        name = item.get("name") or item.get("model")
        if name:
            inventory[name] = item
    return inventory


def validate_target(suite: dict, target_repo: Path) -> dict:
    head = run_cmd(["git", "rev-parse", "HEAD"], cwd=target_repo, check=True).stdout.strip()
    status = run_cmd(["git", "status", "--porcelain=v1"], cwd=target_repo, check=True).stdout
    if head != suite["source"]["head"]:
        raise RuntimeError(f"Target HEAD mismatch: expected {suite['source']['head']}, got {head}")
    if status.strip():
        raise RuntimeError("Target worktree must be clean before benchmark")

    observed_hashes = {}
    for relative, expected in suite["source"]["file_hashes"].items():
        observed = run_cmd(
            ["git", "hash-object", relative], cwd=target_repo, check=True
        ).stdout.strip()
        observed_hashes[relative] = observed
        if observed != expected:
            raise RuntimeError(
                f"Target file hash mismatch for {relative}: expected {expected}, got {observed}"
            )
    return {"head": head, "clean": True, "file_hashes": observed_hashes}


def repository_files(target_repo: Path) -> list[str]:
    output = run_cmd(["git", "ls-files"], cwd=target_repo, check=True).stdout
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def render_context(case: dict, target_repo: Path) -> str:
    sections = []
    for segment in case.get("context", []):
        path = segment["path"]
        start = int(segment["start_line"])
        end = int(segment["end_line"])
        lines = (target_repo / path).read_text(encoding="utf-8").splitlines()
        if start < 1 or end < start or end > len(lines):
            raise ValueError(f"invalid context range {path}:{start}-{end}")
        numbered = "\n".join(
            f"{line_number:04d}: {lines[line_number - 1]}"
            for line_number in range(start, end + 1)
        )
        sections.append(f"===== {path}:{start}-{end} =====\n{numbered}")
    return "\n\n".join(sections)


def json_contract(text: str, role: str) -> tuple[dict | None, bool, bool]:
    stripped = text.strip()
    strict = True
    try:
        value = json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        match = re.fullmatch(r"```(?:json)?\s*\n(.*)\n```", stripped, re.DOTALL | re.IGNORECASE)
        if not match:
            return None, False, False
        strict = False
        try:
            value = json.loads(match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            return None, False, False
    contract = JSON_CONTRACTS[role]
    if not isinstance(value, dict) or set(value) != set(contract):
        return value if isinstance(value, dict) else None, False, strict
    valid = all(isinstance(value.get(key), expected_type) for key, expected_type in contract.items())
    if role == "reviewer" and valid:
        valid = all(
            isinstance(issue, dict)
            and {"id", "severity", "evidence", "advice"}.issubset(issue)
            and all(isinstance(issue[key], str) for key in ("id", "severity", "evidence", "advice"))
            for issue in value["issues"]
        )
    return value, valid, strict


def build_prompt(case: dict, role: str, target_repo: Path, files: list[str]) -> tuple[str, str, int]:
    context = render_context(case, target_repo)
    boundary = "You have no tools, filesystem, shell, Git, or network access. Use only supplied input."
    if role == "scout":
        system = (
            f"You are a bounded repository Scout. {boundary} Return exactly one JSON object "
            'with keys "files" (array of repository paths) and "reason" (string). '
            "Never invent a path and select no more than the requested maximum."
        )
        user = (
            f"CASE: {case['case_id']}\nTASK:\n{case['task']}\n\n"
            f"MAX FILES: {case['max_selected_files']}\n\nTRACKED FILES:\n"
            + "\n".join(files)
        )
        return system, user, 0
    if role == "planner":
        system = (
            f"You are a bounded software Planner. {boundary} Return exactly one JSON object "
            'with keys "summary" (string), "steps" (array), "files_to_change" (array), '
            '"tests" (array), "risks" (array), "constraints" (array), and '
            '"behavior_assertions" (array of explicit expected outcomes). '
            "Do not assume unseen code or expand scope."
        )
        user = f"CASE: {case['case_id']}\nTASK:\n{case['task']}\n\nBOUNDED CONTEXT:\n{context}"
        return system, user, len(context)
    if role == "coder":
        if case.get("output_contract", "direct_diff") == "structured_edit":
            system = (
                f"You are a bounded coding Worker. {boundary} Return exactly one strict JSON "
                'object with key "edits". Each edit must contain exactly string keys "path", '
                '"old_text", and "new_text". Copy old_text exactly from the supplied context; '
                "it must identify one unique occurrence. Prefer the smallest unique snippet, "
                "especially one line, so newline encoding is not part of the identity. "
                "Do not use line numbers as identity, "
                "Markdown fences, unified diff syntax, explanation, or test claims."
            )
        else:
            system = (
                f"You are a bounded coding Worker. {boundary} Output only a complete unified diff "
                "for git apply, without markdown fences or explanation. Keep the change minimal and "
                "never claim tests were executed."
            )
        sections = [f"CASE: {case['case_id']}", f"TASK:\n{case['task']}"]
        newline_note = ""
        anchor_json = ""
        if case.get("output_contract") == "structured_edit":
            newline_styles = []
            for relative in case["allowed_files"]:
                data = (target_repo / relative).read_bytes()
                style = "CRLF" if b"\r\n" in data else "LF"
                newline_styles.append(f"{relative}={style}")
            newline_note = (
                "TARGET NEWLINE STYLE:\n"
                + ", ".join(newline_styles)
                + ". Encode multiline new_text with the matching JSON newline escapes."
            )
            sections.append(newline_note)
        if case.get("context_mode") == "semantic_anchor":
            packet = build_anchor_packet(case, target_repo)
            anchor_json = json.dumps(packet, ensure_ascii=False, indent=2)
            sections.append(
                "SEMANTIC ANCHOR PACKET:\n"
                "Use the edit_target preimage exactly as old_text. Anchors identify location "
                "and behavior contracts; they do not supply the implementation.\n"
                + anchor_json
            )
        if case.get("feedback"):
            sections.append(f"SUPERVISOR REQUIREMENTS:\n{case['feedback']}")
        sections.append(f"BOUNDED CONTEXT:\n{context}")
        user = "\n\n".join(sections)
        return (
            system,
            user,
            len(context)
            + len(case.get("feedback", ""))
            + len(newline_note)
            + len(anchor_json),
        )
    if role == "reviewer":
        taxonomy = "\n".join(f"- {key}: {value}" for key, value in ISSUE_TAXONOMY.items())
        patch = (ROOT / case["candidate_patch"]).read_text(encoding="utf-8")
        system = (
            f"You are a bounded independent Reviewer. {boundary} Return exactly one JSON object "
            'with keys "verdict" (ACCEPT|REVISE|REJECT), "issues" (array), and "summary" '
            '(string). Each issue must have string keys "id", "severity", "evidence", and '
            '"advice". Use only IDs from the supplied taxonomy. Do not claim tests ran.'
        )
        user = (
            f"CASE: {case['case_id']}\nTASK:\n{case['task']}\n\nISSUE TAXONOMY:\n{taxonomy}\n\n"
            f"BOUNDED CONTEXT:\n{context}\n\nCANDIDATE PATCH:\n{patch}"
        )
        return system, user, len(context) + len(patch)
    if role == "escalation_coder":
        old_patch = (ROOT / case["old_patch"]).read_text(encoding="utf-8")
        include_old_patch = case.get("include_old_patch", True)
        system = (
            f"You are a bounded escalation coding Worker. {boundary} Output only a complete "
            "replacement unified diff for git apply, without markdown fences or explanation. "
            "Address the supervisor feedback and never claim tests were executed."
        )
        sections = [
            f"CASE: {case['case_id']}",
            f"TASK:\n{case['task']}",
            f"SUPERVISOR FEEDBACK:\n{case['feedback']}",
        ]
        if include_old_patch:
            sections.append(f"OLD FAILED PATCH:\n{old_patch}")
        sections.append(f"BOUNDED CONTEXT:\n{context}")
        user = "\n\n".join(sections)
        context_chars = len(context) + len(case["feedback"])
        if include_old_patch:
            context_chars += len(old_patch)
        return system, user, context_chars
    raise ValueError(f"unsupported role: {role}")


def evaluate_scout(case: dict, raw: str, files: list[str], minimum: int) -> dict:
    payload, schema_valid, strict_schema = json_contract(raw, "scout")
    selected = payload.get("files", []) if schema_valid else []
    selected = [path for path in selected if isinstance(path, str)]
    known = set(files)
    groups = case.get("required_file_groups") or [[path] for path in case["required_files"]]
    allowed = set(case["allowed_files"])
    invented = [path for path in selected if path not in known]
    irrelevant = [path for path in selected if path in known and path not in allowed]
    recall = sum(any(path in selected for path in group) for group in groups) / len(groups)
    precision = len(allowed.intersection(selected)) / max(1, len(selected))
    extra_count = max(0, len(selected) - len(groups))
    efficiency = max(0.0, 1.0 - extra_count / max(1, case["max_selected_files"] - len(groups) + 1))
    score = round(55 * recall + 25 * precision + 15 * efficiency + 5 * strict_schema, 2)
    hard_gates = {
        "schema": schema_valid,
        "no_invented_paths": not invented,
        "required_file_recall": recall == 1.0,
        "file_limit": len(selected) <= case["max_selected_files"],
        "minimum_score": score >= minimum,
    }
    return {
        "schema_valid": schema_valid,
        "strict_schema_valid": schema_valid and strict_schema,
        "hallucination_count": len(invented),
        "selected_files": selected,
        "relevant_file_recall": round(recall, 3),
        "irrelevant_file_count": len(irrelevant),
        "invented_file_count": len(invented),
        "score": score,
        "hard_gates": hard_gates,
    }


def evaluate_planner(case: dict, raw: str, files: list[str], minimum: int) -> dict:
    payload, schema_valid, strict_schema = json_contract(raw, "planner")
    changed = payload.get("files_to_change", []) if schema_valid else []
    changed = [path for path in changed if isinstance(path, str)]
    known = set(files)
    required = set(case["required_files"])
    allowed = set(case["allowed_files"])
    invented = [path for path in changed if path not in known]
    scope_violations = [path for path in changed if path in known and path not in allowed]
    recall = len(required.intersection(changed)) / len(required)
    searchable = json.dumps(payload or {}, ensure_ascii=False).lower()
    concept_hits = [any(term.lower() in searchable for term in group) for group in case["concept_groups"]]
    concept_coverage = sum(concept_hits) / len(concept_hits)
    semantic_groups = case.get("semantic_groups", [])
    semantic_hits = [any(term.lower() in searchable for term in group) for group in semantic_groups]
    semantic_coverage = sum(semantic_hits) / len(semantic_hits) if semantic_hits else 1.0
    forbidden_hits = [
        phrase for phrase in case.get("forbidden_phrases", []) if phrase.lower() in searchable
    ]
    tests_present = bool(payload and payload.get("tests"))
    steps_present = bool(payload and payload.get("steps"))
    score = round(
        30 * recall
        + 20 * concept_coverage
        + 20 * semantic_coverage
        + 15 * tests_present
        + 10 * (not scope_violations)
        + 5 * steps_present,
        2,
    )
    hard_gates = {
        "schema": schema_valid,
        "no_invented_paths": not invented,
        "required_file_recall": recall == 1.0,
        "no_scope_expansion": not scope_violations,
        "test_strategy": tests_present,
        "semantic_expectations": semantic_coverage == 1.0,
        "no_forbidden_behavior": not forbidden_hits,
        "minimum_score": score >= minimum,
    }
    return {
        "schema_valid": schema_valid,
        "strict_schema_valid": schema_valid and strict_schema,
        "hallucination_count": len(invented),
        "files_to_change": changed,
        "required_file_recall": round(recall, 3),
        "scope_violation_count": len(scope_violations),
        "concept_coverage": round(concept_coverage, 3),
        "semantic_coverage": round(semantic_coverage, 3),
        "forbidden_behavior": forbidden_hits,
        "score": score,
        "hard_gates": hard_gates,
    }


def patch_added_lines(patch: str) -> int:
    return sum(1 for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))


def patch_removed_lines(patch: str) -> int:
    return sum(1 for line in patch.splitlines() if line.startswith("-") and not line.startswith("---"))


def extract_patch(raw: str) -> tuple[str, bool, bool]:
    """Extract one whole fenced diff while preserving strict-format evidence."""
    stripped = raw.strip()
    strict = stripped.startswith("diff --git ") and "```" not in stripped
    if strict:
        return stripped + "\n", True, True
    match = re.fullmatch(r"```(?:diff|patch)?\s*\n(.*)\n```", stripped, re.DOTALL | re.IGNORECASE)
    if not match:
        return stripped + "\n", False, False
    extracted = match.group(1).strip()
    return extracted + "\n", False, extracted.startswith("diff --git ")


def normalized_patch(patch: str) -> str:
    """Normalize only transport formatting, not code content or indentation."""
    extracted, _strict, _extractable = extract_patch(patch)
    return "\n".join(line.rstrip() for line in extracted.strip().splitlines())


def patch_revision_evidence(candidate_raw: str, old_raw: str) -> dict:
    candidate_bytes = candidate_raw.strip().encode("utf-8")
    old_bytes = old_raw.strip().encode("utf-8")
    return {
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "old_patch_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "byte_identical_to_old": candidate_bytes == old_bytes,
        "semantically_unchanged_from_old": normalized_patch(candidate_raw)
        == normalized_patch(old_raw),
    }


def patch_size_evidence(case: dict, patch: str) -> dict:
    added_lines = patch_added_lines(patch)
    removed_lines = patch_removed_lines(patch)
    changed_lines = added_lines + removed_lines
    return {
        "added_lines": added_lines,
        "removed_lines": removed_lines,
        "changed_lines": changed_lines,
        "within_limit": added_lines <= case["max_added_lines"]
        and changed_lines <= case.get("max_changed_lines", float("inf")),
    }


def evaluate_patch(case: dict, raw: str, target_repo: Path, minimum: int) -> dict:
    patch, strict_patch_format, patch_extractable = extract_patch(raw)
    required_terms = [term for term in case["required_patch_terms"] if term not in patch]
    size = patch_size_evidence(case, patch)
    revision = None
    if case.get("old_patch"):
        old_raw = (ROOT / case["old_patch"]).read_text(encoding="utf-8")
        revision = patch_revision_evidence(raw, old_raw)
    apply_ok = False
    strict_apply_ok = False
    recount_apply_ok = False
    changed_files = []
    test_exit_code = None
    test_output = ""
    apply_output = ""

    with tempfile.TemporaryDirectory(prefix="ai-worker-benchmark-") as directory:
        evaluation_repo = Path(directory) / "target"
        clone = run_cmd(
            ["git", "clone", "--quiet", "--no-hardlinks", str(target_repo), str(evaluation_repo)]
        )
        if clone.returncode != 0:
            apply_output = (clone.stdout + clone.stderr).strip()
        else:
            checkout = run_cmd(
                ["git", "checkout", "--quiet", "--detach", "HEAD"], cwd=evaluation_repo
            )
            patch_path = Path(directory) / "candidate.patch"
            patch_path.write_text(patch, encoding="utf-8")
            checked = run_cmd(["git", "apply", "--check", str(patch_path)], cwd=evaluation_repo)
            apply_output = (checked.stdout + checked.stderr).strip()
            strict_apply_ok = checkout.returncode == 0 and checked.returncode == 0
            apply_ok = strict_apply_ok
            apply_args = ["git", "apply", str(patch_path)]
            if not apply_ok and patch_extractable and case.get("allow_recount", False):
                recounted = run_cmd(
                    ["git", "apply", "--recount", "--check", str(patch_path)],
                    cwd=evaluation_repo,
                )
                recount_apply_ok = checkout.returncode == 0 and recounted.returncode == 0
                apply_ok = recount_apply_ok
                apply_args = ["git", "apply", "--recount", str(patch_path)]
                apply_output = (
                    apply_output
                    + "\n[recount]\n"
                    + recounted.stdout
                    + recounted.stderr
                ).strip()
            if apply_ok:
                applied = run_cmd(apply_args, cwd=evaluation_repo)
                apply_ok = applied.returncode == 0
                apply_output = (apply_output + "\n" + applied.stdout + applied.stderr).strip()
            if apply_ok:
                changed_output = run_cmd(
                    ["git", "diff", "--name-only"], cwd=evaluation_repo, check=True
                ).stdout
                changed_files = [line.strip().replace("\\", "/") for line in changed_output.splitlines()]
                if case.get("ensure_test_package", True):
                    (evaluation_repo / "tests" / "__init__.py").touch()
                tested = run_cmd(case["test_command"], cwd=evaluation_repo)
                test_exit_code = tested.returncode
                test_output = (tested.stdout + tested.stderr)[-4000:]

    allowed = set(case["allowed_files"])
    disallowed = [path for path in changed_files if path not in allowed]
    terms_ok = not required_terms
    size_ok = size["within_limit"]
    meaningful_revision = not (
        revision and revision["semantically_unchanged_from_old"]
    )
    test_ok = test_exit_code == 0
    score = round(
        20 * apply_ok
        + 20 * (apply_ok and bool(changed_files) and not disallowed)
        + 15 * terms_ok
        + 30 * test_ok
        + 10 * size_ok
        + 5 * strict_patch_format,
        2,
    )
    hard_gates = {
        "patch_extractable": patch_extractable,
        "git_apply_check": apply_ok,
        "allowed_files_only": apply_ok and bool(changed_files) and not disallowed,
        "required_patch_terms": terms_ok,
        "focused_test": test_ok,
        "diff_size": size_ok,
        "minimum_score": score >= minimum,
    }
    if case.get("require_revision_change"):
        hard_gates["meaningful_revision"] = meaningful_revision
    return {
        "candidate_format": "direct_diff",
        "schema_valid": patch_extractable,
        "strict_schema_valid": strict_patch_format,
        "format_normalized": patch_extractable and not strict_patch_format,
        "hallucination_count": len(disallowed),
        "git_apply_check": apply_ok,
        "git_apply_strict": strict_apply_ok,
        "git_apply_recount": recount_apply_ok,
        "format_recounted": apply_ok and not strict_apply_ok and recount_apply_ok,
        "changed_files": changed_files,
        "missing_patch_terms": required_terms,
        **size,
        "revision": revision,
        "test_result": "PASS" if test_ok else "FAIL" if test_exit_code is not None else "NOT_RUN",
        "test_exit_code": test_exit_code,
        "test_output": test_output,
        "apply_output": apply_output[-2000:],
        "semantic_correctness": terms_ok and test_ok,
        "structured_contract_correctness": None,
        "deterministic_application_correctness": apply_ok,
        "generated_diff_correctness": patch_extractable and apply_ok,
        "focused_test_correctness": test_ok,
        "score": score,
        "hard_gates": hard_gates,
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_structured_edit(case: dict, raw: str, target_repo: Path, minimum: int) -> dict:
    payload, schema_valid, strict_schema, contract_errors = parse_structured_candidate(raw)
    application = {
        "path_validation": False,
        "preconditions_valid": False,
        "stale_state_valid": False,
        "unique_occurrences": False,
        "occurrence_counts": [],
        "errors": [],
        "changed_files": [],
        "preimage_sha256": {},
        "postimage_sha256": {},
        "atomic_application": False,
    }
    changed_files: list[str] = []
    generated_patch = ""
    generated_diff_check = False
    generated_apply_check = False
    postimage_match = False
    required_terms_missing = list(case["required_patch_terms"])
    test_exit_code = None
    test_output = ""
    gate_output = ""
    size = {"added_lines": 0, "removed_lines": 0, "changed_lines": 0, "within_limit": False}

    with tempfile.TemporaryDirectory(prefix="ai-worker-structured-") as directory:
        root = Path(directory)
        assembly_repo = root / "assembly"
        clone = run_cmd(
            ["git", "clone", "--quiet", "--no-hardlinks", str(target_repo), str(assembly_repo)]
        )
        if clone.returncode != 0:
            gate_output = (clone.stdout + clone.stderr).strip()
        elif schema_valid:
            checkout = run_cmd(
                ["git", "checkout", "--quiet", "--detach", "HEAD"], cwd=assembly_repo
            )
            if checkout.returncode == 0:
                application = apply_exact_edits(
                    assembly_repo,
                    payload,
                    allowed_files=case["allowed_files"],
                    max_edits=case["max_edits"],
                )
            else:
                gate_output = (checkout.stdout + checkout.stderr).strip()

        if application["atomic_application"]:
            names = run_cmd(
                ["git", "diff", "--name-only"], cwd=assembly_repo, check=True
            ).stdout
            changed_files = [line.strip().replace("\\", "/") for line in names.splitlines()]
            generated_patch = run_cmd(
                ["git", "diff", "--no-ext-diff", "--binary"], cwd=assembly_repo, check=True
            ).stdout
            checked = run_cmd(["git", "diff", "--check"], cwd=assembly_repo)
            generated_diff_check = checked.returncode == 0 and bool(generated_patch.strip())
            gate_output = (checked.stdout + checked.stderr).strip()
            size = patch_size_evidence(case, generated_patch)
            required_terms_missing = [
                term for term in case["required_patch_terms"] if term not in generated_patch
            ]

            validation_repo = root / "validation"
            validation_clone = run_cmd(
                ["git", "clone", "--quiet", "--no-hardlinks", str(target_repo), str(validation_repo)]
            )
            patch_path = root / "generated.patch"
            patch_path.write_text(generated_patch, encoding="utf-8")
            if validation_clone.returncode == 0:
                run_cmd(["git", "checkout", "--quiet", "--detach", "HEAD"], cwd=validation_repo)
                apply_check = run_cmd(
                    ["git", "apply", "--check", str(patch_path)], cwd=validation_repo
                )
                generated_apply_check = apply_check.returncode == 0
                gate_output = (
                    gate_output + "\n" + apply_check.stdout + apply_check.stderr
                ).strip()
                if generated_apply_check:
                    applied = run_cmd(["git", "apply", str(patch_path)], cwd=validation_repo)
                    generated_apply_check = applied.returncode == 0
                if generated_apply_check:
                    postimage_match = all(
                        _sha256_file(validation_repo / path)
                        == application["postimage_sha256"][path]
                        for path in changed_files
                    )
                    if case.get("ensure_test_package", True):
                        (validation_repo / "tests" / "__init__.py").touch()
                    tested = run_cmd(case["test_command"], cwd=validation_repo)
                    test_exit_code = tested.returncode
                    test_output = (tested.stdout + tested.stderr)[-4000:]

    allowed = set(case["allowed_files"])
    disallowed = [path for path in changed_files if path not in allowed]
    allowed_only = bool(changed_files) and not disallowed
    terms_ok = not required_terms_missing
    test_ok = test_exit_code == 0
    structured_contract_ok = schema_valid and strict_schema
    deterministic_application_ok = (
        application["preconditions_valid"]
        and application["atomic_application"]
        and application["stale_state_valid"]
        and application["unique_occurrences"]
    )
    generated_diff_ok = generated_diff_check and generated_apply_check and postimage_match
    semantic = None
    if case.get("semantic_ground_truth"):
        semantic = evaluate_semantic_candidate(case["semantic_ground_truth"], payload)
        semantic_ok = semantic["semantic_correct"]
    else:
        semantic_ok = terms_ok and test_ok
    semantic_score_ok = semantic_ok if semantic is not None else terms_ok
    score = round(
        15 * structured_contract_ok
        + 10 * application["path_validation"]
        + 15 * application["preconditions_valid"]
        + 15 * deterministic_application_ok
        + 10 * allowed_only
        + 10 * semantic_score_ok
        + 10 * generated_diff_ok
        + 10 * test_ok
        + 5 * size["within_limit"],
        2,
    )
    hard_gates = {
        "strict_structured_contract": structured_contract_ok,
        "path_validation": application["path_validation"],
        "exact_preimage": application["preconditions_valid"] and application["stale_state_valid"],
        "unique_occurrence": application["unique_occurrences"],
        "atomic_application": deterministic_application_ok,
        "allowed_files_only": allowed_only,
        "semantic_requirements": semantic_ok,
        "generated_diff": generated_diff_ok,
        "focused_test": test_ok,
        "diff_size": size["within_limit"],
        "minimum_score": score >= minimum,
    }
    return {
        "candidate_format": "structured_edit",
        "schema_valid": schema_valid,
        "strict_schema_valid": schema_valid and strict_schema,
        "contract_errors": contract_errors,
        "application": application,
        "hallucination_count": len(disallowed),
        "git_apply_check": generated_apply_check,
        "changed_files": changed_files,
        "missing_patch_terms": required_terms_missing,
        **size,
        "generated_patch": generated_patch,
        "generated_diff_check": generated_diff_check,
        "postimage_match": postimage_match,
        "test_result": "PASS" if test_ok else "FAIL" if test_exit_code is not None else "NOT_RUN",
        "test_exit_code": test_exit_code,
        "test_output": test_output,
        "apply_output": gate_output[-2000:],
        "semantic_correctness": semantic_ok,
        "semantic_evidence": semantic,
        "semantic_failure_reason": semantic["semantic_failure_reason"] if semantic else [],
        "target_symbol": case.get("semantic_ground_truth", {}).get("target_symbol"),
        "structured_contract_correctness": structured_contract_ok,
        "deterministic_application_correctness": deterministic_application_ok,
        "generated_diff_correctness": generated_diff_ok,
        "focused_test_correctness": test_ok,
        "score": score,
        "hard_gates": hard_gates,
    }


def evaluate_reviewer(case: dict, raw: str, minimum: int) -> dict:
    payload, schema_valid, strict_schema = json_contract(raw, "reviewer")
    issues = payload.get("issues", []) if schema_valid else []
    detected = {issue["id"]: issue for issue in issues if issue.get("id") in ISSUE_TAXONOMY}
    unknown = [issue.get("id", "") for issue in issues if issue.get("id") not in ISSUE_TAXONOMY]
    gold = {issue["id"]: issue for issue in case["gold_issues"]}
    true_positive = sorted(set(detected).intersection(gold))
    false_positive = sorted(set(detected) - set(gold)) + unknown
    missed = sorted(set(gold) - set(detected))
    recall = len(true_positive) / len(gold)
    precision = len(true_positive) / max(1, len(detected) + len(unknown))
    severity_correct = sum(
        detected[issue_id].get("severity", "").lower() == gold[issue_id]["severity"]
        for issue_id in true_positive
    ) / max(1, len(true_positive))
    advice_useful = all(detected[issue_id].get("advice", "").strip() for issue_id in true_positive)
    verdict_ok = bool(payload and payload.get("verdict") == case["expected_verdict"])
    critical_missed = any(gold[issue_id]["severity"] == "critical" for issue_id in missed)
    score = round(
        50 * recall
        + 15 * precision
        + 15 * severity_correct
        + 10 * verdict_ok
        + 5 * advice_useful
        + 5 * strict_schema,
        2,
    )
    hard_gates = {
        "schema": schema_valid,
        "verdict": verdict_ok,
        "minimum_issue_recall": recall >= case["minimum_issue_recall"],
        "no_critical_miss": not critical_missed,
        "minimum_score": score >= minimum,
    }
    return {
        "schema_valid": schema_valid,
        "strict_schema_valid": schema_valid and strict_schema,
        "hallucination_count": len(unknown),
        "expected_issue_detection": true_positive,
        "true_positive": len(true_positive),
        "false_positive": len(false_positive),
        "missed_issue": missed,
        "issue_recall": round(recall, 3),
        "issue_precision": round(precision, 3),
        "severity_accuracy": round(severity_correct, 3),
        "useful_revision_advice": advice_useful,
        "score": score,
        "hard_gates": hard_gates,
    }


def evaluate(case: dict, raw: str, target_repo: Path, files: list[str], minimum: int) -> dict:
    role = case["role"]
    if role == "scout":
        return evaluate_scout(case, raw, files, minimum)
    if role == "planner":
        return evaluate_planner(case, raw, files, minimum)
    if case.get("output_contract") == "structured_edit":
        return evaluate_structured_edit(case, raw, target_repo, minimum)
    if role in {"coder", "escalation_coder"}:
        return evaluate_patch(case, raw, target_repo, minimum)
    if role == "reviewer":
        return evaluate_reviewer(case, raw, minimum)
    raise ValueError(f"unsupported role: {role}")


def all_hard_gates_pass(result: dict) -> bool:
    gates = result.get("hard_gates", {})
    return bool(gates) and all(gates.values())


def summarize_results(suite: dict, results: list[dict]) -> dict:
    grouped = defaultdict(list)
    for result in results:
        grouped[(result["role"], result["model"])].append(result)

    model_summaries = []
    for (role, model), slots in grouped.items():
        completed = [slot for slot in slots if slot.get("request_success")]
        hard_passes = sum(all_hard_gates_pass(slot) for slot in slots)
        model_summaries.append(
            {
                "role": role,
                "model": model,
                "slots": len(slots),
                "request_successes": len(completed),
                "hard_gate_passes": hard_passes,
                "hard_gate_rate": round(hard_passes / len(slots), 3),
                "mean_score": round(statistics.mean(slot.get("score", 0) for slot in slots), 2),
                "mean_latency_seconds": round(
                    statistics.mean(slot.get("latency_seconds", 0) for slot in slots), 2
                ),
                "qualified": hard_passes == len(slots)
                and statistics.mean(slot.get("score", 0) for slot in slots)
                >= suite["minimum_scores"][role],
            }
        )

    recommendations = {}
    for role in ROLE_ORDER:
        candidates = [item for item in model_summaries if item["role"] == role]
        candidates.sort(
            key=lambda item: (
                item["qualified"],
                item["hard_gate_rate"],
                item["mean_score"],
                -item["mean_latency_seconds"],
            ),
            reverse=True,
        )
        if not candidates:
            continue
        qualified = [item for item in candidates if item["qualified"]]
        primary = qualified[0] if qualified else None
        recommendations[role] = {
            "primary": primary["model"] if primary else None,
            "fallback": qualified[1]["model"] if len(qualified) > 1 else None,
            "best_observed": candidates[0]["model"],
            "primary_qualified": bool(primary),
            "reason": (
                f"hard gates {candidates[0]['hard_gate_passes']}/{candidates[0]['slots']}, "
                f"mean score {candidates[0]['mean_score']}, "
                f"mean latency {candidates[0]['mean_latency_seconds']}s"
            ),
        }
    contract_groups = defaultdict(list)
    for result in results:
        contract_groups[(result["model"], result.get("candidate_format", "other"))].append(result)
    contract_models = []
    for (model, candidate_format), slots in contract_groups.items():
        hard_passes = sum(all_hard_gates_pass(slot) for slot in slots)
        contract_models.append(
            {
                "model": model,
                "candidate_format": candidate_format,
                "slots": len(slots),
                "hard_gate_passes": hard_passes,
                "hard_gate_rate": round(hard_passes / len(slots), 3),
                "semantic_passes": sum(bool(slot.get("semantic_correctness")) for slot in slots),
                "contract_passes": sum(
                    slot.get("structured_contract_correctness") is True for slot in slots
                ),
                "deterministic_application_passes": sum(
                    bool(slot.get("deterministic_application_correctness")) for slot in slots
                ),
                "generated_diff_passes": sum(
                    bool(slot.get("generated_diff_correctness")) for slot in slots
                ),
                "focused_test_passes": sum(
                    bool(slot.get("focused_test_correctness")) for slot in slots
                ),
                "mean_score": round(statistics.mean(slot.get("score", 0) for slot in slots), 2),
                "mean_latency_seconds": round(
                    statistics.mean(slot.get("latency_seconds", 0) for slot in slots), 2
                ),
                "qualified": hard_passes == len(slots),
            }
        )
    contract_models.sort(key=lambda item: (item["model"], item["candidate_format"]))
    return {
        "models": model_summaries,
        "recommendations": recommendations,
        "contract_comparison": contract_models,
    }


def calibrate_structured_cases(suite: dict, target_repo: Path, output_dir: Path) -> list[dict]:
    results = []
    for case in suite["cases"]:
        if case.get("output_contract") != "structured_edit":
            continue
        raw = (ROOT / case["gold_candidate"]).read_text(encoding="utf-8")
        result = evaluate_structured_edit(
            case,
            raw,
            target_repo,
            suite["minimum_scores"][case["role"]],
        )
        results.append(
            {
                "case_id": case["case_id"],
                "gold_candidate": case["gold_candidate"],
                **result,
            }
        )
    (output_dir / "gold_calibration.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    failed = [result["case_id"] for result in results if not all_hard_gates_pass(result)]
    if failed:
        raise RuntimeError(f"structured evaluator gold calibration failed: {failed}")
    return results


def write_anchor_packets(suite: dict, target_repo: Path, output_dir: Path) -> None:
    anchored = [case for case in suite["cases"] if case.get("context_mode") == "semantic_anchor"]
    if not anchored:
        return
    anchor_dir = output_dir / "anchors"
    anchor_dir.mkdir()
    for case in anchored:
        packet = build_anchor_packet(case, target_repo)
        (anchor_dir / f"{case['case_id']}.json").write_text(
            json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def compare_with_baseline(suite: dict, results: list[dict], output_dir: Path) -> dict | None:
    baseline_path = suite.get("baseline_results")
    if not baseline_path:
        return None
    baseline = [
        json.loads(line)
        for line in (ROOT / baseline_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    def metrics(slots: list[dict]) -> dict:
        return {
            "slots": len(slots),
            "semantic_passes": sum(bool(slot.get("semantic_correctness")) for slot in slots),
            "structured_contract_passes": sum(
                bool(slot.get("structured_contract_correctness")) for slot in slots
            ),
            "deterministic_apply_passes": sum(
                bool(slot.get("deterministic_application_correctness")) for slot in slots
            ),
            "generated_diff_passes": sum(
                bool(slot.get("generated_diff_correctness")) for slot in slots
            ),
            "focused_test_passes": sum(
                bool(slot.get("focused_test_correctness")) for slot in slots
            ),
            "hard_gate_passes": sum(all_hard_gates_pass(slot) for slot in slots),
            "mean_context_chars": round(
                statistics.mean(slot.get("input_context_chars", 0) for slot in slots), 2
            ),
            "mean_latency_seconds": round(
                statistics.mean(slot.get("latency_seconds", 0) for slot in slots), 3
            ),
        }

    models = sorted({result["model"] for result in results})
    comparisons = []
    for model in models:
        before_slots = [
            slot
            for slot in baseline
            if slot.get("model") == model and slot.get("candidate_format") == "structured_edit"
        ]
        after_slots = [slot for slot in results if slot.get("model") == model]
        before = metrics(before_slots)
        after = metrics(after_slots)
        context_delta = after["mean_context_chars"] - before["mean_context_chars"]
        context_percent = (
            round(100 * context_delta / before["mean_context_chars"], 2)
            if before["mean_context_chars"]
            else None
        )
        comparisons.append(
            {
                "model": model,
                "baseline": before,
                "semantic_anchor": after,
                "context_delta_chars": round(context_delta, 2),
                "context_delta_percent": context_percent,
            }
        )
    comparison = {
        "baseline_results": baseline_path,
        "anchored_run": output_dir.name,
        "models": comparisons,
    }
    (output_dir / "baseline_comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return comparison


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def run_benchmark(
    *,
    suite_path: Path,
    target_repo: Path,
    ollama_url: str,
    model_filter: list[str] | None = None,
    role_filter: list[str] | None = None,
) -> Path:
    suite = load_suite(suite_path)
    target_before = validate_target(suite, target_repo)
    files = repository_files(target_repo)
    inventory = read_ollama_inventory(ollama_url)
    roles = [role for role in ROLE_ORDER if not role_filter or role in role_filter]
    if role_filter and set(role_filter) - set(ROLE_ORDER):
        raise ValueError(f"unknown roles: {sorted(set(role_filter) - set(ROLE_ORDER))}")

    run_id = "BENCH-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = ROOT / "benchmark_results" / run_id
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "suite.json").write_text(
        json.dumps(suite, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "ollama_url": ollama_url,
        "target_before": target_before,
        "runtime": suite["runtime"],
        "models": {},
    }

    chosen_models = set(model_filter or [])
    for role in roles:
        candidates = suite["candidates"][role]
        if chosen_models:
            candidates = [model for model in candidates if model in chosen_models]
        for model in candidates:
            if model not in inventory:
                raise RuntimeError(f"configured benchmark model is not installed: {model}")
            details = inventory[model].get("details", {})
            manifest["models"][model] = {
                "digest": inventory[model].get("digest"),
                "size": inventory[model].get("size"),
                "parameter_size": details.get("parameter_size"),
                "quantization_level": details.get("quantization_level"),
                "format": details.get("format"),
                "family": details.get("family"),
            }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_anchor_packets(suite, target_repo, output_dir)
    calibrate_structured_cases(suite, target_repo, output_dir)

    results = []
    results_path = output_dir / "results.jsonl"
    runtime = suite["runtime"]
    cases_by_role = defaultdict(list)
    for case in suite["cases"]:
        cases_by_role[case["role"]].append(case)

    for role in roles:
        candidates = suite["candidates"][role]
        if chosen_models:
            candidates = [model for model in candidates if model in chosen_models]
        for model in candidates:
            model_info = manifest["models"][model]
            for case in cases_by_role[role]:
                slot_id = f"{case['case_id']}--{safe_name(model)}"
                print(f"[{len(results) + 1}] {role} {case['case_id']} {model}", flush=True)
                system, user, context_chars = build_prompt(case, role, target_repo, files)
                raw = ""
                base_result = {
                    "run_id": run_id,
                    "suite_id": suite["suite_id"],
                    "case_id": case["case_id"],
                    "role": role,
                    "model": model,
                    "model_digest": model_info["digest"],
                    "quantization": model_info["quantization_level"],
                    "retry": 0,
                    "input_chars": len(system) + len(user),
                    "input_context_chars": context_chars,
                    "output_chars": 0,
                    "request_success": False,
                    "latency_seconds": 0.0,
                    "failure_reason": "",
                    "feedback_variant": case.get("feedback_variant"),
                    "include_old_patch": case.get("include_old_patch"),
                    "candidate_format": case.get("output_contract", "direct_diff"),
                    "context_mode": case.get("context_mode", "bounded"),
                    "anchor_type": case.get("semantic_anchor", {}).get("anchor_type"),
                }
                try:
                    request_started = time.perf_counter()
                    raw, elapsed, metadata = ollama_chat_detailed(
                        model,
                        system,
                        user,
                        num_ctx=runtime["num_ctx"],
                        temperature=runtime["temperature"],
                        seed=runtime["seed"],
                        timeout_seconds=runtime["timeout_seconds"],
                    )
                    base_result.update(
                        request_success=True,
                        latency_seconds=round(elapsed, 3),
                        output_chars=len(raw),
                        ollama_metrics=metadata,
                    )
                    evaluated = evaluate(
                        case,
                        raw.strip(),
                        target_repo,
                        files,
                        suite["minimum_scores"][role],
                    )
                    base_result.update(evaluated)
                except Exception as exc:
                    # Every slot must be preserved as failed Evidence; v1/v2 freeze
                    # retries at zero, so no error category is silently regenerated.
                    failed_elapsed = time.perf_counter() - request_started
                    base_result.update(
                        schema_valid=False,
                        hallucination_count=0,
                        git_apply_check=None,
                        expected_issue_detection=None,
                        test_result="NOT_RUN",
                        score=0.0,
                        latency_seconds=round(failed_elapsed, 3),
                        hard_gates={"request_success": False},
                        failure_reason=f"{type(exc).__name__}: {exc}",
                    )
                observation = run_cmd(["ollama", "ps"])
                base_result["ollama_ps"] = (observation.stdout or observation.stderr).strip()
                (raw_dir / f"{slot_id}.txt").write_text(raw, encoding="utf-8")
                results.append(base_result)
                with results_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(base_result, ensure_ascii=False) + "\n")
                print(
                    json.dumps(
                        {
                            "score": base_result.get("score"),
                            "hard_pass": all_hard_gates_pass(base_result),
                            "seconds": base_result["latency_seconds"],
                            "failure": base_result["failure_reason"],
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )

    target_after = validate_target(suite, target_repo)
    summary = summarize_results(suite, results)
    baseline_comparison = compare_with_baseline(suite, results, output_dir)
    summary.update(
        {
            "run_id": run_id,
            "suite_id": suite["suite_id"],
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "slot_count": len(results),
            "target_after": target_after,
            "baseline_comparison": baseline_comparison,
        }
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"saved: {output_dir}", flush=True)
    return output_dir


def replay_benchmark(
    *,
    suite_path: Path,
    target_repo: Path,
    source_run: Path,
) -> Path:
    """Re-evaluate preserved raw outputs without making another model call."""
    suite = load_suite(suite_path)
    target_before = validate_target(suite, target_repo)
    source_results = [
        json.loads(line)
        for line in (source_run / "results.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_slot = {(item["case_id"], item["model"]): item for item in source_results}
    run_id = "REPLAY-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = ROOT / "benchmark_results" / run_id
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "suite.json").write_text(
        json.dumps(suite, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    source_manifest = json.loads((source_run / "manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "run_id": run_id,
        "suite_id": suite["suite_id"],
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_run": source_run.name,
        "model_calls": 0,
        "raw_reused": True,
        "target_before": target_before,
        "runtime": suite["runtime"],
        "models": source_manifest["models"],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_anchor_packets(suite, target_repo, output_dir)
    calibrate_structured_cases(suite, target_repo, output_dir)

    files = repository_files(target_repo)
    results = []
    for case in suite["cases"]:
        for model in suite["candidates"][case["role"]]:
            previous = by_slot[(case["case_id"], model)]
            raw_name = f"{case['case_id']}--{safe_name(model)}.txt"
            raw = (source_run / "raw" / raw_name).read_text(encoding="utf-8")
            started = time.perf_counter()
            evaluated = evaluate(
                case,
                raw.strip(),
                target_repo,
                files,
                suite["minimum_scores"][case["role"]],
            )
            result = {
                **previous,
                "run_id": run_id,
                "suite_id": suite["suite_id"],
                "replay_source_run": source_run.name,
                "replay_model_call": False,
                "replay_evaluation_seconds": round(time.perf_counter() - started, 3),
                **evaluated,
            }
            results.append(result)
            (raw_dir / raw_name).write_text(raw, encoding="utf-8")
    results_path = output_dir / "results.jsonl"
    with results_path.open("w", encoding="utf-8") as handle:
        for result in results:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    target_after = validate_target(suite, target_repo)
    summary = summarize_results(suite, results)
    baseline_comparison = compare_with_baseline(suite, results, output_dir)
    summary.update(
        {
            "run_id": run_id,
            "suite_id": suite["suite_id"],
            "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "slot_count": len(results),
            "model_calls": 0,
            "source_run": source_run.name,
            "target_after": target_after,
            "baseline_comparison": baseline_comparison,
        }
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"saved: {output_dir}", flush=True)
    return output_dir
