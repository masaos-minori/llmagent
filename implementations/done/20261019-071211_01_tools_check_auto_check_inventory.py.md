## Goal

Create a new standalone checker `tools/check_auto_check_inventory.py` that cross-references every
auto-check documented as `Auto` against an actual runnable script under `tools/` or `scripts/`,
flagging documented-but-absent or name-drifted entries. Non-blocking, `Warning`-level. This closes
the documented `Partial` gap for GV-014.

## Scope

- **In-Scope**:
  - Parse documented auto-check tool references from the authoritative documents.
  - Verify each reference resolves to an existing, runnable script discovered dynamically under
    `tools/` or `scripts/`.
  - Flag documented-but-absent or name-drifted entries at `Warning`.
  - Add unit tests with documented-but-missing and valid fixtures.
- **Out-of-Scope**:
  - Changing which documents are authoritative sources of auto-check claims.
  - Adding new auto-checks.

## Assumptions

- The checker is `Warning`-level and non-blocking, consistent with GV-014's existing gate.
- A documented tool token is resolved by basename (e.g. `check_foo.py`) against files in
  `tools/` and `scripts/`; a relative path token is resolved against the repo root.
- The dominant `tools/check_*.py` convention is string severity (`Issue(severity: str)` with
  `"WARNING"`/`"ERROR"`); follow it (the `Severity` HIGH/MEDIUM/LOW enum is used only by
  `check_canonical_source_conflicts.py`).
- The authoritative input set is `governance_04` `Method = Auto` cells and `routing.md`'s tool
  table; `tools/TOOL_DESCRIPTIONS.md` is treated as optional/confirmed during implementation.

## Design decisions

- New standalone CLI following the `tools/check_*.py` convention (argparse, `Issue` results,
  string `Warning`/`ERROR` severities, `main() -> int` + `sys.exit(main())`).
- Discover tools dynamically by listing `tools/` and `scripts/` at runtime (no hardcoded names).
- Exclude non-path tokens and known alternative invocation names (pre-commit hook names, CI job
  names) to avoid false positives.
- Name drift reported as a non-blocking hint (fuzzy candidate), not a hard failure.

## Alternatives considered

- Hardcoding the list of expected tool filenames — rejected: REQ-002 requires dynamic discovery;
  hardcoding would drift as tools are added.

## Implementation

### Target file

`tools/check_auto_check_inventory.py` (new)

### Procedure

1. Scaffold the module following an existing `tools/check_*.py` (e.g. `check_docs_quality.py`):
   argparse CLI, `Issue` results with string severity, `main() -> int` ending in
   `sys.exit(main())`.
2. Implement authoritative-source parsing (UNK-01): extract tool references from
   `governance_04` matrix rows whose method column is `Auto` (capture the backtick-quoted tool
   token) and from `routing.md`'s tool-table rows (capture backtick-quoted `tools/...` /
   `scripts/...` paths).
3. Implement dynamic tool discovery: list files under `tools/` and `scripts/` at runtime; build a
   set of basenames and full relative paths.
4. Implement resolution + flagging (UNK-02/03): for each documented token, resolve by basename or
   relative path. If no match, flag at `Warning` (documented-but-absent). If only a close
   (edit-distance) candidate exists, emit a non-blocking drift hint. Exclude non-path tokens and
   known alternative invocation names.
5. Report `Warning`-only; preserve the non-blocking contract.

### Method

- **CLI.** Mirror `check_docs_quality.py`: `argparse.ArgumentParser`, optional `--root` (default
  repo root), `def main(argv=None) -> int` ending in `sys.exit(main())`.
- **Parsing.** Regex for backtick-quoted tokens within `Method = Auto` matrix cells and
  `routing.md` tool-table cells; keep only tokens that look like file paths (`*.py`, `tools/...`,
  `scripts/...`).
- **Discovery.** `Path("tools").iterdir()` + `Path("scripts").iterdir()`; collect basenames and
  relative paths. Fail safe if a directory is missing.
- **Resolution.** Exact basename match → OK. Relative-path token matched against relative paths →
  OK. Otherwise `Warning` (absent). Edit-distance candidate within a small threshold → non-blocking
  drift hint.
- **Exclusions (UNK-02).** Skip tokens that are natural language, or that match a small allowlist
  of known alternative invocation names (pre-commit hook names, CI job names). Document the
  allowlist in-code.

### Details

- `REQ-001`: documented tool refs are parsed from the authoritative documents.
- `REQ-002`: tool discovery lists `tools/`/`scripts/` dynamically (no hardcoded names).
- `REQ-003`: a documented tool with no matching script, or whose name has drifted, is flagged at
  `Warning`.
