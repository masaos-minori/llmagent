# Implementation: Full verification of the `mcp` → `mcp_servers` rename and launcher (Phase 5)

## Goal

Confirm that the Phase 1-4 changes (package rename, new launcher, deploy-skill update, docs update) leave the codebase fully consistent: no stray references to the old package name, no architecture-boundary regressions, no test regressions, and the new launcher actually solves the original `ModuleNotFoundError` in the dev venv.

## Scope

**In:**
- Run the full validation sequence from `rules/toolchain.md` against the renamed tree
- Manually exercise `scripts/mcp_launcher.py` against a real server in the dev venv to confirm the original bug is fixed
- Confirm the port-collision guard against a live agent-managed server
- Confirm `docs`/`mcp` consistency-checker tooling passes

**Out:**
- No new functional changes — this phase is verification-only; any failure found here should be routed back to the relevant Phase 1-4 implementation, not patched ad hoc within this document's scope

## Assumptions

1. This document depends on Phases 1-4 having already landed (package rename, launcher, deploy-skill doc update, mcp docs update).
2. The dev venv (`.venv`) has the PyPI `mcp` SDK installed transitively via `semgrep` (the dev dependency group) — this is the environment in which the original bug reproduces and where the fix must be confirmed; the production venv (`/opt/llm/venv`) does not have this dependency and was never affected.

## Implementation

### Target file

None (verification-only; no files are modified by this phase).

### Procedure

1. `PYTHONPATH=scripts uv run lint-imports` — confirm 0 violations under the renamed `.importlinter` contracts (Phase 1).
2. `uv run pytest` — confirm no new failures across the full suite (the rename touches ~97 files' imports; a full run, not a targeted subset, is required here specifically because the blast radius spans nearly every test file that imports `mcp.*`).
3. `python tools/check_mcp_docs_consistency.py` (verify actual entry-point name at runtime, since it may have shifted with other concurrent doc restructuring) — confirm doc/code consistency checks pass.
4. In the dev venv, run `uv run python scripts/mcp_launcher.py git` and confirm:
   - No `ModuleNotFoundError: No module named 'mcp.audit'` (the original bug)
   - `curl -s http://127.0.0.1:8014/health` (or git-mcp's configured port) returns HTTP 200
5. Run `uv run python scripts/mcp_launcher.py --list` and confirm all 10 server keys are printed.
6. With the agent running and git-mcp already active under it, run `uv run python scripts/mcp_launcher.py git` again (without `--force`) and confirm the port-collision guard prints a warning and exits non-zero rather than attempting to bind the already-used port.
7. `uv run ruff check scripts/mcp_servers scripts/mcp_launcher.py` — 0 errors.
8. `uv run mypy scripts/` — no new errors introduced by the rename (compare against the pre-existing baseline error count established in prior sessions, e.g. via `git stash` comparison, since this repository has known pre-existing mypy debt unrelated to any single change).
9. `uv run pre-commit run --all-files` — final gate; if the pre-existing repo-wide mypy debt blocks this hook (a known, previously-encountered condition in this repository), request explicit user approval before using `SKIP=mypy`, consistent with prior precedent in this project — never use `--no-verify`.

### Method

Sequential execution of the standard validation toolchain (`rules/toolchain.md`) plus the plan's own manual verification steps (7节/8节 in the source plan) — no code is written in this phase.

### Details

- Step 2 (full `pytest`, not a targeted file subset) is called out explicitly because this is the one phase in the plan where a narrow test selection would be insufient: the rename's blast radius is "every file that imports the renamed package," which cuts across nearly all test modules, not a localized subset.
- Step 6 assumes an agent instance is actually running with git-mcp active; if no such instance is available at implementation time, this specific check may need to be deferred to a manual QA pass rather than blocking the rest of Phase 5's automated checks.

## Validation plan

```bash
PYTHONPATH=scripts uv run lint-imports
uv run pytest
python tools/check_mcp_docs_consistency.py
uv run python scripts/mcp_launcher.py --list
uv run python scripts/mcp_launcher.py git
curl -s http://127.0.0.1:8014/health
uv run ruff check scripts/mcp_servers scripts/mcp_launcher.py
uv run mypy scripts/
uv run pre-commit run --all-files
```

Expected outcome: architecture contracts hold, full test suite has no new failures, MCP doc/code consistency checks pass, standalone launch works without the original `ModuleNotFoundError`, and the port-collision guard behaves as designed.
