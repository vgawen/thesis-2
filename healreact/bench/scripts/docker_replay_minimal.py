#!/usr/bin/env python3
"""
Minimal runtime replay for HealReact's static L3 repairs.

Goal
----
Convert the paper's static proxy ("v1 exact selector match = 58/75 = 62.4%
over all 93 koenig breaks") into a real Playwright pass/fail measurement for
the same v1-exact cases.

This script deliberately reuses ReproBreak's own reproduction harness instead
of reimplementing Docker setup:

  1. Load the v1 baseline JSON and select rows where exact_match == true.
  2. For each locator_id, ask ReproBreak's DB for the reproduction bundle.
  3. Checkout the fixed commit, extract its Dockerfile/run_tests.sh, and build
     or reuse the per-commit Docker image.
  4. Run the fixed test once as an infrastructure baseline.
  5. Replace the fixed `new_locator` in the checked-out test file with
     HealReact's `proposed_selector`, mount that patched file into the
     ReproBreak container, and run the same Playwright test file.

Classification
--------------
  true_pass:
      fixed baseline passed, patched HealReact selector also passed.
  resolver_correct_runtime_broken:
      fixed baseline passed, but patched HealReact selector failed at runtime.
      This is the important gap between static selector equality and actual
      Playwright behavior (visibility, timing, async, assertions, etc.).
  infrastructure_fail:
      Docker/image/test did not start, fixed baseline did not pass, or the patch
      could not be applied. These cases should not count against the repairer.

Prerequisites
-------------
  - Docker Desktop is installed and running.
  - ReproBreak is available, with data/ReproBreak.db present.
  - The ReproBreak Python environment has its dependencies installed
    (notably the `docker` Python package).

Example
-------
  cd /Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/scripts
  ~/Downloads/ReproBreak/ReproBreak-main/.venv/bin/python docker_replay_minimal.py --limit 3
  ~/Downloads/ReproBreak/ReproBreak-main/.venv/bin/python docker_replay_minimal.py --ids 615,702,703
  ~/Downloads/ReproBreak/ReproBreak-main/.venv/bin/python docker_replay_minimal.py --no-fixed-baseline
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
BENCH_ROOT = ROOT.parent / "cases" / "koenig"
DEFAULT_REPRO_ROOT = Path.home() / "Downloads" / "ReproBreak" / "ReproBreak-main"
DEFAULT_HEAL_OUT = BENCH_ROOT / "_abl_w1_f1.json"
DEFAULT_RESULTS = BENCH_ROOT / "_docker_replay_minimal.json"


def load_reprobreak(repro_root: Path) -> dict[str, Any]:
    """Import the small set of ReproBreak helpers we need."""
    sys.path.insert(0, str(repro_root))
    import docker  # type: ignore
    from reproduce import (  # type: ignore
        extract_reproduction_files,
        get_locator_break_reproduction_info,
    )
    from create_reproducible_dataset import (  # type: ignore
        TestStatus,
        clone_repo,
        parse_test_result,
        reset_repository,
        setup_base_image,
    )

    return {
        "docker": docker,
        "extract_reproduction_files": extract_reproduction_files,
        "get_info": get_locator_break_reproduction_info,
        "TestStatus": TestStatus,
        "clone_repo": clone_repo,
        "parse_test_result": parse_test_result,
        "reset_repository": reset_repository,
        "setup_base_image": setup_base_image,
    }


def sh(cmd: list[str], cwd: Path | None = None) -> int:
    return subprocess.call(cmd, cwd=str(cwd) if cwd else None)


def replace_once_in_line(path: Path, line_no: int, old: str, new: str) -> tuple[bool, str]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if line_no < 1 or line_no > len(lines):
        return False, f"line_no_out_of_range:{line_no}"
    target = lines[line_no - 1]
    if old not in target:
        return False, "new_locator_not_found_on_target_line"
    lines[line_no - 1] = target.replace(old, new, 1)
    path.write_text("".join(lines), encoding="utf-8")
    return True, "patched"


def optimize_repro_dockerfile(reproduce_path: Path) -> None:
    """Make ReproBreak's generated Dockerfile feasible for a minimal smoke run.

    The upstream Dockerfile installs all Playwright browsers. For this paper's
    minimal runtime check we only need the Chromium path that Playwright uses by
    default, and Docker Desktop on macOS can take a very long time exporting the
    all-browser image. This keeps the reproduction harness unchanged except for
    narrowing browser installation.
    """
    dockerfile = reproduce_path / "Dockerfile"
    if not dockerfile.exists():
        return
    text = dockerfile.read_text()
    text = text.replace(
        "npx playwright install --with-deps",
        "NODE_TLS_REJECT_UNAUTHORIZED=0 npx playwright install --with-deps chromium",
    )
    dockerfile.write_text(text)


def run_e2e_with_logs(
    client: Any,
    image: str,
    command: str,
    parse_test_result: Any,
    volumes: dict[str, Any] | None = None,
    timeout_sec: int = 300,
) -> dict[str, Any]:
    """ReproBreak-compatible container run, but preserve exit code and logs."""
    container = None
    try:
        container = client.containers.run(
            image=image,
            command=command,
            volumes=volumes,
            detach=True,
            remove=False,
        )

        result: dict[str, Any] = {}

        def wait_for_container() -> None:
            try:
                result["exit_code"] = container.wait()["StatusCode"]
            except Exception as e:
                result["wait_error"] = repr(e)

        thread = threading.Thread(target=wait_for_container)
        thread.start()
        thread.join(timeout=timeout_sec)

        if thread.is_alive():
            container.kill()
            try:
                logs = container.logs(stream=False).decode("utf-8", errors="ignore")
            except Exception as e:
                logs = f"(container logs unavailable after timeout: {e!r})"
            return {
                "status": "did not start",
                "exit_code": None,
                "timed_out": True,
                "log_tail": logs[-4000:],
            }
        if "wait_error" in result:
            return {
                "status": "did not start",
                "exit_code": None,
                "timed_out": False,
                "error": result["wait_error"],
                "log_tail": "",
            }

        try:
            raw_logs = container.logs(stream=False)
            status = parse_test_result(result["exit_code"], raw_logs)
            logs = raw_logs.decode("utf-8", errors="ignore")
            status_value = status.value if hasattr(status, "value") else str(status)
        except Exception as e:
            # Some Docker Desktop configurations use a logging driver that does
            # not support `docker logs`. In that case, exit code is still enough
            # for the minimal pass/fail replay metric.
            logs = f"(container logs unavailable: {e!r})"
            status_value = "passed" if result["exit_code"] == 0 else "failed"
        return {
            "status": status_value,
            "exit_code": result["exit_code"],
            "timed_out": False,
            "log_tail": logs[-4000:],
        }
    except Exception as e:  # Docker daemon/image/test-runner errors.
        return {
            "status": "did not start",
            "exit_code": None,
            "timed_out": False,
            "error": repr(e),
            "log_tail": "",
        }
    finally:
        if container is not None:
            with contextlib.suppress(Exception):
                container.remove(force=True)


def selected_rows(heal_out: Path, ids: set[int] | None, limit: int) -> list[dict[str, Any]]:
    data = json.loads(heal_out.read_text())
    rows = [r for r in data["rows"] if r.get("exact_match")]
    if ids is not None:
        rows = [r for r in rows if int(r["id"]) in ids]
    if limit:
        rows = rows[:limit]
    return rows


def classify(fixed: dict[str, Any] | None, patched: dict[str, Any] | None, patch_ok: bool) -> str:
    if not patch_ok:
        return "infrastructure_fail"
    if fixed is not None and fixed.get("status") != "passed":
        return "infrastructure_fail"
    if patched is None:
        return "infrastructure_fail"
    if patched.get("status") == "passed":
        return "true_pass"
    if patched.get("status") == "failed":
        return "resolver_correct_runtime_broken"
    return "infrastructure_fail"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repro-root", type=Path, default=Path(os.environ.get("REPRO_ROOT", DEFAULT_REPRO_ROOT)))
    ap.add_argument("--db", type=Path, default=None, help="defaults to <repro-root>/data/ReproBreak.db")
    ap.add_argument("--work-dir", type=Path, default=None,
                    help="defaults to <repro-root>/data/reproduction_files")
    ap.add_argument("--heal-out", type=Path, default=DEFAULT_HEAL_OUT)
    ap.add_argument("--out", type=Path, default=DEFAULT_RESULTS)
    ap.add_argument("--ids", default="", help="comma-separated locator ids; default = all v1-exact ids")
    ap.add_argument("--limit", type=int, default=0, help="smoke-test first N selected ids")
    ap.add_argument("--timeout-sec", type=int, default=300)
    ap.add_argument("--no-fixed-baseline", action="store_true",
                    help="skip fixed-mode baseline run; faster but weaker infrastructure classification")
    args = ap.parse_args()

    if not args.repro_root.exists():
        print(f"ERROR: ReproBreak repo not found: {args.repro_root}", file=sys.stderr)
        return 2
    if not args.heal_out.exists():
        print(f"ERROR: heal output not found: {args.heal_out}", file=sys.stderr)
        return 2

    repro = load_reprobreak(args.repro_root)
    docker = repro["docker"]
    db = args.db or (args.repro_root / "data" / "ReproBreak.db")
    work_dir = args.work_dir or (args.repro_root / "data" / "reproduction_files")
    if not db.exists():
        print(f"ERROR: ReproBreak DB not found: {db}", file=sys.stderr)
        return 2

    try:
        client = docker.from_env(timeout=args.timeout_sec + 120)
        client.ping()
    except Exception as e:
        print(f"ERROR: Docker daemon not available: {e}", file=sys.stderr)
        print("Start Docker Desktop first: open -a Docker", file=sys.stderr)
        return 2

    id_filter = {int(x) for x in re.split(r"[,\\s]+", args.ids.strip()) if x} if args.ids.strip() else None
    rows = selected_rows(args.heal_out, id_filter, args.limit)
    print(f"selected v1-exact rows: {len(rows)}")

    out_rows: list[dict[str, Any]] = []
    counts = {
        "true_pass": 0,
        "resolver_correct_runtime_broken": 0,
        "infrastructure_fail": 0,
    }

    repos_path = work_dir / "repos"
    repos_path.mkdir(parents=True, exist_ok=True)

    for idx, row in enumerate(rows, 1):
        locator_id = int(row["id"])
        proposed = row["proposed_selector"]
        print(f"\\n[{idx}/{len(rows)}] id={locator_id} proposed={proposed}")

        info = repro["get_info"](str(db), locator_id)
        if not info:
            record = {"id": locator_id, "verdict": "infrastructure_fail", "error": "id_not_in_reprobreak_db"}
            out_rows.append(record)
            counts["infrastructure_fail"] += 1
            continue

        repo_name = info["repository_name"].split("/")[-1]
        reproduce_path = repos_path / repo_name
        repo_path = reproduce_path / repo_name
        reproduce_path.mkdir(parents=True, exist_ok=True)

        repro["clone_repo"](info["repository_name"], str(repo_path))
        repro["reset_repository"](str(repo_path))
        sh(["git", "-C", str(repo_path), "checkout", info["commit_sha"]])
        repro["extract_reproduction_files"](info["files_json"], str(reproduce_path), repo_name)
        optimize_repro_dockerfile(reproduce_path)

        image = f"{repo_name}:{info['commit_sha']}"
        if not client.images.list(filters={"reference": image}):
            print("  building Docker image...")
            image = repro["setup_base_image"](client, str(reproduce_path), info["commit_sha"])
            if image is None:
                record = {"id": locator_id, "verdict": "infrastructure_fail", "error": "image_build_failed"}
                out_rows.append(record)
                counts["infrastructure_fail"] += 1
                continue
        else:
            print("  Docker image exists; reusing")

        test_file_path = info["test_file_path"]
        absolute_repo_path = repo_path.resolve()
        absolute_test_file_path = absolute_repo_path / test_file_path
        command = f"bash /run_tests.sh /app/{test_file_path}"
        volume = {str(absolute_test_file_path): {"bind": f"/app/{test_file_path}", "mode": "ro"}}

        fixed_result = None
        if not args.no_fixed_baseline:
            print("  running fixed baseline...")
            fixed_result = run_e2e_with_logs(
                client, image, command, repro["parse_test_result"], volume, args.timeout_sec
            )
            print(f"    fixed_status={fixed_result.get('status')} exit={fixed_result.get('exit_code')}")

        patch_ok, patch_note = replace_once_in_line(
            absolute_test_file_path,
            int(info["line_no"]),
            info["new_locator"],
            proposed,
        )
        if not patch_ok:
            print(f"  patch failed: {patch_note}")
            verdict = "infrastructure_fail"
            patched_result = None
        else:
            print("  running patched HealReact selector...")
            patched_result = run_e2e_with_logs(
                client, image, command, repro["parse_test_result"], volume, args.timeout_sec
            )
            print(f"    patched_status={patched_result.get('status')} exit={patched_result.get('exit_code')}")
            verdict = classify(fixed_result, patched_result, patch_ok)

        counts[verdict] += 1
        out_rows.append({
            "id": locator_id,
            "commit_sha": info["commit_sha"],
            "test_file_path": test_file_path,
            "line_no": info["line_no"],
            "old_locator": info["old_locator"],
            "new_locator": info["new_locator"],
            "proposed_selector": proposed,
            "patch_note": patch_note,
            "fixed": fixed_result,
            "patched": patched_result,
            "verdict": verdict,
        })
        args.out.write_text(json.dumps(summary(out_rows, counts), indent=2))
        repro["reset_repository"](str(repo_path))

    args.out.write_text(json.dumps(summary(out_rows, counts), indent=2))
    print(f"\\noutput -> {args.out}")
    print(json.dumps(summary(out_rows, counts)["summary"], indent=2))
    return 0


def summary(rows: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    attempted = len(rows)
    true_pass = counts["true_pass"]
    denominator_all_93 = 93
    return {
        "summary": {
            "n_attempted": attempted,
            **counts,
            "true_pass_rate_attempted": round(true_pass / attempted * 100, 1) if attempted else 0.0,
            "end_to_end_repair_pass_rate_over_93": round(true_pass / denominator_all_93 * 100, 1),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    raise SystemExit(main())
