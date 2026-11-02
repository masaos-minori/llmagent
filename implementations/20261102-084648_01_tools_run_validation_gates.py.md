## Goal
- Make `drift` compare the tool-backed pre-commit hooks with the gate mapping (`REQ-001`: hook parity), add gates for the seven hook-only checkers (`REQ-002`), and keep slow gates out of fast mode (`REQ-004`: measured cost).

## Scope
- In scope: hook parsing, hook checker-id derivation, the reviewed allowlist constant, `drift_report()` and `_run_drift()` changes, seven new `ROUTING_GATES` entries, the module docstring and `drift` help text, and (only if a measured gate is slow) a full-mode-only guard in `select_gates()`.
- Out of scope: merging gates and hooks, CI changes, changing what any checker verifies.

## Assumptions
- Source plan A1, A2, A3 (corrected in Step 3a of this cycle): PyYAML is importable; a hook `entry` of the form `python -m tools.<name>` reduces to the gate id form only after rewriting the `tools.<name>` token to `tools/<name>.py`; a hook flag becomes part of the id.
- Step 3a finding (Plan corrected): the planned id rule yields eight unmapped hooks, not seven. `check-compat-shims` (entry carries `--check-removed-names --check-doc-symbols`, id `check_compat_shims:--check-removed-names`) does not match the existing patternless gate `check_compat_shims`; it is allowlisted with a reason (Plan UNK-03). `workitem-traceability` (id `check_workitem_traceability:--active-only`) is mapped by a gate whose command carries `--active-only`.
- Step 3a finding: the new drift hook (`python -m tools.run_validation_gates drift`, row 03) is itself a tool-backed hook; hooks whose base tool is `run_validation_gates` are skipped via `_SELF_CHECKER_ID`, otherwise the check fails on itself.
- Fast-mode cost of `check_workitem_traceability --active-only` is unknown (Plan UNK-02); measured at implementation.
- Overlap (Step 2): `tools/run_validation_gates.py` is also targeted by the Plans filed from `flowimp001`, `flowimp003`, `flowimp010`, and `flowimp011`. Judged compatible: each adds one mapping entry for its own new routing row; this Plan changes `drift_report()`, `_run_drift()`, the allowlist, and adds seven entries. Sequencing dependency in one respect: a sibling's new routing row needs its own mapping entry in the same change, and the hook-parity check this Plan adds does not affect a tool without a hook. Whichever lands second rebases onto the other's `ROUTING_GATES` additions.

## Design decisions
- Parse the config with `yaml.safe_load` in a pure function that takes text, so tests need no file; `_run_drift()` does the file I/O and prints errors.
- The allowlist is a module constant of `(hook id, reason)` pairs; the check rejects an empty reason and an entry that names no hook in the config, so it cannot go stale silently.

## Alternatives considered
- Regex scan of the YAML: rejected, it hides malformed config (Plan Design).
- Compare hooks with `routing.md` only: rejected, `drift_report()` already forces mapping and `routing.md` to agree, so mapping covers both.
- Strip all flags when deriving a hook id: rejected, it would diverge from `Gate.checker_id` and hide a hook that runs stricter flags than its gate; an allowlist entry makes the difference explicit.

## Implementation
### Target file
`tools/run_validation_gates.py`

### Procedure
- Add `import yaml` and a module constant `_PRECOMMIT_CONFIG` (new) naming `.pre-commit-config.yaml`.
- Add `COMMIT_ONLY_HOOKS` (new), a tuple of `(hook_id, reason)`; initial content: `check-compat-shims` with the reason that the hook runs `--check-removed-names --check-doc-symbols` while the manual gate runs the checker with defaults and has no path patterns. Record any other checker found commit-only during the timing step (UNK-01) here with a reason.
- Add `_hook_checker_id(entry)` (new) and `parse_precommit_hooks(config_text)` (new) returning `(hooks, errors)` where `hooks` maps hook id to checker id.
- Extend `drift_report(routing_text, precommit_text=None)` and `_run_drift()` so the hook comparison runs when the config text is supplied and drift exits non-zero on any error.
- Append seven `Gate` entries to `ROUTING_GATES` (table below).
- If the timing step shows a gate is slow in fast mode, set that gate's `mode=MODE_FULL` and make `select_gates()` skip routing gates whose `mode` is `MODE_FULL` when the run mode is fast; record the measured seconds and reason in a comment on the gate.
- Update the module docstring (`drift` bullet) and the `drift` subparser help to mention the hook comparison.

