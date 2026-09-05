## Goal
Remove `_print_semantic_cache_settings()` and its call from
`scripts/agent/commands/cmd_config_display.py` (`REQ-007`).

## Scope
- **In-Scope**: remove the `_print_semantic_cache_settings — Semantic cache settings`
  line from the module docstring's function-index list (line 10); remove
  `_print_semantic_cache_settings()`'s definition in its entirety (the method printing
  "Semantic cache:", `use_semantic_cache`, `sem_cache_threshold`, `sem_cache_max_size`);
  remove its call and the immediately preceding blank-line separator write from
  `_print_config_values()`, so the surrounding settings-block spacing convention
  (one blank line between each settings group) is preserved without a gap.
- **Out-of-Scope**: `_print_execution_settings()`/`_print_mcp_settings()` and every
  other `_print_*_settings()` method — confirmed unrelated by reading the full file;
  `_print_config_values()`'s other calls — unchanged except for the one call/blank-line
  pair removed.

## Assumptions
- Same hard ordering dependency as procedure documents `01`-`08`: this change must not
  be applied until `semcacherm` has landed — `ctx.cfg.rag.use_semantic_cache`/
  `semantic_cache_threshold`/`semantic_cache_max_size` (read by
  `_print_semantic_cache_settings()`) remain valid `RAGConfig` attributes until
  procedure document `03` (`scripts/agent/config_dataclasses.py`) removes them; this
  document's removal must land in the same or a later pass than `03`'s, not before it
  (removing the reader before the field still exists is harmless, but removing the
  field before the reader is gone would raise `AttributeError`).

## Design decisions
(per `skills/python-design/SKILL.md` Final Output §6, narrow bullet only)
- Remove the method, its docstring-index entry, and its call together in one document
  — `_print_semantic_cache_settings()` has exactly one caller
  (`_print_config_values()`) and no other reason to exist once the three fields it
  reads are gone.
- Remove the blank-line write immediately preceding the call (not the one following
  it) — `_print_config_values()`'s existing pattern is "print settings block, then
  write a blank-line separator, then print the next block"; removing the
  `_print_semantic_cache_settings(ctx)` call together with the separator write that
  precedes *this specific* call keeps every remaining settings block still separated
  by exactly one blank line, with no double-blank-line or no-blank-line artifact.

## Alternatives considered
N/A: straightforward removal of one method, its index entry, and its single call site.

## Implementation
### Target file
`scripts/agent/commands/cmd_config_display.py`

### Procedure
1. Re-verify `semcacherm` has landed (Assumptions) before proceeding; verify this
   document's implementation lands in the same or a later pass than procedure document
   `03` (`scripts/agent/config_dataclasses.py`).
2. Remove `  _print_semantic_cache_settings — Semantic cache settings` from the module
   docstring's function-index list (line 10).
3. Remove `_print_semantic_cache_settings()`'s definition in its entirety (the method
   signature, docstring, and its three `self._out.write(...)` calls printing "Semantic
   cache:", `use_semantic_cache`, `sem_cache_threshold`, `sem_cache_max_size`).
4. In `_print_config_values()`, remove the `self._out.write("")` blank-line-separator
   call that immediately precedes `self._print_semantic_cache_settings(ctx)`, together
   with that call itself — leaving `_print_execution_settings(ctx)` followed directly
   by the blank-line-separator write that previously separated
   `_print_semantic_cache_settings()` from `_print_mcp_settings()`.

### Method
Direct `Edit`: one docstring-line removal, one method-body removal, and one
call-site-plus-preceding-blank-line removal.

### Details
- Re-read `_print_config_values()`'s exact current call sequence immediately before
  editing (per Step 3a Adversarial Verification) to confirm which blank-line write
  precedes vs. follows the target call, since this Plan's own row evidence did not
  itemize the exact blank-line pairing — match on the method-call sequence, not on
  assumed line numbers.
- Confirm after editing: `rg -n "semantic_cache|_print_semantic_cache_settings"
  scripts/agent/commands/cmd_config_display.py` returns zero matches.

## Compatibility considerations
- The `/config` (or equivalent) CLI command's displayed output loses its "Semantic
  cache:" section — this is the intended behavior change; no other output section is
  affected.

## Security considerations
N/A: no security-sensitive code path is touched.

## Rollback considerations
- Revert via `git checkout` on this single file; safe to revert independently of
  procedure document `03` as long as this document's implementation is applied no
  earlier than `03`'s (per Assumptions) — a revert restores the reader while the field
  it reads may or may not still exist, but a revert scenario implies undoing the whole
  Plan together in practice.

## Validation plan
- `uv run pytest tests/agent/commands/test_cmd_config_char.py -v` (updated by its own
  procedure document) — passes; confirms the "Semantic cache:" output block and its
  three lines no longer appear.
- `rg -n "semantic_cache|_print_semantic_cache_settings"
  scripts/agent/commands/cmd_config_display.py` — zero matches.

## Completion criteria
- `_print_semantic_cache_settings()` no longer exists and is no longer called (Plan
  `AC-6`).
- `tests/agent/commands/test_cmd_config_char.py` passes.

## Out of scope
- `scripts/agent/config_dataclasses.py`'s `RAGConfig` fields this method reads
  (procedure document `03`).
- Every other `_print_*_settings()` method.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Blocked until `semcacherm` lands — see Assumptions |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by procedure document for `tests/agent/commands/test_cmd_config_char.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation deferred to `semcachedocs` |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Depends on `semcacherm`'s implementation landing first | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-007` (remove `_print_semantic_cache_settings()` and its call)
- **Source issue**: issues/20260902-150340_semcacheconfig_remove_semanticcache_settings_from_config_contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-141001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-185605
- **Related target files**: scripts/agent/commands/cmd_config_display.py
