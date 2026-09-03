## Goal
Add semantic definitions for 7 compatibility-related terms (Backward Compatibility,
Operational Fallback, Default, Lenient Parsing, Migration, Obsolete, Dead Code) to
`docs/00_governance_02_documentation-metadata.md`'s Terminology Glossary, each with
one project-relevant example drawn from confirmed current repository behavior.

## Scope
- **In-Scope**: `docs/00_governance_02_documentation-metadata.md`'s
  `## Terminology Glossary` section only — adding the 7 new term definitions.
- **Out-of-Scope**: the existing 11-row spelling/capitalization table (unchanged);
  clarifying the existing `Deprecated` evidence label — that belongs to
  `docs/00_governance_04_documentation-checks.md` (seq 02 of this Plan, per REQ-001's
  2026-09-03 correction); `docs/00_governance_04_documentation-checks.md` (seq 02)
  and `docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03) have
  their own implementation-procedure documents.

## Assumptions
- The existing `## Terminology Glossary` section (lines 151-176, confirmed
  2026-09-03: an 11-row spelling/capitalization table plus `### Usage Rules`)
  contains no compatibility-related semantic terms — re-verified by direct `Read`
  immediately before writing this document, matching the Plan's own evidence with
  no drift.
- `Deprecated` is not one of the 7 terms defined here — the Plan's REQ-001 was
  corrected 2026-09-03 to attribute the existing `Deprecated` evidence label's
  clarification to `docs/00_governance_04_documentation-checks.md`'s
  `### 10. Evidence Label Validation` section instead (seq 02's own scope).

## Design decisions
- **New subsection, not a new column on the existing table**: the existing
  11-row table's columns (`Term`/`Preferred Form`/`Alternative Forms`/`Notes`)
  encode spelling/capitalization conventions, not semantic definitions with
  examples — forcing a `Definition`/`Example` pair into that schema would either
  overload the `Notes` column illegibly or require restructuring a table this Plan
  does not target. A new `### Compatibility and Lifecycle Terminology` subsection
  with its own `Term | Definition | Example` table keeps both concerns legible and
  independently maintainable.
- **Every example is grounded in a `grep`/`Read`-verified current repository
  fact**, not an invented illustration, per this Plan's own Reference Files
  evidence and this row's own re-verification (see Details below for each term's
  citation) — consistent with `rules/ai-execution.md` Repository Tool Usage's
  evidence requirement.
- **`Obsolete` vs. `Dead Code` are kept as two distinct terms with two distinct
  examples** (not merged into one), because they describe different observable
  states: `Obsolete` (`read_json_file()`) is a name still reachable and callable,
  just no longer the current production path for its original purpose; `Dead
  Code` (`is_side_effect()`) has zero call sites anywhere in current source — the
  Plan's own `REQ-003` design (asymmetric detection: grep-absence for fully-removed
  names vs. context-aware check for demoted-but-present names) depends on this
  same distinction being drawn correctly in the Glossary first.
