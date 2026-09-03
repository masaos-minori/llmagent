## Goal
Document the removed-name reintroduction detection rule's asymmetric design
(REQ-003/004), add it as a new `GV-020` Governance Verification Matrix row
(REQ-006), add it to the Merge Condition Validation "PR checklist" with a
zero-unexplained-findings completion criterion (REQ-006), and clarify the
existing `Deprecated` evidence label's definition for consistency with the new
compatibility terms added to `docs/00_governance_02_documentation-metadata.md`
(REQ-001 sub-task).

## Scope
- **In-Scope**: `docs/00_governance_04_documentation-checks.md`'s
  `### 4. Backward Compatibility Check` (rule design addition),
  `### 10. Evidence Label Validation` (`Deprecated` clarification), Governance
  Verification Matrix (new `GV-020` row), `### Follow-up Work Needed` (new item),
  `### 13. Merge Condition Validation` (PR-checklist addition).
- **Out-of-Scope**: `docs/00_governance_02_documentation-metadata.md` (seq 01 of
  this Plan), `docs/00_governance_03_issue-and-uncertainty-management.md`
  (seq 03); implementing the `read_json_file`-style context-aware detection case
  itself (a genuine follow-up — see Assumptions); wiring `--check-removed-names`
  into CI as default-on (deferred until `plans/done/20260903-090104_plan.md`'s
  corpus fix lands, per that flag's own docstring).

## Assumptions
- `tools/check_compat_shims.py::check_removed_name_reintroduction()` already
  implements the grep-vs-source-absence half of REQ-003's rule (both named
  examples: `_update_null_fill`; `ToolRouteResolver`+`server_configs`
  section-scoped co-occurrence), gated behind `--check-removed-names` (default
  off) — re-verified 2026-09-03 by direct `Read` of
  `tools/check_compat_shims.py:170-329`. This was added in commit `309a9ab10`,
  after this Plan's own 09:09 generation time, so the Plan's original "Status
  Missing"/"a follow-up issue" framing for REQ-006/Out-of-Scope was corrected
  2026-09-03 (see the Plan's own Requirements section) to `Partial` before this
  row was written.
- `_HISTORICAL_CONTEXT_MARKERS = {"legacy", "historical", "archive only",
  "resolved", "was:", "removed"}` and `_is_historical_context()` (checks the
  current line plus the preceding 10 lines) already implement REQ-004's
  historical-reference allowlist convention — re-verified at the same read.
- The `read_json_file`-style context-aware check (a name retained in source but
  no longer the current production path) is genuinely not implemented anywhere —
  re-verified: `check_removed_name_reintroduction()`'s own module comment states
  this explicitly ("needs a harder, context-aware... check that this function
  does not attempt").
- This repository has no file literally named a "PR checklist" — the closest
  existing analog `docs/00_governance_04_documentation-checks.md`'s own
  `### 13. Merge Condition Validation` (Blocking/Non-blocking conditions, Merge
  Workflow) is the target REQ-006's "PR checklist description" refers to, since
  that is the only document in the repository that actually gates merge
  decisions with a checklist-like structure.
- The file is 17284 bytes as of 2026-09-03, well under the 24576-byte
  `MAX_SIZE` (see `implementations/done/20260903-142052_01_...md`) — this row's
  additions have ample headroom.

## Design decisions
- **`GV-020`'s classification is Warning, not Blocking** (REQ-005's
  Blocking-vs-Warning decision, actually implemented here since REQ-005's own
  target file is `docs/00_governance_03...md`, but the classification value
  itself must appear in this row's `GV-020` table row): a newly-introduced
  heuristic check — especially its still-partial, context-aware half once
  implemented — risks false positives; pairing Warning classification with
  REQ-005's temporary-exception process (reason/owner/expiration) gives a release
  valve without silently accepting real reintroductions. This mirrors
  `check_compat_shims.py`'s own existing convention (new checks stay report-only
  via an opt-in flag until the corpus is compliant), applied here to the GV-matrix
  classification level instead of a CLI flag.
- **`GV-020`'s `Status` is `Partial`**, matching this table's existing value
  vocabulary (used by `GV-013`) rather than inventing a new status value — the
  grep-vs-source-absence half is real and running (opt-in); the context-aware
  half is not.
- **The rule's design description is added to `### 4. Backward Compatibility
  Check` (the existing `check_compat_shims.py` section), not a new numbered
  item**, since the check IS `check_compat_shims.py` (now with an added
  capability), not a separate tool — adding a new numbered item would
  misrepresent it as a distinct check with its own home.
- **The `Deprecated` evidence-label clarification cross-references, rather than
  redefines, the new Glossary terms**: `Deprecated` (this section) classifies how
  well an assertion is *grounded* ("the writer confirms this description is of an
  obsolete feature"), while `Obsolete`/`Dead Code` (the Glossary, seq 01) classify
  the compatibility *lifecycle state* of the thing being described — these are
  different axes (evidence-grounding vs. lifecycle-state) that happen to share
  vocabulary, so clarifying the distinction (not merging the definitions) is what
  "consistency with the new terms" requires.
- **The Merge Condition Validation addition is a non-blocking condition plus one
  new sentence**, not a new numbered blocking-condition bullet, consistent with
  `GV-020`'s own Warning classification decided above — a Blocking-conditions
  bullet would contradict the GV-matrix row's own Gate column.

## Alternatives considered
- **Classify `GV-020` as Blocking** — rejected (see Design decisions): a
  still-partial, heuristic check should not hard-block merges before its
  false-positive rate is understood in practice; REQ-005's own temporary-exception
  process presupposes a Warning-tier release valve exists to except through.
- **Add a new `### 15.` (or similar) numbered section for the removed-name rule
  instead of extending `### 4.`** — rejected: `check_compat_shims.py` already has
  a numbered "home" (`### 4.`); a second section for the same tool would
  duplicate/fragment its description across two places, which this document's
  own existing convention (one numbered item per tool) does not do elsewhere.
- **Redefine `Deprecated` in `### 10. Evidence Label Validation` to mean the same
  thing as the new Glossary `Obsolete`/`Dead Code` terms** — rejected: these
  genuinely describe different axes (see Design decisions); conflating them would
  itself introduce the vocabulary drift this Plan's own Reason for Change warns
  against.

## Implementation
### Target file
`docs/00_governance_04_documentation-checks.md`

### Procedure
1. Re-read `### 4. Backward Compatibility Check` (lines 89-98),
   `### 10. Evidence Label Validation` item 5 (line 154), the Governance
   Verification Matrix's last row (`GV-019`, line 266) and Follow-up Work Needed's
   last item (item 13, line 294), and `### 13. Merge Condition Validation`
   (lines 201-220) immediately before editing to reconfirm no drift (done above;
   confirmed identical to the Plan's citations after re-verification).
2. Add the removed-name reintroduction rule design to
   `### 4. Backward Compatibility Check`.
3. Add the `Deprecated` clarification sentence to
   `### 10. Evidence Label Validation` item 5.
4. Add the `GV-020` row immediately after `GV-019` in the Governance Verification
   Matrix.
5. Add Follow-up Work Needed item 14 for `GV-020`.
6. Add the non-blocking condition and completion-criterion sentence to
   `### 13. Merge Condition Validation`.

### Method
Direct text edit (e.g. via the `Edit` tool) using the exact before/after blocks in
Details, as five independent edits (not textually adjacent).

### Details

**Edit 1 — `### 4. Backward Compatibility Check` rule design**:

Before:
```
### 4. Backward Compatibility Check (`check_compat_shims.py`)

Checks for stale compatibility layers left behind after API migrations.

**Scanned directories:**
- `scripts/`
- `docs/`
- `tests/`
- `tools/`
```

After:
```
### 4. Backward Compatibility Check (`check_compat_shims.py`)

Checks for stale compatibility layers left behind after API migrations.

**Scanned directories:**
- `scripts/`
- `docs/`
- `tests/`
- `tools/`

**Removed-name reintroduction detection** (`check_removed_name_reintroduction()`,
opt-in via `--check-removed-names`, default off): flags a name confirmed absent
from source code being presented as current in `docs/*.md`, outside historical
context. Two cases require different detection strategies:
- **Name confirmed fully absent from source** (e.g. `_update_null_fill`;
  `ToolRouteResolver`+`server_configs` co-occurrence, section-scoped) — a simple
  grep-vs-source-absence check suffices. Implemented.
- **Name that remains in source but is no longer the current production path**
  (e.g. `read_json_file`, still defined in
  `scripts/rag/ingestion/pipeline_utils.py` but no longer the current production
  reader) — requires checking whether a *current-specification* section presents
  it as production, not merely whether the identifier string appears in `docs/`.
  Not yet implemented (follow-up).

**Historical-reference allowlist**: a line within 10 lines of an explicit marker
(`legacy`, `historical`, `archive only`, `resolved`, `was:`, `removed`) is exempt
from this check (`_HISTORICAL_CONTEXT_MARKERS` / `_is_historical_context()`).
```

**Edit 2 — `Deprecated` evidence-label clarification**:

Before:
```
5. **Deprecated** — Describes an obsolete feature no longer in use
```

After:
```
5. **Deprecated** — Describes an obsolete feature no longer in use. Distinct from `docs/00_governance_02_documentation-metadata.md`'s Terminology Glossary terms `Obsolete` (a name still present and callable, but no longer the current production path) and `Dead Code` (a name with zero current callers): this evidence label classifies how well a *statement* is grounded, not the compatibility lifecycle of the thing the statement describes.
```

**Edit 3 — new `GV-020` row**:

Before:
```
| GV-019 | No unnecessary Metadata or Status fields added | Meta | Manual | Human review | Periodic | Warning | Missing | Register Known Issue |
```

After:
```
| GV-019 | No unnecessary Metadata or Status fields added | Meta | Manual | Human review | Periodic | Warning | Missing | Register Known Issue |
| GV-020 | Removed-name reintroduction in current specifications | Chk | Auto | `check_compat_shims.py --check-removed-names` | PR | Warning | Partial | Implement the context-aware (retained-but-superseded) detection case; promote to default-on once the corpus is compliant |
```

**Edit 4 — Follow-up Work Needed item 14**:

Before:
```
13. **GV-019**: Add metadata field usage policy enforcement

## Change Impact Assessment
```

After:
```
13. **GV-019**: Add metadata field usage policy enforcement
14. **GV-020**: Implement the `read_json_file`-style context-aware detection
    case (a name retained in source but no longer the current production path);
    promote `--check-removed-names` from opt-in to default-on once
    `plans/done/20260903-090104_plan.md` (toolroutedoc)'s corpus fix lands, per
    `check_compat_shims.py`'s own "report-only until compliant" convention.

## Change Impact Assessment
```

**Edit 5 — Merge Condition Validation addition**:

Before:
```
**Non-blocking conditions (allow merge with warning):**
- High-severity open issue exists in affected area
- Documentation outdated but code is correct
- Config drift detected but no behavioral impact
```

After:
```
**Non-blocking conditions (allow merge with warning):**
- High-severity open issue exists in affected area
- Documentation outdated but code is correct
- Config drift detected but no behavioral impact
- Removed-name reintroduction detected by `check_compat_shims.py --check-removed-names` (`GV-020`), without an approved temporary exception (`docs/00_governance_03_issue-and-uncertainty-management.md`)

A `GV-020` finding is not itself blocking, but every finding must be resolved or
covered by an approved temporary exception before merge — an unexplained finding
left neither fixed nor excepted is treated as incomplete review, not a passing PR.
```

## Compatibility considerations
No other document links to `### 4.`, `### 10.`, `### 13.`, the Governance
Verification Matrix, or Follow-up Work Needed by anchor in a way these five
insertions would disturb (each is an addition within an existing section, not a
heading rename or move). Independent of seq 01/03 — this row references
`docs/00_governance_02_documentation-metadata.md`'s new Glossary terms by name in
Edit 2's prose, but does not require seq 01 to already be applied for this row's
own edits to be internally valid (the cross-reference remains meaningful once
seq 01 lands, and is not a broken link either way, since it references a section
name, not an anchor).

## Security considerations
None — documentation-only additions describing an existing, already-reviewed
tool's behavior and governance bookkeeping; no code, credentials, or
access-control content is affected.

## Rollback considerations
Single-file, five-edit change to a Markdown document under version control;
revert via `git revert`. No other file references `GV-020` or this row's new
prose yet, so rollback carries no cross-file follow-up.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_04_documentation-checks.md | Automated doc quality check | `uv run python tools/check_docs_quality.py` | No new errors |
| docs/00_governance_04_documentation-checks.md | Manual cross-check | Re-read `GV-020`'s row | Status is `Partial`; the row does not claim more automated enforcement than actually exists (per this Plan's 2026-09-03 correction) |
| docs/00_governance_04_documentation-checks.md | Manual cross-check | Re-read the `### 4.` rule-design addition | The asymmetric design (implemented vs. follow-up case) is stated accurately against `tools/check_compat_shims.py`'s actual current code |

## Completion criteria
- `docs/00_governance_04_documentation-checks.md` documents the removed-name
  reintroduction rule's asymmetric design, distinguishing the implemented
  grep-vs-source-absence case from the not-yet-implemented context-aware case
  (AC-5, REQ-003).
- The historical-reference allowlist convention is documented (AC-6, REQ-004).
- `GV-020` exists in the Governance Verification Matrix with Status `Partial` and
  a Warning classification; the Merge Condition Validation section references it
  with a zero-unexplained-findings completion criterion (AC-8, REQ-006).
- The `### 10.` `Deprecated` evidence label is clarified against the new Glossary
  terms (AC-1, REQ-001 sub-task).
- `uv run python tools/check_docs_quality.py` reports no new errors.

## Out of scope
`docs/00_governance_02_documentation-metadata.md` (seq 01),
`docs/00_governance_03_issue-and-uncertainty-management.md` (seq 03) — each has
its own implementation-procedure document per this Plan's Implementation Target
Files table. Implementing the `read_json_file`-style context-aware check itself,
and promoting `--check-removed-names` to default-on — both genuine follow-ups,
not this row's scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903 | 20260903 | Re-verified all 5 edit anchor points before editing — no drift (identical line numbers). Applied Edits 1-5 exactly as designed. |
| 2 | Add or update tests per Validation plan | Completed | 20260903 | 20260903 | N/A: documentation-only row, no test file owned by this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903 | 20260903 | `check_docs_quality.py`: 0 errors, 1 pre-existing unrelated warning. `check_docs_structure.py`: All checks passed (19918 bytes, well under limit). Diff confirmed scoped to exactly the 5 intended edits (30 insertions, 1 deletion). |
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
- **Requirement ID**: REQ-001 (sub-task), REQ-003, REQ-004, REQ-006
- **Source issue**: issues/done/20260902-143332_compatterms_standardize_compat_terminology_and_regression_checks.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-090945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-152026
- **Related target files**: docs/00_governance_04_documentation-checks.md
