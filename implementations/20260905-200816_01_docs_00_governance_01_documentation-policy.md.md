## Goal
Add a "Claim Type Taxonomy" section (13 claim types, six-column resolution matrix, Authority-vs-Evidence note, Multi-Type-Documents note) to `docs/00_governance_01_documentation-policy.md`, and a one-sentence cross-reference note on the existing "Canonical Source Precedence" table, per `REQ-001`-`REQ-007`.

## Scope
- In scope: inserting the new "## Claim Type Taxonomy" section between the existing "## Canonical Source Precedence" heading and its "### Decision Target Canonical Source Matrix" subsection; adding one cross-reference sentence to "## Canonical Source Precedence"'s introduction.
- Out of scope: everything under Plan `plans/20260905-164413_plan.md`'s "Out-of-Scope" (see Out of scope below) — this document modifies exactly the one target file the Plan's `Implementation Target Files` table names.

## Assumptions
- The existing "## Canonical Source Precedence" table and "### Decision Target Canonical Source Matrix" subsection are not deleted or rewritten by this document — the new section is purely additive, consistent with Plan Assumption 1.
- No claim type beyond the 13 required is introduced (Plan's Scope Constraint).

## Design decisions
- The new section is inserted as a peer `##` heading (not nested under "Canonical Source Precedence"), since it introduces a distinct, forward-looking model rather than elaborating the legacy ranking (Plan Design).
- Each of the 13 claim types is defined as its own `####` subsection; boundary rules are stated only for the 4 types the Plan's `REQ-002` names (`architecture-decision`, `functional-requirement`, `runtime-behavior`, `verification-contract`), not for all 78 possible pairs — this keeps the section proportionate to what `REQ-002` actually requires.
- The six-column resolution matrix is a single Markdown table (one row per claim type) rather than 13 separate tables, so a reader can compare canonical-source-kind assignments across claim types at a glance.

## Alternatives considered
- Rewriting "Canonical Source Precedence"'s ranking table in place instead of adding a new section: rejected — that removal is `M-01-02`'s scope (Plan Out-of-Scope), and doing it here would exceed this Plan's `Implementation Target Files` freeze.
- Nesting the new section under "Canonical Source Precedence" as a subsection: rejected — the taxonomy is a distinct, forward-looking model, not an elaboration of the legacy ranking (Plan Design).

## Implementation
### Target file
`docs/00_governance_01_documentation-policy.md`

### Procedure
1. Insert the new "## Claim Type Taxonomy" section immediately after line 65 (the blank line following the existing Rank table, before line 67's "### Decision Target Canonical Source Matrix").
2. Insert one cross-reference sentence into "## Canonical Source Precedence"'s introduction (after line 56's "the following precedence applies:" sentence, before the Rank table at line 58).

### Method
Use `Edit` with exact-match anchors on the current heading text confirmed via Read (`## Canonical Source Precedence` at line 54, `### Decision Target Canonical Source Matrix` at line 67) — insert new content between them without altering either existing heading or table.

### Details
The new "## Claim Type Taxonomy" section contains, in order (per Plan Design/`REQ-001`-`REQ-005`):
1. **Introductory paragraph**: states the taxonomy resolves canonical authority at claim level (not whole-document level), and that it supersedes "Canonical Source Precedence"'s ranking only once `M-01-02` completes the replacement (`REQ-006`'s forward cross-reference).
2. **13 claim-type definitions** (`####` subsections), each naming: the claim type; its normative definition; its boundary against the nearest overlapping type(s) — boundary text only for `architecture-decision`, `functional-requirement`, `runtime-behavior`, `verification-contract` (`REQ-002`). The 13 types, verbatim from the Plan's `REQ-001`: `architecture-decision`, `functional-requirement`, `external-behavior`, `api-contract`, `runtime-behavior`, `verification-contract`, `production-effective-value`, `configuration-schema`, `database-schema`, `operational-procedure`, `security-policy`, `documentation-metadata`, `unconfirmed-claim`.
3. **Resolution matrix** (six columns: Claim type, Definition, Canonical source kind, Auxiliary evidence, Conflict destination, Notes or constraints), one row per claim type, encoding the 10 rules from the Plan's `REQ-003`:
   - Accepted ADRs canonical for adopted architecture (`architecture-decision` row; note states this does not grant code authority over adopted design — AC4).
   - Canonical Specifications authoritative for normative functional requirements (`functional-requirement` row).
   - Official API schemas/contracts authoritative for external interfaces (`api-contract` row).
   - Source code canonical only for current runtime behavior (`runtime-behavior` row; note explicitly states code authority does not extend to adopted design — AC4).
   - Tests authoritative as executable verification only, not as an automatic replacement for normative requirements (`verification-contract` row; note explicitly states tests cannot silently redefine requirements — AC5).
   - Deployed configuration canonical for effective production values (`production-effective-value` row).
   - Configuration schemas canonical for valid configuration structure and value constraints (`configuration-schema` row).
   - Official DDL/schema generators canonical for DB schema (`database-schema` row).
   - Operations documents/runbooks canonical for operator procedures (`operational-procedure` row).
   - Needs Confirmation inventory canonical for active unconfirmed claims (`unconfirmed-claim` row).
   - `external-behavior`, `security-policy`, `documentation-metadata` rows: canonical source kind and conflict destination filled per the same six-column pattern, consistent with AC2/AC7 ("each claim type has exactly one default canonical source kind" / "a conflict destination is defined for every one of the 13 claim types") even though the source Issue's 10 enumerated rules do not name these three explicitly.
