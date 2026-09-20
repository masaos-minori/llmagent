## Goal
Create `docs/05_agent_12_07_memory-module-reference-generated.md` as a new generated
companion document for the Memory domain (`REQ-002`), then run
`tools/generate_reference_table.py --type memory` to populate its guarded block
(`REQ-003`) — both per Plan `plans/20260920-161148_plan.md`, whose
`Implementation Target Files` table assigns both Requirements to this one target-file
row. Mirrors `docs/05_agent_14_reference-api-generated.md`'s shape.

## Scope
In scope: creating this one new file with front matter, an introduction paragraph, a
`## Related Documents` section, a `## Keywords` section, and guard-comment markers
(`REQ-002`); then running the generator (dry-run, then live) to populate the guarded
block with `scripts/agent/memory/*.py`'s public class/function index (`REQ-003`). Out
of scope: modifying any of the six existing `docs/05_agent_12_0[1-6]_*.md` chapter
documents; `tools/generate_reference_table.py` itself (that is `REQ-001`'s own
target-file row, a separate implementation procedure document, and MUST land — or at
minimum have its `"memory"` `DOMAIN_*` wiring merged — before this row's `REQ-003` step
can run).

## Assumptions
`docs/05_agent_12_07_memory-module-reference-generated.md` does not yet exist
(re-confirmed during this document's creation). `docs/05_agent_14_reference-api-generated.md`
(re-read in full during this document's creation) is the correct structural template
to mirror, per the Plan's Implementation intent.

## Design decisions
Mirror `05_agent_14_reference-api-generated.md`'s exact structure: front matter
(`title`/`area`/`tags`/`related`), a `## Purpose` section explaining this is a
generated companion, `## Related Documents` linking back to the six hand-curated
chapter files it complements, `## Keywords`, and a `## Module Class/Function
Reference (auto-generated)` heading containing the guard-comment pair with the
domain-specific welcome sentence between them — but leave the block's table body empty
(no rows) until `REQ-003`'s generator run populates it, since this row does not run the
generator itself.

## Alternatives considered
- Populate the guarded block with a hand-written placeholder table row: rejected —
  ADR-015's Invariants require guarded-block content to be produced only by the
  generator; a hand-written placeholder would itself violate "never hand-edited
  between the guard comments" the moment it is committed, even as a stopgap.
- Name the file `docs/05_agent_memory_reference-generated.md` (a name pattern outside
  the `12_0N` chapter-numbering sequence): rejected — `REQ-001`'s
  `REFERENCE_DOC_MEMORY` constant (this same Plan's Row 1) already fixes the exact
  path as `docs/05_agent_12_07_memory-module-reference-generated.md`; this row must
  use that exact path for the two rows to be consistent.

## Implementation
### Target file
`docs/05_agent_12_07_memory-module-reference-generated.md`

### Procedure
1. Confirm `REQ-001` (Row 1 of this Plan, `tools/generate_reference_table.py`'s
   `"memory"` `DOMAIN_*` wiring) has landed — this row's step 5 below cannot succeed
   otherwise.
2. Confirm the target path does not yet exist (re-check immediately before writing, in
   case a concurrent process created it).
3. Create the file with:
   - Front matter: `title: "Memory Layer Reference — Generated Class/Function Index"`,
     `area: agent`, `tags: [agent, memory, api-reference, generated]`, `related:`
     listing all six existing `docs/05_agent_12_0[1-6]_*.md` chapter files.
   - `# Memory Layer Reference — Generated Class/Function Index` (H1 matching the
     title).
   - `## Purpose`: states this is a generated index of every public top-level
     class/function under `scripts/agent/memory/*.py`
     (`tools/generate_reference_table.py --type memory`), a companion to the six
     hand-curated Memory Layer chapter documents, kept separate so none of them needs
     to embed a mechanically-derived listing; states not to hand-edit between the
     guard comments.
   - `## Related Documents`: links to all six chapter files plus
     `00_governance_01_documentation-policy.md` (ADR-015 Reference Document Class
     Disposition), mirroring `05_agent_14`'s own reference to that ADR.
   - `## Keywords`: `agent, memory, api-reference, generated`.
   - `## Module Class/Function Reference (auto-generated)` heading, followed by the
     guard-start comment `<!-- AUTO-GENERATED: gen_memory_reference.py
     class-function-reference -->`, the welcome sentence ("Generated from
     `scripts/agent/memory/*.py` top-level public classes and functions. Do not
     hand-edit between the guard comments; run `python tools/generate_reference_table.py
     --type memory` to refresh."), no table rows, and the guard-end comment
     `<!-- END AUTO-GENERATED -->`.
4. Run `uv run python tools/generate_reference_table.py --type memory --dry-run` and
   review the printed output for plausibility (one row per public top-level
   class/function under `scripts/agent/memory/*.py`, matching the shape of
   `05_agent_14`'s existing table).
5. Run `uv run python tools/generate_reference_table.py --type memory` (live) and
   confirm the guarded block in this file is populated with content identical to the
   step 4 dry-run output.

### Method
One `Write` creating the new file in full per Procedure step 3 (empty guarded block),
followed by two `Bash` invocations of the generator (Procedure steps 4-5, dry-run then
live) rather than a second `Edit` — the generator itself writes the guarded block's
content; this row does not hand-author the table.

### Details
The guard-comment pair and welcome sentence must byte-for-byte match
`tools/generate_reference_table.py`'s `"memory"` `DOMAIN_GUARDS`/`DOMAIN_WELCOME_LINES`
entries (added by `REQ-001`, this Plan's Row 1) — confirm this row's guard-comment text
matches Row 1's `GUARD_START_MEMORY` value exactly before running step 4, since a
mismatch would cause the generator to fail to locate the guarded block (or, worse,
silently write a second, unmatched block). After step 5, do not hand-edit anything
between the guard comments — per ADR-015's Invariants, that content is owned
exclusively by the generator from this point forward.

## Compatibility considerations
`N/A: this is a new file; no existing document, code, or public interface is affected`.

## Security considerations
`N/A: no security-relevant content is touched`.

## Rollback considerations
Delete the new file (`git rm` or `git checkout` on a tracked-then-reverted state) — no
other file references it until `REQ-001`'s `REFERENCE_DOC_MEMORY` constant lands, so
this row is independently revertable.

## Validation plan
- `uv run python tools/check_docs_structure.py docs/05_agent_12_07_memory-module-reference-generated.md`
  — confirm it passes (front matter complete, required sections present) (Plan `AC-2`).
- `uv run python tools/check_docs_content_policy.py` — confirm the populated guarded
  block is recognized as guard-exempt, not flagged as a field/type table (Plan `AC-2`).
  Per the Plan's own Tests note: if the guard-format exemption mismatch ADR-015's
  Consequences already tracks separately also affects this new `memory` guard string,
  record it as a new, separately-tracked finding — do not fix the underlying checker
  bug under this row.
- `uv run pytest tests/tools/test_generate_reference_table.py -v` — confirm a `memory`
  test case (added by `REQ-001`'s row, or added here if not already present) passes.
- Re-run `uv run python tools/generate_reference_table.py --type memory --dry-run` and
  diff its output against the live-written guarded block — confirm they match exactly
  (Plan `AC-3`).

## Completion criteria
The new file exists with front matter, `## Purpose`, `## Related Documents`, `##
Keywords`, and a guarded block whose guard-comment text and welcome sentence exactly
match `REQ-001`'s `GUARD_START_MEMORY`/`DOMAIN_WELCOME_LINES["memory"]` values and whose
table content matches a live generator run's output; none of the six existing chapter
files is modified.

## Out of scope
- Any of the six existing `docs/05_agent_12_0[1-6]_*.md` chapter documents — not
  modified by this Plan at all (see Plan Scope).
- `tools/generate_reference_table.py` itself — that is `REQ-001`'s own target-file row
  (a separate implementation procedure document); this row only depends on it landing
  first.
- Fixing a guard-format exemption mismatch in `check_docs_content_policy.py`, if one
  is found during validation — record and report separately, per ADR-015's
  Consequences section, which already tracks this class of bug.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the new file with front matter and guard markers (REQ-002) | Completed | 20260920-172230 | 20260920-172230 | New file created with front matter, Purpose, Related Documents, Keywords, and empty guard markers |
| 2 | Run generator dry-run then live to populate the guarded block (REQ-003) | Completed | 20260920-172230 | 20260920-172230 | Depends on REQ-001 (Row 1) having landed first Generator dry-run reviewed then run live; guarded block populated with scripts/agent/memory/*.py public class/function index; 7/7 tests pass; other domains' generated docs (05_agent_14, 06_eventbus_06) untouched |
| 3 | Add or update tests per Validation plan | Completed | 20260920-172230 | 20260920-172230 | Extend `tests/tools/test_generate_reference_table.py` with a `memory` case if REQ-001's row did not already add one check_docs_structure.py/content_policy.py: all pass, zero findings |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-172230 | 20260920-172230 | Scoped to `check_docs_structure.py`/`check_docs_content_policy.py`/pytest per Validation plan N/A: no docs/00_index.md task-scope mapping row for this new generated file |

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
- **Requirement ID**: `REQ-002`, `REQ-003` — create the new generated-companion file, then run the generator to populate its guarded block
- **Source issue**: issues/20260920-154806_memref01_resolve-nc-038-memory-reference-class-migration-target-and-wiring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-161148_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-164038
- **Related target files**: docs/05_agent_12_07_memory-module-reference-generated.md