- **`Dead Code`'s example note flags, but does not fix, an unrelated stale
  docstring** (`scripts/shared/tool_constants.py`'s comment still describes
  `is_side_effect()` as "the sole first-checked classifier used by
  `ToolExecutor.execute()`", contradicted by zero actual call sites and by
  `docs/04_mcp_03_01_dispatch-and-routing.md`'s own accurate "deprecated... no
  longer used" description) — this is a genuine, pre-existing documentation
  inconsistency discovered during this row's evidence-gathering, but it is in
  neither this Plan's nor the sibling `toolroutedoc` Plan's Implementation Target
  Files, so it is reported here as a Plan Gap rather than fixed unilaterally.

## Alternatives considered
- **Add an 8th term, `Deprecated`, duplicating the existing evidence label's
  concept in the Glossary** — rejected: this would create two differently-scoped
  "Deprecated" definitions in two different governance documents (an evidence-label
  sense in governance_04, a compatibility-vocabulary sense here), risking exactly
  the vocabulary drift this Plan's own Reason for Change warns against. The
  corrected REQ-001 instead clarifies the one existing definition in place.
- **Invent illustrative (non-repository) examples for terms lacking an obvious
  current instance** — rejected in favor of spending the extra `grep`/`Read` effort
  to find a real one for every term (see Details), since a fabricated example
  would misrepresent "project-relevant" and could not be independently verified by
  a future reader.

## Implementation
### Target file
`docs/00_governance_02_documentation-metadata.md`

### Procedure
1. Re-read `## Terminology Glossary` (lines 151-176) immediately before editing to
   reconfirm no drift (done above; no drift found).
2. Insert a new `### Compatibility and Lifecycle Terminology` subsection
   immediately after the existing `### Usage Rules` subsection (before
   `## Link Rules`), containing the table in Details below.

### Method
Direct text edit (e.g. via the `Edit` tool) inserting the new subsection between
the end of `### Usage Rules` and the `## Link Rules` heading.

### Details

**Insertion point** (anchor — the blank line between `### Usage Rules`'s last
bullet and `## Link Rules`):

Before:
```
7. **Subsequent occurrences**: Use only the preferred form after first definition.

## Link Rules
```

After:
```
7. **Subsequent occurrences**: Use only the preferred form after first definition.

### Compatibility and Lifecycle Terminology

| Term | Definition | Example |
|------|------------|---------|
| Backward Compatibility | Preserving an old public interface or API surface so existing callers continue to work unchanged after the underlying implementation changes. | `scripts/agent/__init__.py`'s module docstring: "Exports all component classes and the AgentREPL facade for backward compatibility" — old import paths through the package's `__init__.py` keep working. |
| Operational Fallback | A runtime behavior that automatically switches to an alternate code path when a primary path fails or is unavailable, without requiring manual intervention. Distinct from Backward Compatibility (a static interface-preservation property): a fallback is a live, per-call runtime decision. | RAG's `call_rag_service()` falls back to in-process execution when the remote RAG service call fails (`docs/03_rag_03_01_query_pipeline-overview.md`). |
| Default | A value substituted when a configuration key is absent or `None`, applied at load time. Distinct from Lenient Parsing: a present-but-wrong-typed value still raises rather than silently falling back to the default. | `get_typed(d, "field_name", int, "an integer", default=DEFAULT_VALUE)` (`rules/coding.md` Type-coercion policy) returns `default` only when the key is missing or `None`. |
| Lenient Parsing | Tolerating an unexpected or partially-invalid input by skipping or degrading gracefully rather than raising, when that input is not itself the primary contract being validated. | `scripts/shared/production_config_validator.py`'s best-effort tool-registry lookup is skipped (not failed) on an unexpected exception during production config validation (`# noqa: BLE001` — justified inline as best-effort). |
| Migration | A structural or schema change applied incrementally to an existing system's persisted state, without discarding existing data. | `workflow.sqlite`'s `db/schema_sql.py::apply_workflow_migrations()` applies a sequential list of (ID, SQL) pairs as incremental column additions to existing databases; a no-op for new databases (`docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`). |
| Obsolete | A named entity (function, class, config key) that still exists in source and remains callable, but is no longer the current production path for its original purpose — superseded by a different mechanism. | `read_json_file()` (`scripts/rag/ingestion/pipeline_utils.py`) is retained in code but no longer documented as the current production reader (`plans/done/20260903-085152_plan.md`). |
| Dead Code | A named entity that exists in source with zero current callers anywhere in the codebase — distinct from Obsolete, which may still be reachable via a legacy path. | `shared/tool_executor_helpers.py::is_side_effect()` is defined but has zero call sites in current source (confirmed by repository-wide search); `docs/04_mcp_03_01_dispatch-and-routing.md` accurately describes it as "deprecated (no longer used after TTL cache removal)". |

## Link Rules
```

## Compatibility considerations
No other document links to `### Usage Rules` or `## Link Rules` by anchor in a way
this insertion would disturb (the new subsection is inserted between them, not
replacing either). Independent of seq 02/03 — this row can be applied in any order
relative to them, since none of the 7 term definitions references content those
rows add.

## Security considerations
None — documentation-only addition of term definitions; no code, credentials, or
access-control content is affected.

## Rollback considerations
Single-file, single-insertion change to a Markdown document under version control;
revert via `git revert`. No other file references this new subsection yet, so
rollback carries no cross-file follow-up.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_02_documentation-metadata.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_02_documentation-metadata.md | Manual cross-check | Re-read the 7 new terms | Each term is pairwise distinguishable from the others (per AC-1/AC-4), each example is a real, verifiable repository fact |

## Completion criteria
- `docs/00_governance_02_documentation-metadata.md`'s Terminology Glossary defines
  Backward Compatibility, Operational Fallback, Default, Lenient Parsing,
  Migration, Obsolete, and Dead Code, each with one project-relevant example
  (AC-1, AC-4).
- `uv run python tools/check_docs_quality.py` reports no new errors.

## Out of scope
`docs/00_governance_04_documentation-checks.md` (seq 02, including the `Deprecated`
evidence-label clarification per REQ-001's correction),
`docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03) — each has its
own implementation-procedure document per this Plan's Implementation Target Files
table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified insertion point before editing — no drift. Inserted the 7-term table exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_docs_structure.py`: All checks passed (11543 bytes, well under limit). Diff confirmed scoped to exactly the 12 inserted lines. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | N/A: no `docs/00_index.md` task-scope mapping applies |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20260902-143332_compatterms_standardize_compat_terminology_and_regression_checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-152026
- **Related target files**: docs/00_governance_02_documentation-metadata.md