### Method
- `_hook_checker_id(entry: str) -> str | None`: split `entry` on whitespace; rewrite any token matching `^tools\.([A-Za-z0-9_]+)$` to `tools/<name>.py`; if no token then matches `_TOOL_PY_RE`, return `None` (not tool-backed: `bash -c ...`, `uv run mypy ...`). A token that starts with `tools.` or `tools/` but fails both patterns is reported as an error by the caller (unparseable tool-backed entry). Return `_checker_id_from_command(tuple(tokens))`.
- `parse_precommit_hooks` (new): `yaml.safe_load`; on `yaml.YAMLError`, a non-mapping document, a missing or non-list `repos`, or a hook without a string `id`, append one error message and continue or return. Skip hooks with no `entry` (remote repos such as ruff). Skip a derived id whose base (text before the first `:`) equals `_SELF_CHECKER_ID`.
- In `drift_report`: `allowed = {hook_id for hook_id, _ in COMMIT_ONLY_HOOKS}`; for each hook whose checker id is not in `{gate.checker_id for gate in ROUTING_GATES}` and whose hook id is not in `allowed`, append `pre-commit hook has no gate mapping or allowlist entry: {hook_id} ({checker_id})`. Append an error for an allowlist entry with a blank reason and for an allowlist hook id absent from the config.
- `_run_drift`: read `routing.md` as today and `.pre-commit-config.yaml` from the repo root; an `OSError` on either prints `ERROR: cannot read ...` to stderr and returns 1 (REQ-001: unreadable config).

### Details
- Gate entries (name: patterns; command): `check_adr_invariant_matrix`, `check_adr_reference`, `check_adr_structure`: `("*.py", "**/*.py", "*.md", "**/*.md")` (mirrors `types_or: [python, markdown]`; `**/` requires a directory so the root-level forms are listed explicitly, the convention `check_module_size` already uses); `check_known_deviation_sync`: `("docs/*.md", "docs/**/*.md")`; `check_plan_target_overlaps`: `("plans/*.md",)`; `check_conftest_integrity`: `("tests/*conftest*", "tests/**/*conftest*")`; `check_workitem_traceability`: patterns `issues/`, `plans/`, `implementations/` each with `*.md` and `**/*.md`, command `uv run python tools/check_workitem_traceability.py --active-only`. All others use `("uv", "run", "python", "tools/<name>.py")`, `source=SOURCE_ROUTING`, `mode=MODE_FAST`. Each checker accepts no required argument (verified: only an optional `--format`, plus the traceability `--active-only`).
- Timing step: after adding the gates, time `uv run python tools/run_validation_gates.py` on a docs-only diff and on a diff touching one `.py` plus one `.md`, before and after, and record the added seconds in the implementing commit message and the Plan's Execution Status notes. Time `check_workitem_traceability.py --active-only` by itself (UNK-02).

## Compatibility considerations
- Existing mapping entries, ids, and `routing.md` rows are unchanged; `drift_report(routing_text)` called with one argument keeps its current behavior, so existing tests and any caller still pass.
- The default gate run only gains gates. The ADR gates now run on any `.py` or `.md` diff; the measured cost decides whether they stay in fast mode.
- `checker_id` format is unchanged.

## Security considerations
- N/A: no new trust boundary. `yaml.safe_load` only, never `yaml.load`; the config is a repository file. Gate commands are fixed argv tuples run without a shell, as today.

## Rollback considerations
Revert the commit. No persisted state or migration is involved.

## Validation plan
- `uv run pytest tests/tools/test_run_validation_gates.py -v` (row 02 adds the cases).
- `uv run python tools/run_validation_gates.py drift` reports no unmapped hook on the live repository.
- `uv run ruff format tools/run_validation_gates.py`; `uv run ruff check tools/run_validation_gates.py`; `uv run mypy tools/run_validation_gates.py`; `uv run bandit tools/run_validation_gates.py` (pre-existing bandit findings are recorded, only new ones count).
- Tool lint sequence of `routing.md` "Adding a new tool" on the changed tool.

## Completion criteria
- `drift` reads the hook config, and reports every tool-backed hook with neither a mapping nor an allowlist entry; malformed or unreadable config exits non-zero with a message.
- The seven gates exist with filter-mirroring patterns; `check_workitem_traceability` carries `--active-only`; `check-compat-shims` is allowlisted with a reason; the self-hook is excluded.
- Added fast-mode time is measured and recorded; a slow gate (if any) is full-mode only with the reason in a comment.

## Out of Scope
- The `routing.md` rows (row 04), the pre-commit hook (row 03), tests (row 02), and docs (rows 05, 06) belong to their own documents.
- Fixing the stale `--fast` / "stops on first Fail" wording in the `TOOL_DESCRIPTIONS.md` entries is not part of this change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Includes the timing step |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests live in the row 02 document (`tests/tools/test_run_validation_gates.py`); run them here |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tool lint sequence, `drift`, tool tests |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: module docstring and help text only; other docs are rows 04 to 06 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`
- **Source issue**: issues/20261030-191302_flowimp005_gates-hook-parity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075445_flowimp005_gates-hook-parity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084648
- **Related target files**: tools/run_validation_gates.py
