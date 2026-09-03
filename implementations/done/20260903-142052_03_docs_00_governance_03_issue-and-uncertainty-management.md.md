## Goal
Register four new Needs Confirmation Inventory entries (`NC-022` through `NC-025`)
in `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2, for the four
genuinely-unresolved questions this Plan's dependency-graph redesign surfaces but
does not itself resolve (the three EventBus-related runtime edges' implementation
status, the `scripts/rag/`/`scripts/mcp_servers/rag_pipeline/` relationship, whether
Security is a runtime component, and whether a Configuration Ownership Map / API
Consumer Map is needed).

## Scope
- **In-Scope**: `docs/00_governance_03_issue-and-uncertainty-management.md` Part 2
  ("## Part 2: Needs Confirmation Inventory") `### Active Items` only — adding four
  new `#### NC-XXX` entries and updating the closing "No other active items…"
  sentence.
- **Out-of-Scope**: Part 1 (Known Issues) — this row registers Needs Confirmation
  entries only, not Known Issues, since none of the four questions is a
  document-vs-document or code-vs-document conflict (the Plan's own classification:
  each resolves to "mark Needs Confirmation," not "register Known Issue").
  `docs/00_governance_01_documentation-policy.md` (seq 01), `docs/00_governance_04_documentation-checks.md`
  (seq 02), the new tool and test (seq 04/05), the CI workflow step (seq 06).

## Assumptions
- `NC-022` through `NC-025` remain unused repository-wide as of 2026-09-03
  (re-verified below in Implementation > Procedure step 1, per the Plan's own
  correction requiring a fresh re-check at actual implementation time — this
  document was already restructured once by unrelated work since the Plan was
  frozen).
- The four entries are inserted between `#### NC-021` (ends line 723) and
  `#### NC-026` (starts line 724), restoring ascending numeric order
  (021, 022, 023, 024, 025, 026, 027, 028, 029), rather than appended after `#### NC-029`
  (which would leave the list out of numeric order for no benefit).
- Each entry's `Line Number` field cites the current (pre-seq-01) file's Software
  Runtime Dependency Graph / Change Impact Rule location as an approximate reference
  only, consistent with this document's own existing "~NN" approximate-line-number
  convention (see e.g. `NC-021`'s "~39", `NC-026`'s "~37") — exact line numbers must
  be confirmed against `docs/00_governance_01_documentation-policy.md`'s
  post-seq-01/02 content before or at this row's actual implementation, since seq
  01/02 shift line numbers within that file.

## Design decisions
- **ID assignment order matches REQ-010's own listed order**: `NC-022` = the three
  EventBus edges (Plan's `UNK-01`), `NC-023` = `rag`/`rag_pipeline` relationship
  (`UNK-02`), `NC-024` = Security runtime-component status (`UNK-03`), `NC-025` =
  Configuration/API map necessity (`UNK-04`) — this is also the exact ID assignment
  already used by seq 01's Software Runtime Dependency Graph text (`NC-022` for the
  EventBus edges, `NC-023` for the RAG relationship note), so this row's entries
  must keep the same mapping or seq 01's citations become wrong.
- **Priority values**: `NC-022` and `NC-023` are set `Medium` (both concern the
  Runtime Graph's actual edge/node scope, which downstream tooling — the new cycle
  detector, seq 04 — depends on being accurate); `NC-024` and `NC-025` are set `Low`
  (scope/tooling questions with no immediate correctness impact on the graph as
  currently defined), mirroring this table's existing convention where structural
  scope questions rank above nice-to-have rationale/documentation questions (e.g.
  `NC-021`: Medium vs `NC-027`-`NC-029`: Low).
- **`Blocking`: No for all four**: the Plan's own Unknowns table already marks
  `UNK-01` through `UNK-04` as `Blocking? False` — "None of the above block writing
  this Plan's implementation steps" — carried through unchanged into each entry's
  `Blocking` field.

## Alternatives considered
- **Append the four new entries after `NC-029`** — rejected in favor of inserting
  between `NC-021` and `NC-026` (see Assumptions): restores ascending numeric order
  with no downside, and this document has no rule requiring entries to appear in
  registration-date order rather than ID order.
- **Register these four items as Known Issues instead of Needs Confirmation
  entries** — rejected: none of the four is a document-to-document or
  code-vs-document conflict per the Known Issues Registration Rule in
  `docs/00_governance_01_documentation-policy.md`; each is an open question with no
  current documented answer to conflict with, which is exactly what the Needs
  Confirmation Inventory (not Known Issues) exists to track.