4. **"Authority vs. Evidence" note** (`REQ-004`): states the Canonical source kind column is authority, the Auxiliary evidence column is evidence, and the two are never interchangeable.
5. **"Multi-Type Documents" note** (`REQ-005`): states a single document may carry claims of more than one type, and classification is by claim, not by the document as a whole.

The cross-reference sentence added to "## Canonical Source Precedence"'s introduction (`REQ-006`) states this table is pending replacement by the Claim Type Taxonomy above per `M-01-02`, and that new authority questions should consult the taxonomy first.

After drafting, re-read the whole new section once end-to-end to confirm claim-type terminology is used consistently between the 13 definitions and the resolution matrix (`REQ-007`) — no mixed vocabulary (e.g. a definition calling something `architecture-decision` while the matrix row is labeled differently).

## Compatibility considerations
The existing "Canonical Source Precedence" ranking table and "Decision Target Canonical Source Matrix" subsection are left fully intact — only one new sentence is added to the former's introduction. No existing cross-reference to either heading (by name or anchor) breaks, since neither heading is renamed, moved, or removed.

## Security considerations
N/A: documentation-only change to a governance policy document; no secrets, credentials, or executable content are introduced (per `skills/DESIGN.md` No secrets in output).

## Rollback considerations
A single `git revert` of the commit containing this change fully restores the prior state — the change is additive to one file with no other file depending on the new section's content yet (per Plan Assumptions, `M-01-02`/`M-01-03`/`M-01-06` are still pending and do not yet reference it).

## Validation plan
- Run `uv run python tools/check_docs_quality.py docs/00_governance_01_documentation-policy.md` — must exit 0 with no quality findings.
- Run `uv run python tools/check_docs_structure.py docs/00_governance_01_documentation-policy.md` — must exit 0 with no structural findings.
- Manual review: confirm every one of the 13 claim types has exactly one canonical source kind and one conflict destination in the resolution matrix (AC2, AC7).

## Completion criteria
- The "## Claim Type Taxonomy" section exists with all 13 claim-type definitions, the boundary rules for the 4 named overlapping types, the six-column resolution matrix, the Authority-vs-Evidence note, and the Multi-Type-Documents note (AC1, AC2, AC3, AC6, AC7).
- The `runtime-behavior` and `verification-contract` matrix rows carry the specific notes required by AC4/AC5.
- "Canonical Source Precedence"'s introduction carries the one-sentence cross-reference note (AC8).
- `check_docs_quality.py` and `check_docs_structure.py` both exit 0 against the edited file (AC9).

## Out of scope
- Removing or rewriting the existing "Canonical Source Precedence" ranking table (`M-01-02`).
- Removing `docs/00_governance_04_documentation-checks.md` Manual Check 9's recency rule (`M-01-03`).
- Implementing the Canonical Source Registry (`M-01-04`).
- Rewriting any area document-guide's own Canonical Source Rule(s) section (`M-01-06`).
- Modifying runtime application behavior.
- Creating or modifying Specification/Reference/Operations template files (Plan Unknowns UNK-01 — no such files were found to exist).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only change, no automated test targets this section's prose (Plan's own Tests note) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Scoped to `check_docs_quality.py`/`check_docs_structure.py` per Validation plan, not the full code validation sequence (documentation-only change) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this document's Target file IS the documentation being updated (Step 1 covers it) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260903-103024_m0101_define-canonical-claim-type-taxonomy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-164413_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-200816
- **Related target files**: docs/00_governance_01_documentation-policy.md
