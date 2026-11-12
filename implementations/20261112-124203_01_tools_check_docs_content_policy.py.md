## Goal
Extract self-contained helpers out of `tools/check_docs_content_policy.py` so it shrinks, then widen `_INDEX_TABLE_HEADER_RE` so a hand-written `| File | Class/Function | Signature | Summary |` table is flagged while guarded blocks stay exempt (`REQ-001`, `REQ-007` / `AC-1`, `AC-7`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Baseline (checked 2026-11-12): the tool is 33240 bytes and grandfathered at that size in `tools/check_module_size_tools_baseline.txt`, so growth fails the gate; `_INDEX_TABLE_HEADER_RE` (line 47) requires a first column `Function|Method|Class` and a last column `Signature|Description`; the exemption for `AUTO-GENERATED` guards is applied by `_is_guard_start`/`_is_guard_end` in the file-walking loop and stays.
- A trial of the widened pattern below matches the `eventbus_08` header, matches nothing else outside guarded blocks in the current corpus, and does not match two-column or `| File | Purpose | Description |` tables (checked in Step 3a).
- `tests/tools/test_check_docs_content_policy.py` imports `DocFile` and every `check_*` function from `tools.check_docs_content_policy`; an extracted name must stay importable from it (import it back, used) or the test import changes in row 07.
- Overlap: none among open Plans for this file. The finding is a WARNING; `--strict` (CI) exits 1 on it.
- Execution order: this Plan lands after the procedures of adrrev015, adrrev017, and adrrev011 are executed (Plan `Depends on`); `plan_dependency_order.py` reports this Plan `ready` because those Plans are archived, but their procedures may still be unexecuted, so the corpus smoke run in Phase 4 decides.

## Design decisions
- Extract leaf nodes only (for example `_is_guard_start`, `_is_guard_end`, `DocFile`, `discover_all_md_files`), chosen from `module_nodes.py measure` output; do not move the regex constants that the checks read.
- Widen the regex with one added alternative instead of a looser first column, to avoid false positives on ordinary `File` tables.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`tools/check_docs_content_policy.py`

### Procedure
1. `uv run python tools/module_nodes.py measure tools/check_docs_content_policy.py`; choose nodes (UNK-03).
2. Create `tools/_docs_content_policy_helpers.py` (row 02) and move the nodes with `module_nodes.py extract --src tools/check_docs_content_policy.py --dest tools/_docs_content_policy_helpers.py --name <node>`; import them back as `from tools._docs_content_policy_helpers import ...`.
3. Run `tests/tools/test_check_docs_content_policy.py` and the size gate; then (row 03) record the new size.
4. After the failing fixture tests of row 07 exist, widen `_INDEX_TABLE_HEADER_RE`.

### Method
- New pattern: `^\s*\|\s*(?:(?:Function|Method|Class)\s*\|.*|(?:File|Module)\s*\|\s*(?:Class|Function)[^|]*\|.*)\|\s*(?:Signature|Description|Summary)\s*\|` with `re.IGNORECASE`.
- The existing guarded-block skip (`in_auto_generated`) is untouched, so the same header inside a guard is exempt.
- Run `uv run python tools/module_nodes.py compare` to confirm moved functions are unchanged.

### Details
- The extraction must come first so the file never grows past its recorded size; after both changes the file is smaller than 33240 bytes.
- Smoke run: `uv run python tools/check_docs_content_policy.py --strict` against real `docs/` must still pass.

## Compatibility considerations
N/A: internal tool; the detection widens by one header shape and guarded blocks stay exempt.

## Security considerations
N/A: a read-only documentation checker.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_check_docs_content_policy.py -q`.
- `uv run ruff format <file>`, `uv run ruff check <file>`, `uv run mypy <file>`, `uv run bandit <file>` — clean.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` — pass.
- `uv run python tools/check_docs_content_policy.py --strict` on real `docs/` — pass.

## Completion criteria
- The `eventbus_08` header shape is flagged outside a guard and exempt inside one; the tool is below 33240 bytes; tests, size gate, ruff, mypy, bandit pass.

## Out of Scope
- Fixing documents the checker flags (owning Plans); a semantic contradiction detector; CI or pre-commit wiring.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the failing test first and confirm it fails against the unmodified tool | Pending | — | — | |
| 2 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the tests, then the validation sequence (`rules/toolchain.md`) for the changed tool | Pending | — | — | |
| 4 | Smoke-run the tool against the real `docs/` corpus and record the result | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` / `REQ-007` — extract helpers, then widen the inventory-table header pattern
- **Source issue**: issues/20261109-113351_adrrev018_docs-checker-harden.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-111505_adrrev018_docs-checker-harden.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-124203
- **Related target files**: `tools/check_docs_content_policy.py`