## Implementation
### Target file
`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Immediately before editing, re-read `## Part 2: Needs Confirmation Inventory` >
   `### Active Items` in full and re-run `grep -rn "NC-022\|NC-023\|NC-024\|NC-025"
   docs/ plans/ issues/ implementations/` to re-confirm all four IDs remain unused
   (re-verified 2026-09-03 at this Plan's correction time and again while writing
   this implementation-procedure document; re-check once more at actual
   implementation time per the Plan's own correction note, since unrelated work has
   restructured this document once already since the Plan was frozen).
2. Insert the four new entries (Details below) immediately after `#### NC-021`'s
   last field (`- **Blocking**: No`, currently line 722) and its trailing blank line
   (723), and immediately before `#### NC-026` (currently line 724).
3. Update the closing sentence "No other active items beyond NC-021, NC-026,
   NC-027, NC-028, and NC-029 above." (currently line 792) to include the four new
   IDs.

### Method
Direct text edit (e.g. via the `Edit` tool): one edit inserting the four entries as
a single contiguous block between `NC-021` and `NC-026`, and one separate edit
updating the closing sentence.

### Details

**Edit 1 — insert four new entries between `NC-021` and `NC-026`**:

Before (anchor — the blank line between `NC-021`'s last field and `#### NC-026`):
```
- **Blocking**: No

#### NC-026
```

After:
```
- **Blocking**: No

#### NC-022

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph
- **Line Number**: ~300 (approximate; confirm exact line against this document's
  content as edited by this Plan's seq 01 implementation-procedure)
- **Question**: Are `RAG → EventBus`, `MCP → EventBus`, and `Agent → EventBus`
  unimplemented design intent, or a documentation error that should be removed from
  the graph entirely?
- **Evidence**: `grep -rl "eventbus" scripts/agent/ scripts/mcp_servers/ scripts/rag/`
  returns 0 matches — none of Agent, MCP, or RAG source imports or HTTP-publishes to
  EventBus, despite these three edges being asserted in the previous (pre-correction)
  Area Dependency Graph
- **Impact**: If unimplemented, the corrected graph's marking of these edges as
  Needs Confirmation (rather than confirmed fact) is the right interim state; if a
  documentation error, the edges should eventually be removed once confirmed absent
- **Required Action**: Owner review of whether Agent/MCP/RAG are intended to
  eventually publish to EventBus, or whether these edges should be removed once
  confirmed absent
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next EventBus integration review, or next Software Runtime
  Dependency Graph review, whichever comes first
- **Blocking**: No

#### NC-023

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph
- **Line Number**: ~300 (approximate; see NC-022)
- **Question**: Are `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/` the same
  RAG implementation (one wrapping the other) or two independent implementations?
- **Evidence**: Not investigated by `plans/20260902-191512_plan.md` (explicitly
  Out-of-Scope there); the Software Runtime Dependency Graph's RAG node's exact
  relationship to the MCP node's `rag_pipeline` server is undetermined as a result
- **Impact**: Without resolving this, the Runtime Graph's RAG node scope is
  ambiguous, and any future edge involving RAG cannot be confirmed as
  direct-vs-indirect
- **Required Action**: Owner or RAG-area-lead investigation comparing
  `scripts/rag/` and `scripts/mcp_servers/rag_pipeline/`'s actual code and
  responsibilities
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Medium
- **Related NC**: None
- **Resolution Target**: Next RAG architecture review
- **Blocking**: No

#### NC-024

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Software Runtime Dependency Graph / Governance Applicability Matrix
- **Line Number**: ~300 (approximate; see NC-022)
- **Question**: Should the Security governance area be treated as a runtime
  component (added as a node to the Software Runtime Dependency Graph) rather than
  governance-only?
- **Evidence**: No `scripts/security/` or equivalent runtime package was found by a
  quick `find` during this Plan's investigation, but this was not exhaustively
  confirmed
- **Impact**: If Security has a runtime component not yet reflected as a graph
  node, the Runtime Graph's node set (Agent, MCP, RAG, EventBus, Shared/DB) would be
  incomplete
- **Required Action**: Owner confirmation of whether a Security runtime component
  exists anywhere in the repository; if so, add it to the Software Runtime
  Dependency Graph's node set
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance area-scope review
- **Blocking**: No

#### NC-025

- **Source File**: `00_governance_01_documentation-policy.md`
- **Section**: Change Impact Rule
- **Line Number**: ~200 (approximate; confirm exact line against this document's
  content as edited by this Plan's seq 01 implementation-procedure)
- **Question**: Is a Configuration Ownership Map or API Consumer Map needed for the
  Change Impact Rule's configuration/API-change categories, beyond the existing
  Canonical Source Precedence matrix?
- **Evidence**: The Change Impact Rule directs configuration/API changes to the
  existing Canonical Source Precedence matrix (Decision Target Canonical Source
  Matrix) rather than a dedicated map; no such map exists anywhere in the repository
- **Impact**: Without a dedicated map, configuration/API change-impact scoping
  relies on the same general-purpose matrix used for all decision types, which may
  be too coarse for large configuration surfaces
- **Required Action**: Owner review of whether configuration/API change volume
  justifies building a dedicated Configuration Ownership Map or API Consumer Map
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-03
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next governance tooling review
- **Blocking**: No

#### NC-026
```

**Edit 2 — update the closing sentence**:

Before:
```
No other active items beyond NC-021, NC-026, NC-027, NC-028, and NC-029 above.
```

After:
```
No other active items beyond NC-021 through NC-029 above.
```

## Compatibility considerations
No other document references `NC-022` through `NC-025` yet (re-confirmed at
Procedure step 1) other than seq 01's Software Runtime Dependency Graph text (which
cites `NC-022` and `NC-023` by ID, not by line number, so it is not affected by this
row's exact line-number approximations). Apply this row after seq 01 so the
`Line Number` fields can be finalized against seq 01's actual applied content rather
than left as pre-edit approximations.

## Security considerations
None — documentation-only addition to a governance tracking inventory; no code,
credentials, or access-control content is affected.

## Rollback considerations
Single-file, two-edit change to a Markdown document under version control; revert
via `git revert`. Removing these four entries later (once resolved, per this
document's own Status Values rule that resolved items are removed rather than
marked closed) is the document's normal lifecycle, not a rollback.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Automated Needs Confirmation inventory check | `uv run python tools/check_needs_confirmation_inventory.py` | New `NC-022`-`NC-025` entries pass field validation (all 15 fields present, ID not duplicated) |
| docs/00_governance_03_issue-and-uncertainty-management.md | Automated doc structure/quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual review | Re-read the four new entries and the updated closing sentence | Each entry contains all 15 required fields; IDs appear in ascending order with no gaps or duplicates |

## Completion criteria
- `docs/00_governance_03_issue-and-uncertainty-management.md` contains new NC
  entries `NC-022` through `NC-025` for the EventBus edges, the
  `rag`/`rag_pipeline` relationship, Security's runtime-component status, and the
  Configuration/API map question (AC-7).
- `uv run python tools/check_needs_confirmation_inventory.py` and `uv run python
  tools/check_docs_quality.py` report no new errors.

## Out of scope
`docs/00_governance_01_documentation-policy.md` (seq 01),
`docs/00_governance_04_documentation-checks.md` (seq 02), the new tool and test
(seq 04/05), the CI workflow step (seq 06) — each has its own
implementation-procedure document per this Plan's Implementation Target Files table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified NC-022-025 unused immediately before editing (`grep -rn` across `docs/`, `plans/`, `issues/`, `implementations/` found only Plan/procedure reservations, no live registration); also re-verified Line Number fields against seq 01's actual applied content: Software Runtime Dependency Graph at line 306, Change Impact Rule at line 198 (both corrected from the "~300"/"~200" placeholders) |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_needs_confirmation_inventory.py`: 8 warnings, identical set to before this edit (0 new). `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_docs_structure.py` was not part of this row's own Validation plan and was not run as a gate — see Blocker Log for the pre-existing finding it would have surfaced. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260903 | 20260903 | This row's own target file is the documentation update; no `docs/00_index.md` task-scope mapping applies |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | Non-blocking observation (not a blocker for this row): `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` reports the file at 51181 bytes, exceeding even the raised 24576-byte `MAX_SIZE` (see seq 01's Blocker Log). The file was already at 46529 bytes — over the raised limit — before this row's edit; this row's 4-entry addition (~4652 bytes) is not the cause of the violation, and `check_docs_structure.py` was never part of this row's own Validation plan. Out of scope for this row (adding NC entries); the file's overall size would need its own splitting/restructuring effort, tracked here only as an observation, not acted on. | N/A | N/A: pre-existing condition, not caused by or resolved by this row |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-010
- **Source issue**: issues/done/20260902-102831_depgraph_area-dependency-graph-cycle-and-relationship-conflation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-191512_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142052
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