- `REQ-004`: no false positives on the current corpus, including differently-named invocations.
- **UNK-01:** fix the input set to `governance_04` `Method = Auto` cells + `routing.md` tool
  table; document it in-code; treat `TOOL_DESCRIPTIONS.md` as optional/confirmed during impl.
- **UNK-02:** exclude non-path tokens and maintain a small allowlist of known alternative
  invocation names; fail safe toward no false positive.
- **UNK-03:** start with exact basename/path match (flag absent); add fuzzy candidate as a
  non-blocking hint.

### Implementation notes (defects found during adversarial verification)

Two runtime/type defects were caught by the unit-test pass and fixed in place before validation
completed. Both are documented here per memo3 item 2 (correct procedure docs on findings).

- **`_path_tokens` called without `line_no`.** `parse_governance_rows` / `parse_routing_rows`
  called `_path_tokens(" ".join(cells))` and passed a stray `line_no` to `findings.extend(...)`.
  `_path_tokens(line, line_no)` requires both args, so every parser call raised
  `TypeError` at runtime. Fixed by passing `line_no` into `_path_tokens` and dropping the stray
  argument from `extend`. Verified by the corpus run, which previously never executed.
- **`Path.sep` does not exist.** `ToolIndex.discover` used
  `str(py.relative_to(root)).replace(Path.sep, "/")`; `Path` has no `sep` attribute, so discovery
  raised `AttributeError`. Replaced with `py.relative_to(root).as_posix()`.
- **`object` type-hint for parsers.** `audit`/`_default_sources` typed parse functions as
  `object`, which mypy rejected (`"object" not callable`, operator error not covered by the
  `# type: ignore`). Replaced with a dedicated `ParseFn = Callable[[str], list[tuple[str, int]]]`
  alias, removing the suppression and the ruff `UP037` quoted-forward-ref finding on
  `ToolIndex.discover`'s return annotation.
- Discovery uses `rglob("*.py")` (recursive) rather than a single-level `iterdir()`, so nested
  tool paths resolve via `rel_paths` as the corpus test expects.

## Compatibility considerations

New CLI entry point only; no external callers. `Warning`-only findings preserve the non-blocking
contract.

## Security considerations

N/A: reads local `docs/`, `routing.md`, and lists `tools/`/`scripts/`; applies read-only regexes.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tools/check_auto_check_inventory.py` | Format/lint | `uv run ruff format tools/ && uv run ruff check tools/` | Clean |
| `tools/check_auto_check_inventory.py` | Type check | `uv run mypy --no-namespace-packages tools/` | Clean |
| `tools/check_auto_check_inventory.py` | Security | `uv run bandit -r tools/ -c pyproject.toml -ll` | No high/medium |
| `tools/check_auto_check_inventory.py` | Architecture | `PYTHONPATH=scripts uv run lint-imports` | No boundary violations |
| `tools/check_auto_check_inventory.py` | Unit + corpus | `uv run pytest tests/tools/test_check_auto_check_inventory.py` then corpus run | Absent flagged; corpus clean |
| Whole change | Full regression | `uv run pytest` + `uv run pre-commit run --all-files` | No new failures |

## Completion criteria

- The checker parses authoritative auto-check references, discovers tools dynamically, and flags
  documented-but-absent/drifted entries at `Warning`.
- Unit tests cover documented-but-missing and valid fixtures plus a corpus run with zero false
  positives.
- The GV-014 matrix row reports the audit as automated with the follow-up note cleared.

## Out of scope

Changing which documents are authoritative sources of auto-check claims and adding new
auto-checks.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261019 | 20261019 | REQ-001/002/003; UNK-01/02/03. Two defects fixed during verification (see Implementation notes): `_path_tokens` missing `line_no` arg, `Path.sep` AttributeError. |
| 2 | Add or update tests per Validation plan | Completed | 20261019 | 20261019 | REQ-001/002/003/004. 17 tests incl. real-corpus zero-finding assertion. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261019 | 20261019 | ruff/mypy/bandit/lint-imports clean; targeted + full suite green (1 pre-existing unrelated github failure). diff-cover unmeasurable: coverage config instruments only `scripts/`, not `tools/`. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261019 | 20261019 | Out of scope for this procedure; GV-014 doc update handled by procedure 03 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004` (new checker: parse documented auto-check refs, discover tools dynamically, flag absent/drifted at `Warning`)
- **Source issue**: `issues/done/20261018-173319_gov014_automate-audit-of-auto-checks-documented-as-implemented.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261018-181700_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-071211
- **Related target files**: `tools/check_auto_check_inventory.py`
