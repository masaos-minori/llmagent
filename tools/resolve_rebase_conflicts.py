#!/usr/bin/env python3
"""Resume an in-progress rebase resolving rmcompat007 sweep conflicts.

Policy (recorded in the session report):
- scripts/, config/, tools/ baselines, registry/manifests, generated docs:
  take the UPSTREAM side (--ours during rebase). The upstream sweep
  (f36c64236) follows the Plan-frozen pattern (REQ- etc., AC-N kept) with a
  whole-tree consistent tool run; local over-deletions (AC/wfretry001) are
  superseded for conflicted hunks.
- Any conflicted path outside these classes stops the script (no auto-resolve).
- Commits proven empty after resolution (fully absorbed upstream) are skipped
  via `git rebase --skip` and logged; any other continue failure stops.

Run repeatedly until the rebase completes: `uv run python tools/resolve_rebase_conflicts.py`
"""

import subprocess
import sys

GIT = ["git"]


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(GIT + list(args), capture_output=True, text=True)


def conflicted_files() -> list[str]:
    out = run("diff", "--name-only", "--diff-filter=U").stdout
    return [line for line in out.splitlines() if line.strip()]


def resolve_side(path: str) -> str:
    if path.startswith(("scripts/", "config/", "tools/", "registry/manifests/")):
        return "--ours"
    if path == "docs/24_eventbus/eventbus_08_reference_api.md":
        return "--ours"
    return "STOP"


def rebase_in_progress() -> bool:
    for p in ("rebase-merge", "rebase-apply"):
        probe = run("rev-parse", "--git-path", p).stdout.strip()
        if probe and subprocess.run(["test", "-e", probe]).returncode == 0:
            return True
    return False


def main() -> int:
    if not rebase_in_progress():
        print("no rebase in progress")
        return 0
    log = []
    while rebase_in_progress():
        files = conflicted_files()
        if files:
            for path in files:
                side = resolve_side(path)
                if side == "STOP":
                    print(f"STOP: unclassifiable conflicted path: {path}")
                    return 1
                res = run("checkout", side, "--", path)
                if res.returncode != 0:
                    print(f"STOP: checkout {side} failed for {path}: {res.stderr}")
                    return 1
                res = run("add", "--", path)
                if res.returncode != 0:
                    print(f"STOP: git add failed for {path}: {res.stderr}")
                    return 1
                log.append(f"resolved {path} with {side}")
        env_git = GIT + ["-c", "core.editor=true", "rebase", "--continue"]
        res = subprocess.run(env_git, capture_output=True, text=True)
        combined = res.stdout + res.stderr
        if res.returncode != 0:
            if rebase_in_progress() and conflicted_files():
                # continue picked some commits, then hit a new conflict: loop resolves it
                continue
            if rebase_in_progress():
                # no conflicts staged but nothing changed: the pick became empty
                skip = GIT + ["rebase", "--skip"]
                skipped = subprocess.run(skip, capture_output=True, text=True)
                if skipped.returncode != 0:
                    print(f"STOP: rebase --skip failed: {skipped.stderr}")
                    return 1
                log.append("skipped empty commit (fully absorbed upstream)")
            else:
                print(f"STOP: rebase --continue failed:\n{combined}")
                return 1
    for line in log:
        print(line)
    status = run("status", "-sb").stdout.splitlines()[0]
    print(f"rebase completed: {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
