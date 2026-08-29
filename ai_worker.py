from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
MODEL_CFG = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))
PROJECT_CFG = json.loads((ROOT / "config" / "project.json").read_text(encoding="utf-8"))


def prepare_command(args, *, platform_name=None):
    """Return a subprocess command that can execute native and script shims.

    Windows command shims installed by npm and similar tools commonly end in
    ``.cmd`` or ``.bat``. ``CreateProcess`` cannot execute those files directly,
    so list-form commands must go through ``cmd.exe`` while preserving argument
    quoting. String commands retain the existing shell behavior.
    """
    if isinstance(args, str):
        return args, True

    command = [str(value) for value in args]
    if not command:
        raise ValueError("command must not be empty")

    active_platform = os.name if platform_name is None else platform_name
    executable = shutil.which(command[0]) if active_platform == "nt" else None
    if executable and executable.lower().endswith((".cmd", ".bat")):
        command_line = subprocess.list2cmdline([executable, *command[1:]])
        command_processor = os.environ.get("COMSPEC", "cmd.exe")
        return [command_processor, "/d", "/s", "/c", command_line], False

    return command, False


def run_cmd(args, cwd=None, check=False):
    command, shell = prepare_command(args)
    p = subprocess.run(command, cwd=cwd, text=True, capture_output=True, shell=shell)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {args}\n{p.stdout}\n{p.stderr}")
    return p


def repo() -> Path:
    return Path(PROJECT_CFG["worktree"])


def original_repo() -> Path:
    return Path(PROJECT_CFG["target_repo"])


def ollama_chat_detailed(
    model: str,
    system: str,
    user: str,
    *,
    num_ctx=None,
    temperature=None,
    seed=None,
    timeout_seconds=900,
):
    """Call the local Ollama chat endpoint and retain runtime metadata."""
    url = MODEL_CFG["ollama_url"].rstrip("/") + "/api/chat"
    limits = MODEL_CFG["limits"]
    options = {
        "temperature": limits["temperature"] if temperature is None else temperature,
        "num_ctx": num_ctx or limits["num_ctx_default"],
    }
    if seed is not None:
        options["seed"] = seed
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": options,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout_seconds) as r:
        obj = json.loads(r.read().decode("utf-8"))
    elapsed = time.perf_counter() - started
    metadata = {
        "model": obj.get("model", model),
        "created_at": obj.get("created_at"),
        "done_reason": obj.get("done_reason"),
        "total_duration_ns": obj.get("total_duration"),
        "load_duration_ns": obj.get("load_duration"),
        "prompt_eval_count": obj.get("prompt_eval_count"),
        "prompt_eval_duration_ns": obj.get("prompt_eval_duration"),
        "eval_count": obj.get("eval_count"),
        "eval_duration_ns": obj.get("eval_duration"),
    }
    return obj["message"]["content"], elapsed, metadata


def ollama_chat(model: str, system: str, user: str, *, num_ctx=None, temperature=None):
    limits = MODEL_CFG["limits"]
    content, elapsed, _metadata = ollama_chat_detailed(
        model,
        system,
        user,
        num_ctx=num_ctx,
        temperature=temperature,
        seed=limits.get("seed"),
    )
    return content, elapsed


def extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a : b + 1])
        raise


def safe_relpath(value: str):
    value = value.replace("\\", "/").strip().lstrip("/")
    if not value:
        return None
    if ".." in Path(value).parts:
        return None
    return value


def ollama_model_names(output: str):
    """Extract model names from the stable first column of ``ollama list``."""
    lines = [line.split() for line in output.splitlines() if line.strip()]
    if not lines:
        return set()
    start = 1 if lines[0][0].upper() == "NAME" else 0
    return {columns[0] for columns in lines[start:] if columns}


