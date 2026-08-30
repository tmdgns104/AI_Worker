from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath
from typing import Any


class AnchorError(ValueError):
    pass


def _safe_source(repository: Path, relative: str) -> tuple[Path, str, ast.Module]:
    if not relative or "\\" in relative:
        raise AnchorError(f"unsafe path: {relative}")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise AnchorError(f"unsafe path: {relative}")
    source_path = repository / Path(*path.parts)
    if not source_path.is_file() or source_path.is_symlink():
        raise AnchorError(f"source is not a regular file: {relative}")
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        source = handle.read()
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as exc:
        raise AnchorError(f"syntax error in {relative}: {exc.msg}") from exc
    return source_path, source, tree


def _symbol_rows(tree: ast.Module) -> list[tuple[str, ast.AST, str, str | None]]:
    rows: list[tuple[str, ast.AST, str, str | None]] = []

    def visit(body: list[ast.stmt], prefix: tuple[str, ...], parent_kind: str | None) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef):
                qualified = ".".join((*prefix, node.name))
                rows.append((qualified, node, "class", ".".join(prefix) or None))
                visit(node.body, (*prefix, node.name), "class")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualified = ".".join((*prefix, node.name))
                if isinstance(node, ast.AsyncFunctionDef):
                    kind = "async_method" if parent_kind == "class" else "async_function"
                else:
                    kind = "method" if parent_kind == "class" else "function"
                rows.append((qualified, node, kind, ".".join(prefix) or None))
                visit(node.body, (*prefix, node.name), "function")

    visit(tree.body, (), None)
    return rows


def _node_text(source: str, node: ast.AST) -> tuple[str, str]:
    lines = source.splitlines(keepends=True)
    start = node.lineno - 1
    end = node.end_lineno or node.lineno
    full_source = "".join(lines[start:end]).rstrip("\r\n")
    body = getattr(node, "body", [])
    body_start = body[0].lineno - 1 if body else start + 1
    signature = "".join(lines[start:max(start + 1, body_start)]).rstrip("\r\n")
    return signature, full_source


def extract_symbol_anchor(
    repository: Path,
    *,
    path: str,
    symbol: str,
    anchor_id: str,
    role: str,
    max_source_chars: int,
    source_mode: str = "full",
) -> dict[str, Any]:
    _source_path, source, tree = _safe_source(repository, path)
    rows = _symbol_rows(tree)
    exact = [row for row in rows if row[0] == symbol]
    matches = exact or [row for row in rows if row[0].split(".")[-1] == symbol]
    if not matches:
        raise AnchorError(f"missing symbol {symbol} in {path}")
    if len(matches) != 1:
        raise AnchorError(f"ambiguous symbol {symbol} in {path}")
    qualified, node, kind, containing = matches[0]
    signature, full_source = _node_text(source, node)
    selected_source = signature if source_mode == "signature" else full_source
    if source_mode not in {"signature", "full"}:
        raise AnchorError(f"unknown source mode: {source_mode}")
    if len(selected_source) > max_source_chars:
        raise AnchorError(
            f"source for {qualified} exceeds budget {max_source_chars}: {len(selected_source)}"
        )
    callees = sorted(
        {
            call.func.id if isinstance(call.func, ast.Name) else call.func.attr
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, (ast.Name, ast.Attribute))
        }
    )
    return {
        "anchor_id": anchor_id,
        "role": role,
        "path": path,
        "symbol": qualified,
        "kind": kind,
        "containing": containing,
        "signature": signature,
        "source": selected_source,
        "preimage": signature if role == "edit_target" else None,
        "direct_callees": callees,
        "source_chars": len(selected_source),
    }


def extract_import_anchor(
    repository: Path,
    *,
    path: str,
    module: str,
    names: list[str],
    anchor_id: str,
    role: str,
) -> dict[str, Any]:
    _source_path, source, tree = _safe_source(repository, path)
    expected = sorted(names)
    matches = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != module:
            continue
        observed = sorted(alias.name for alias in node.names)
        if observed == expected:
            matches.append(node)
    if not matches:
        raise AnchorError(f"missing import {module}:{','.join(expected)} in {path}")
    if len(matches) != 1:
        raise AnchorError(f"ambiguous import {module}:{','.join(expected)} in {path}")
    signature, source_text = _node_text(source, matches[0])
    return {
        "anchor_id": anchor_id,
        "role": role,
        "path": path,
        "symbol": module,
        "kind": "import_from",
        "containing": None,
        "signature": signature,
        "source": source_text,
        "preimage": source_text if role == "edit_target" else None,
        "direct_callees": [],
        "source_chars": len(source_text),
    }


