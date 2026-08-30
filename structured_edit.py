from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile


EDIT_KEYS = {"path", "old_text", "new_text"}


def parse_structured_candidate(raw: str) -> tuple[dict | None, bool, bool, list[str]]:
    """Parse the exact edit contract while recording non-strict fenced JSON."""
    stripped = raw.strip()
    strict = True
    try:
        payload = json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        match = re.fullmatch(
            r"```(?:json)?\s*\n(.*)\n```", stripped, re.DOTALL | re.IGNORECASE
        )
        if not match:
            return None, False, False, ["output is not one JSON object"]
        strict = False
        try:
            payload = json.loads(match.group(1).strip())
        except (json.JSONDecodeError, TypeError):
            return None, False, False, ["fenced content is not valid JSON"]

    errors: list[str] = []
    if not isinstance(payload, dict) or set(payload) != {"edits"}:
        errors.append("top-level object must contain only edits")
        return payload if isinstance(payload, dict) else None, False, strict, errors
    edits = payload["edits"]
    if not isinstance(edits, list) or not edits:
        errors.append("edits must be a non-empty array")
    else:
        for index, edit in enumerate(edits):
            if not isinstance(edit, dict) or set(edit) != EDIT_KEYS:
                errors.append(f"edit {index} must contain only path, old_text, new_text")
                continue
            if not all(isinstance(edit[key], str) for key in EDIT_KEYS):
                errors.append(f"edit {index} fields must be strings")
            elif not edit["old_text"]:
                errors.append(f"edit {index} old_text must not be empty")
    return payload, not errors, strict, errors


def _safe_relative_path(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _read_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_atomic(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def apply_exact_edits(
    repository: Path,
    payload: dict,
    *,
    allowed_files: list[str],
    max_edits: int,
) -> dict:
    """Validate every exact preimage first, then apply the complete edit set."""
    edits = payload["edits"]
    errors: list[str] = []
    allowed = set(allowed_files)
    originals: dict[str, str] = {}
    operations: dict[str, list[tuple[int, int, str]]] = {}
    occurrence_counts: list[int] = []

    if len(edits) > max_edits:
        errors.append(f"edit count {len(edits)} exceeds maximum {max_edits}")

    for index, edit in enumerate(edits):
        relative = edit["path"]
        old_text = edit["old_text"]
        new_text = edit["new_text"]
        if not _safe_relative_path(relative):
            errors.append(f"edit {index} has unsafe path")
            occurrence_counts.append(0)
            continue
        if relative not in allowed:
            errors.append(f"edit {index} path is not allowed: {relative}")
            occurrence_counts.append(0)
            continue
        target = repository / Path(*PurePosixPath(relative).parts)
        if not target.is_file() or target.is_symlink():
            errors.append(f"edit {index} target is not a regular tracked file")
            occurrence_counts.append(0)
            continue
        if old_text == new_text:
            errors.append(f"edit {index} is a no-op")
        if relative not in originals:
            originals[relative] = _read_exact(target)
        content = originals[relative]
        count = content.count(old_text)
        occurrence_counts.append(count)
        if count != 1:
            errors.append(f"edit {index} old_text occurrence count is {count}, expected 1")
            continue
        start = content.index(old_text)
        operations.setdefault(relative, []).append((start, start + len(old_text), new_text))

    for relative, file_operations in operations.items():
        ordered = sorted(file_operations)
        for previous, current in zip(ordered, ordered[1:]):
            if previous[1] > current[0]:
                errors.append(f"overlapping edits for {relative}")

    base_result = {
        "path_validation": not any("path" in error or "target" in error for error in errors),
        "preconditions_valid": not errors,
        "stale_state_valid": all(count == 1 for count in occurrence_counts),
        "unique_occurrences": all(count == 1 for count in occurrence_counts),
        "occurrence_counts": occurrence_counts,
        "errors": errors,
        "changed_files": [],
        "preimage_sha256": {},
        "postimage_sha256": {},
        "atomic_application": False,
    }
    if errors:
        return base_result

    staged: dict[str, str] = {}
    for relative, content in originals.items():
        updated = content
        for start, end, new_text in sorted(operations[relative], reverse=True):
            updated = updated[:start] + new_text + updated[end:]
        if updated == content:
            base_result["errors"].append(f"combined edit set is a no-op for {relative}")
            base_result["preconditions_valid"] = False
            return base_result
        staged[relative] = updated

    replaced: list[str] = []
    try:
        for relative in sorted(staged):
            _write_atomic(repository / Path(*PurePosixPath(relative).parts), staged[relative])
            replaced.append(relative)
    except Exception:
        for relative in replaced:
            _write_atomic(repository / Path(*PurePosixPath(relative).parts), originals[relative])
        raise

    base_result.update(
        changed_files=sorted(staged),
        preimage_sha256={
            path: hashlib.sha256(originals[path].encode("utf-8")).hexdigest()
            for path in sorted(staged)
        },
        postimage_sha256={
            path: hashlib.sha256(staged[path].encode("utf-8")).hexdigest()
            for path in sorted(staged)
        },
        atomic_application=True,
    )
    return base_result