def doctor():
    print("== Executables ==")
    failures = []
    executables = {}
    for exe in ["git", "codex", "ollama"]:
        found = shutil.which(exe)
        executables[exe] = found
        ok = bool(found)
        if not ok:
            failures.append(f"missing executable: {exe}")
        print(f"{exe:8} {'OK' if ok else 'FAIL'}  {found or 'NOT FOUND'}")

    print("\n== Paths ==")
    print("AI Worker   :", ROOT)
    target_exists = original_repo().exists()
    target_is_git = False
    if target_exists and executables["git"]:
        target_check = run_cmd(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=original_repo()
        )
        target_is_git = target_check.returncode == 0 and target_check.stdout.strip() == "true"
    target_status = "OK" if target_is_git else "MISSING OR NOT GIT"
    if not target_is_git:
        failures.append(f"invalid target repository: {original_repo()}")
    print("target repo :", original_repo(), target_status)
    print("worktree    :", repo(), "EXISTS" if repo().exists() else "not created yet")

    print("\n== Versions ==")
    for executable, args in (
        ("git", ["git", "--version"]),
        ("codex", ["codex", "--version"]),
        ("ollama", ["ollama", "--version"]),
    ):
        if not executables[executable]:
            continue
        p = run_cmd(args)
        output = (p.stdout or p.stderr).strip()
        print(output or f"{executable}: no version output")
        if p.returncode != 0:
            failures.append(f"version command failed: {executable}")

    print("\n== Ollama models ==")
    installed_models = set()
    if executables["ollama"]:
        p = run_cmd(["ollama", "list"])
        model_output = (p.stdout or p.stderr).strip()
        print(model_output or "no models reported")
        if p.returncode != 0:
            failures.append("Ollama is not reachable")
        else:
            installed_models = ollama_model_names(p.stdout)

    print("\n== Configured roles ==")
    for role, model in MODEL_CFG["roles"].items():
        available = model in installed_models
        print(f"{role:20} {model:48} {'OK' if available else 'MISSING'}")
        if not available:
            failures.append(f"configured model missing for {role}: {model}")

    print("\n== Doctor verdict ==")
    if failures:
        print("FAIL")
        for failure in failures:
            print("-", failure)
        return 1
    print("PASS")
    return 0


def bootstrap():
    src = original_repo()
    wt = repo()
    branch = PROJECT_CFG["branch"]
    base = PROJECT_CFG["base_branch"]

    if not src.exists():
        raise SystemExit(f"Target repository not found: {src}")
    if run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd=src).returncode != 0:
        raise SystemExit(f"Not a git repository: {src}")

    wt.parent.mkdir(parents=True, exist_ok=True)
    if wt.exists():
        print(f"worktree already exists: {wt}")
        return

    existing = run_cmd(["git", "branch", "--list", branch], cwd=src)
    if existing.stdout.strip():
        cmd = ["git", "worktree", "add", str(wt), branch]
    else:
        cmd = ["git", "worktree", "add", "-b", branch, str(wt), base]

    p = run_cmd(cmd, cwd=src)
    print(p.stdout.strip())
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    print(f"created: {wt}")


def git_snapshot():
    r = repo()
    if not r.exists():
        raise SystemExit("Run `python ai_worker.py bootstrap` first.")

    def g(*args):
        return run_cmd(["git", *args], cwd=r).stdout.strip()

    return {
        "branch": g("branch", "--show-current"),
        "head": g("rev-parse", "HEAD"),
        "status": g("status", "--short"),
        "recent": g("--no-pager", "log", "-5", "--oneline"),
    }


def list_repo_files():
    p = run_cmd(["git", "ls-files"], cwd=repo(), check=True)
    return [x.strip().replace("\\", "/") for x in p.stdout.splitlines() if x.strip()]


def read_context(paths):
    limits = MODEL_CFG["limits"]
    total_limit = limits["max_total_context_chars"]
    file_limit = limits["max_file_chars"]
    out = []
    used = 0

    for rel in paths[: limits["selected_files"]]:
        rel = safe_relpath(rel)
        if not rel:
            continue
        p = (repo() / rel).resolve()
        try:
            p.relative_to(repo().resolve())
        except ValueError:
            continue
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        text = text[:file_limit]
        if used + len(text) > total_limit:
            text = text[: max(0, total_limit - used)]
        if not text:
            break
        out.append(f"\n===== FILE: {rel} =====\n{text}")
        used += len(text)
        if used >= total_limit:
            break
    return "".join(out)


def make_run_id(prefix="RUN"):
    return f"{prefix}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"


def benchmark(models=None, *, roles=None, suite_path=None):
    """Run the versioned role benchmark without modifying the Target worktree."""
    from benchmark_runner import run_benchmark

    return run_benchmark(
        suite_path=Path(suite_path) if suite_path else ROOT / "benchmarks" / "suite_v2.json",
        target_repo=repo(),
        ollama_url=MODEL_CFG["ollama_url"],
        model_filter=models,
        role_filter=roles,
    )