def build_anchor_packet(case: dict, repository: Path) -> dict[str, Any]:
    contract = case["semantic_anchor"]
    anchors = []
    for spec in contract["specs"]:
        common = {
            "repository": repository,
            "path": spec["path"],
            "anchor_id": spec["anchor_id"],
            "role": spec["role"],
        }
        if spec["type"] == "symbol":
            anchor = extract_symbol_anchor(
                **common,
                symbol=spec["symbol"],
                max_source_chars=spec["max_source_chars"],
                source_mode=spec.get("source_mode", "full"),
            )
        elif spec["type"] == "import":
            anchor = extract_import_anchor(
                **common,
                module=spec["module"],
                names=spec["names"],
            )
        else:
            raise AnchorError(f"unknown anchor type: {spec['type']}")
        anchors.append(anchor)
    return {
        "schema_version": 1,
        "anchor_type": contract["anchor_type"],
        "behavior_contract": contract["behavior_contract"],
        "anchors": anchors,
    }


def evaluate_semantic_candidate(ground_truth: dict, payload: dict | None) -> dict[str, Any]:
    edits = payload.get("edits", []) if isinstance(payload, dict) else []
    usable = [edit for edit in edits if isinstance(edit, dict)]
    candidate_paths = sorted(
        {edit.get("path") for edit in usable if isinstance(edit.get("path"), str)}
    )
    candidate_text = "\n".join(
        edit.get("new_text", "")
        for edit in usable
        if isinstance(edit.get("new_text", ""), str)
    )
    expected_paths = sorted(ground_truth["expected_changed_files"])
    missing_terms = [term for term in ground_truth["required_terms"] if term not in candidate_text]
    missing_target = [term for term in ground_truth["target_terms"] if term not in candidate_text]
    forbidden_hits = [term for term in ground_truth["forbidden_terms"] if term in candidate_text]
    unexpected_paths = sorted(set(candidate_paths) - set(expected_paths))
    missing_paths = sorted(set(expected_paths) - set(candidate_paths))
    reasons = []
    if unexpected_paths:
        reasons.append("UNRELATED_CHANGE")
    if missing_paths or missing_target:
        reasons.append("WRONG_TARGET_SYMBOL")
    if forbidden_hits:
        reasons.append("WRONG_BEHAVIOR")
    if missing_terms:
        reasons.append("INCOMPLETE_FIX")
    if not usable and "INCOMPLETE_FIX" not in reasons:
        reasons.append("INCOMPLETE_FIX")
    if ground_truth.get("semantic_check") == "first_oversized_progress_test":
        if not _first_oversized_progress_is_valid(
            candidate_text, ground_truth["semantic_function"]
        ):
            reasons.append("MISUNDERSTOOD_DATA_FLOW")
    return {
        "semantic_correct": not reasons,
        "semantic_failure_reason": list(dict.fromkeys(reasons)),
        "candidate_paths": candidate_paths,
        "missing_required_terms": missing_terms,
        "missing_target_terms": missing_target,
        "forbidden_behavior_hits": forbidden_hits,
        "unexpected_paths": unexpected_paths,
        "missing_expected_paths": missing_paths,
    }


def _integer(node: ast.AST | None) -> int | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, int) else None


def _static_text_length(node: ast.AST | None) -> int | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return len(node.value)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
            multiplier = _integer(node.right)
            return len(node.left.value) * multiplier if multiplier is not None else None
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            multiplier = _integer(node.left)
            return len(node.right.value) * multiplier if multiplier is not None else None
    return None


def _first_oversized_progress_is_valid(candidate_text: str, function_name: str) -> bool:
    try:
        wrapped = "class _Candidate:\n" + candidate_text + "\n        pass\n"
        tree = ast.parse(wrapped)
    except (SyntaxError, ValueError):
        return False
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    ]
    if len(functions) != 1:
        return False
    function = functions[0]
    messages_value = None
    for node in function.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "messages" for target in node.targets)
        ):
            messages_value = node.value
            break
    if not isinstance(messages_value, ast.List) or len(messages_value.elts) != 1:
        return False
    message = messages_value.elts[0]
    if not (
        isinstance(message, ast.Call)
        and isinstance(message.func, ast.Name)
        and message.func.id == "ConversationMessage"
        and len(message.args) >= 3
    ):
        return False
    cursor = _integer(message.args[0])
    content_length = _static_text_length(message.args[2])
    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "select_message_chunk"
    ]
    if len(calls) != 1 or cursor is None or content_length is None:
        return False
    keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords if keyword.arg}
    after_cursor = _integer(keywords.get("after_cursor"))
    max_characters = _integer(keywords.get("max_characters"))
    return (
        after_cursor is not None
        and after_cursor < cursor
        and max_characters is not None
        and max_characters < content_length
    )
