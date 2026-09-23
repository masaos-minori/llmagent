## Goal

Implement REQ-003 (`plans/20260923-152824_plan.md`) in
`tools/check_docs_consistency.py`: update `_CONF_D_DOC` for the
directory-qualified `rel_path` that `discover_md_files()` now produces once
seq 01 (`tools/_docs_consistency_lib.py`) lands.

## Scope

Modify only `tools/check_docs_consistency.py` to update `_CONF_D_DOC`'s value
from `"01_overview-files-06-misc.md"` to
`"01_overview/01_overview-files-06-misc.md"`.

## Assumptions

- This document depends on seq 01 (`tools/_docs_consistency_lib.py`) having
  already landed — `_CONF_D_DOC` is compared via `f.rel_path == _CONF_D_DOC`
  inside `check_conf_d_listing()`, and `rel_path` only becomes
  directory-qualified once `discover_md_files()`'s glob is recursive.
- `main()`'s own domain-dispatch logic (`DOMAIN_PREFIXES`, the
  `discover_md_files(docs_dir, prefix=prefix)` call at line ~704) needs no
  change — `docs_dir` stays the flat `docs/` root, and seq 01's recursive
  glob already makes it find every domain's files regardless of subfolder.
  Confirmed via Read during the source Plan's drafting: `DOMAIN_PREFIXES`
  covers 5 domains (`agent`, `mcp`, `rag`, `deployment`, `overview`), not
  just the 3 the source Issue named.
- `check_schema_drift()`'s two `discover_md_files()` calls
  (`prefix="90_shared_04_"`, `prefix="05_agent_09_"`) need no change either —
  both pass the flat `docs_dir` root with a prefix, unaffected by the
  recursive-glob fix the same way `main()`'s own call is.

## Design decisions

- Update only the one constant identified — no other logic in this large
  file changes. `check_conf_d_listing()`'s own `discover_md_files(docs_dir,
  prefix=_CONF_D_DOC.split("_", 1)[0])` call (prefix `"01"`) is unaffected by
  the constant's new value, since the prefix computation happens on the
  string literal, not on a re-derivation from `_CONF_D_DOC` at call time —
  confirm this during implementation (see Alternatives considered).

## Alternatives considered

- Changing `check_conf_d_listing()`'s prefix-derivation logic
  (`_CONF_D_DOC.split("_", 1)[0]`) instead of just updating the constant:
  rejected unless verification during implementation shows the split would
  produce a different (wrong) prefix once `_CONF_D_DOC` includes a directory
  segment — in that case, derive the prefix from `Path(_CONF_D_DOC).name`
  instead of the raw string, to keep the split operating on the bare
  filename only.

## Implementation

### Target file

`tools/check_docs_consistency.py`

### Procedure

1. Locate `_CONF_D_DOC = "01_overview-files-06-misc.md"` (near line 469).
2. Change its value to `"01_overview/01_overview-files-06-misc.md"`.
3. Re-check `check_conf_d_listing()`'s `_CONF_D_DOC.split("_", 1)[0]` prefix
   derivation (line ~643) against the new value: `"01_overview/01_overview-files-06-misc.md".split("_", 1)[0]`
   evaluates to `"01"` still (the split occurs on the first underscore,
   which is still inside the `"01_overview"` segment, before any `/`) — if
   implementation confirms this still yields `"01"`, no further change is
   needed there; if not, change the derivation to split on
   `Path(_CONF_D_DOC).name` instead.

### Method

One `Edit` call to the constant's value; a verification-only re-check of the
one dependent line (no edit expected there unless the split logic proves
wrong).

### Details

Current:
```python
_CONF_D_DOC = "01_overview-files-06-misc.md"
```

After modification:
```python
_CONF_D_DOC = "01_overview/01_overview-files-06-misc.md"
```

## Compatibility considerations

- Depends on seq 01 landing first (see Assumptions) — this document's own
  Validation plan below only fully passes once both have landed together.
- No change to `DOMAIN_PREFIXES`, `main()`, or any of the 5 domains'
  dispatch logic.

## Security considerations

No security impact.

## Rollback considerations

1. Revert `_CONF_D_DOC` to its original bare-filename value.
2. No other state to unwind.

## Validation plan

Run `uv run pytest tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py -q` (both confirmed hermetic — should pass unchanged, since neither exercises `check_conf_d_listing()` against a moved file). Manually verify `check_conf_d_listing()` against a synthetic tree with `01_overview-files-06-misc.md` placed under a `01_overview/` subdirectory once seq 01 has landed.

## Completion criteria

- `_CONF_D_DOC` equals `"01_overview/01_overview-files-06-misc.md"`.
- `check_conf_d_listing()`'s prefix derivation still yields `"01"` (confirmed
  or corrected per Procedure step 3).
- `uv run pytest tests/tools/test_check_agent_docs_consistency.py tests/tools/test_check_docs_consistency_port.py -q` passes.

## Out of scope

- `DOMAIN_PREFIXES`, `main()`'s domain-dispatch logic, or any of the 5
  domains' own check functions beyond `check_conf_d_listing()`'s one
  constant dependency.
- Any physical `docs/` file move.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260923-154822 | 20260923-154822 | Step3 stale_detector false-positives (_CONF_D_DOC, DOMAIN_PREFIXES) confirmed via grep against actual source (both exist) -- tool mis-scoped due to other file paths in the same paragraph; bypassed. _CONF_D_DOC updated; split('_',1)[0] prefix derivation confirmed still yields '01' with the new value, no further edit needed. |
| 2 | Add or update tests per Validation plan | Completed | 20260923-154822 | 20260923-154822 | No new test needed beyond seq01's coverage; confirmed via test_check_agent_docs_consistency.py + test_check_docs_consistency_port.py (both unaffected, 21 passed). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260923-154822 | 20260923-154822 | ruff/mypy/bandit pass. All 5 domains (agent/mcp/rag/deployment/overview) run identically before/after this change (diffed byte-for-byte via git stash), zero regression. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260923-154822 | 20260923-154822 | N/A: no docs/00_index.md task-scope mapping for tools/check_docs_consistency.py. |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/done/20260923-140602_docsreorg02_make-docs-domain-checkers-subfolder-aware.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260923-152824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260923-153716
- **Related target files**: tools/check_docs_consistency.py