def run_task(task: str):
    snap = git_snapshot()
    files = list_repo_files()
    limits = MODEL_CFG["limits"]
    roles = MODEL_CFG["roles"]
    run_id = make_run_id()
    rd = ROOT / "runs" / run_id
    rd.mkdir(parents=True, exist_ok=False)

    scout_system = (
        "You are a repository scout with no tools or filesystem access. "
        "Choose only the most relevant paths from the supplied file list. "
        "Return strict JSON: {\"files\":[...],\"reason\":\"...\"}. "
        f"Select at most {limits['selected_files']} files and never invent paths."
    )
    scout_user = f"TASK:\n{task}\n\nREPOSITORY SNAPSHOT:\n{json.dumps(snap, ensure_ascii=False, indent=2)}\n\nFILES:\n" + "\n".join(files)
    scout_raw, scout_sec = ollama_chat(
        roles["scout"], scout_system, scout_user, num_ctx=limits["num_ctx_default"]
    )
    (rd / "01_scout_raw.txt").write_text(scout_raw, encoding="utf-8")

    selected = []
    try:
        scout = extract_json(scout_raw)
        selected = [safe_relpath(x) for x in scout.get("files", [])]
        selected = [x for x in selected if x in files][: limits["selected_files"]]
    except Exception:
        pass

    if not selected:
        preferred = ["STATUS.md", "README.md", "app/main.py", "app/runtime.py", "app/conversation.py"]
        selected = [x for x in preferred if x in files][: limits["selected_files"]]

    context = read_context(selected)
    (rd / "02_context.txt").write_text(context, encoding="utf-8")

    planner_system = (
        "You are a bounded software planner with no tools. Analyze only supplied context. "
        "Return strict JSON with summary, risks, plan, files_to_change, tests, constraints. "
        "Prefer one small reversible improvement and do not assume unseen code."
    )
    planner_user = f"TASK:\n{task}\n\nSNAPSHOT:\n{json.dumps(snap, ensure_ascii=False, indent=2)}\n\nCONTEXT:\n{context}"
    planner_raw, planner_sec = ollama_chat(roles["planner"], planner_system, planner_user)
    (rd / "03_planner_raw.txt").write_text(planner_raw, encoding="utf-8")
    try:
        plan = extract_json(planner_raw)
    except Exception:
        plan = {"summary": planner_raw, "plan": [], "files_to_change": selected, "tests": []}

    coder_system = (
        "You are a bounded coding worker. You have no filesystem, Git, shell or network tools. "
        "Produce only a unified diff suitable for git apply from supplied files. "
        "Do not use markdown fences. Keep changes small. Never claim tests were run."
    )
    coder_user = f"TASK:\n{task}\n\nPLAN:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n\nCURRENT FILE CONTENT:\n{context}"
    patch, coder_sec = ollama_chat(roles["coder"], coder_system, coder_user)
    patch = patch.strip()
    candidate_path = rd / "candidate.patch"
    candidate_path.write_text(patch + "\n", encoding="utf-8")

    reviewer_system = (
        "You are an independent code reviewer with no tools. "
        "Return strict JSON with verdict ACCEPT|REVISE|REJECT, confidence 0..1, issues, suggestions, tests. "
        "Review only the supplied task/context/patch and never claim tests were executed."
    )
    reviewer_user = f"TASK:\n{task}\n\nPLAN:\n{json.dumps(plan, ensure_ascii=False, indent=2)}\n\nCONTEXT:\n{context}\n\nPATCH:\n{patch}"
    reviewer_raw, reviewer_sec = ollama_chat(
        roles["reviewer"], reviewer_system, reviewer_user, num_ctx=limits["num_ctx_heavy"]
    )
    (rd / "04_review_raw.txt").write_text(reviewer_raw, encoding="utf-8")
    try:
        review = extract_json(reviewer_raw)
    except Exception:
        review = {
            "verdict": "REVISE",
            "confidence": 0.0,
            "issues": ["Reviewer returned invalid JSON."],
            "suggestions": [reviewer_raw],
            "tests": [],
        }

    check = run_cmd(["git", "apply", "--check", str(candidate_path)], cwd=repo())
    check_ok = check.returncode == 0

    metrics = {
        "scout_model": roles["scout"],
        "planner_model": roles["planner"],
        "coder_model": roles["coder"],
        "reviewer_model": roles["reviewer"],
        "seconds": {
            "scout": round(scout_sec, 2),
            "planner": round(planner_sec, 2),
            "coder": round(coder_sec, 2),
            "reviewer": round(reviewer_sec, 2),
        },
    }
    (rd / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# Local Worker Candidate Report\n\nRun: `{run_id}`\n\n## Task\n{task}\n\n## Repository\n- Branch: `{snap['branch']}`\n- HEAD: `{snap['head']}`\n- Dirty before run: `{snap['status'] or 'clean'}`\n\n## Selected files\n""" + "\n".join(f"- `{x}`" for x in selected) + f"""\n\n## Planner summary\n{plan.get('summary', '')}\n\n## Independent review\n- Verdict: **{review.get('verdict', 'UNKNOWN')}**\n- Confidence: `{review.get('confidence', '?')}`\n\n## Deterministic evidence\n- `git apply --check candidate.patch`: **{'PASS' if check_ok else 'FAIL'}**\n- Output: `{(check.stdout + check.stderr).strip() or 'none'}`\n\n## Timing\n- Scout: {metrics['seconds']['scout']} s\n- Planner: {metrics['seconds']['planner']} s\n- Coder: {metrics['seconds']['coder']} s\n- Reviewer: {metrics['seconds']['reviewer']} s\n\n## Supervisor action\nCodex must inspect this report and `candidate.patch`.\nThe candidate has NOT been applied.\nLocal model verdict is not authoritative.\n"""
    (rd / "report.md").write_text(report, encoding="utf-8")

    inbox = f"""# SUPERVISOR INBOX\n\nNewest run: `{run_id}`\n\nTask:\n{task}\n\nRead:\n1. `runs/{run_id}/report.md`\n2. `runs/{run_id}/candidate.patch`\n\nCandidate was NOT applied.\n`git apply --check`: {'PASS' if check_ok else 'FAIL'}\nLocal reviewer verdict: {review.get('verdict', 'UNKNOWN')}\n"""
    (ROOT / "SUPERVISOR_INBOX.md").write_text(inbox, encoding="utf-8")

    print(f"RUN_ID={run_id}")
    print(f"report: {rd / 'report.md'}")
    print(f"patch : {candidate_path}")
    print(f"git apply --check: {'PASS' if check_ok else 'FAIL'}")
    print(f"review verdict: {review.get('verdict', 'UNKNOWN')}")


def revise(run_id: str):
    rd = ROOT / "runs" / run_id
    feedback_path = rd / "codex_feedback.txt"
    if not rd.exists():
        raise SystemExit(f"Unknown run: {run_id}")
    if not feedback_path.exists():
        raise SystemExit(f"Create {feedback_path} first.")

    feedback = feedback_path.read_text(encoding="utf-8")
    context = (rd / "02_context.txt").read_text(encoding="utf-8")
    old_patch = (rd / "candidate.patch").read_text(encoding="utf-8")
    model = MODEL_CFG["roles"]["escalation_coder"]

    system = (
        "You are an escalation coding worker with no tools. "
        "Revise the unified diff using only supplied context and supervisor feedback. "
        "Output only a unified diff suitable for git apply."
    )
    user = f"SUPERVISOR FEEDBACK:\n{feedback}\n\nCURRENT CONTEXT:\n{context}\n\nOLD PATCH:\n{old_patch}"
    patch, elapsed = ollama_chat(model, system, user, num_ctx=MODEL_CFG["limits"]["num_ctx_heavy"])
    out = rd / "candidate_revised.patch"
    out.write_text(patch.strip() + "\n", encoding="utf-8")
    chk = run_cmd(["git", "apply", "--check", str(out)], cwd=repo())
    print(f"model: {model}")
    print(f"seconds: {elapsed:.2f}")
    print(out)
    print("git apply --check:", "PASS" if chk.returncode == 0 else "FAIL")
    if chk.stdout or chk.stderr:
        print((chk.stdout + chk.stderr).strip())


def status():
    print(json.dumps(git_snapshot(), ensure_ascii=False, indent=2))
    inbox = ROOT / "SUPERVISOR_INBOX.md"
    if inbox.exists():
        print("\n== Inbox ==")
        print(inbox.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description="Codex Supervisor + bounded local Ollama worker harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("bootstrap")
    sub.add_parser("status")

    p_bench = sub.add_parser("benchmark")
    p_bench.add_argument("models", nargs="*")
    p_bench.add_argument("--roles", nargs="*")
    p_bench.add_argument("--suite")

    p_run = sub.add_parser("run")
    p_run.add_argument("task")

    p_rev = sub.add_parser("revise")
    p_rev.add_argument("run_id")

    ns = ap.parse_args()
    if ns.cmd == "doctor":
        raise SystemExit(doctor())
    if ns.cmd == "bootstrap":
        bootstrap()
    elif ns.cmd == "status":
        status()
    elif ns.cmd == "benchmark":
        benchmark(ns.models or None, roles=ns.roles or None, suite_path=ns.suite)
    elif ns.cmd == "run":
        run_task(ns.task)
    elif ns.cmd == "revise":
        revise(ns.run_id)


if __name__ == "__main__":
    main()
