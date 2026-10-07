## Goal

Update the descriptions of the three changed tools in `tools/TOOL_DESCRIPTIONS.md` so
they reflect the post-migration ADR structure (`REQ-005` / `REQ-001`: the ADR `## Related
Documents` body block no longer exists, `## Implementation References` is now a top-level
section, and `check_known_deviation_sync.py` no longer parses the old subsection; AC-5).

## Scope

- **In-Scope**: `tools/TOOL_DESCRIPTIONS.md` — three Japanese description cells in the two
  tables (the ADR-related module list and the document-structure-tools list). And its
  validation tool `tools/check_tool_descriptions_sync.py` (its own row references it).
- **Out-of-Scope**: the three tool source files; other tool descriptions; `routing.md`
  (separate row).

## Assumptions

- The three changed tools are `check_docs_structure.py`, `check_adr_structure.py`,
  `check_known_deviation_sync.py` (the three whose behaviour this plan changes).
- `TOOL_DESCRIPTIONS.md` is Japanese body text; only the affected cells change. English
  section headings and the rest of the file stay untouched.

## Design decisions

- Edit only the cells that describe the three changed tools' behaviour. Leave every other
  row (including the shared `_front_matter_schema.py` cell that merely names
  `check_docs_structure.py` as a consumer) verbatim.
- Keep the descriptions factual and present-tense; match the new tool behaviour exactly.

## Alternatives considered

- Rewriting the whole file's style or normalising Japanese phrasing everywhere — rejected:
  out of scope; only the three drifted cells need correcting (AGENTS.md Global Rule 5).

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

1. **`check_known_deviation_sync.py` cell** (domain-consistency table, the
   `check_known_deviation_sync.py` row). Remove the parenthetical describing the parsed
   subsection: delete `(および`## Related Documents`→`### Known Issues`)` from the sentence
   that introduces the Known Issue IDs. The cell should now say the tool checks each ADR's
   `## Known Deviations` only.
2. **`check_adr_structure.py` cell** (domain-consistency table, the `check_adr_structure.py`
   row). Change the drift-check description from `` `## Implementation Notes` と `###
   Implementation References` 間 `` to `` `## Implementation Notes` と `## Implementation
   References` 間 `` — the References section is now top-level.
3. **`check_docs_structure.py` cell** (document-structure-tools table, the
   `check_docs_structure.py` row). Remove the clause `` ## Related Documents はADR文書のみ
   必須。非ADR文書に本文のRelated系セクションが残っていると報告し、`` — the ADR
   `## Related Documents` requirement is dropped. Optionally note that `related:` coverage
   now scans documents referenced by the ADR body rather than a removed body section.

### Method

- Read `TOOL_DESCRIPTIONS.md` lines 60-67 (ADR-related module list), 88-91
  (document-structure-tools list).
- Apply the three cell edits above with exact-string replacements.
- Run `uv run python tools/check_tool_descriptions_sync.py` and confirm it passes.

### Details

- `check_known_deviation_sync.py` cell currently reads: `` 各ADRの`## Known Deviations`(および`## Related Documents`→`### Known Issues`)が参照するKnown Issue ID `` — drop the parenthetical.
- `check_adr_structure.py` cell currently reads: ``(b)`## Implementation Notes`と`### Implementation References`間のscripts/tests配下パス引用のドリフト`` — change `### Implementation References` to `## Implementation References`.
- `check_docs_structure.py` cell currently reads: ``...Keywords セクション(`## Related Documents` はADR文書のみ必須。非ADR文書に本文のRelated系セクションが残っていると報告し、ADR文書はFront Matterの`related:`が本文の参照先を網羅しているかを検査する)...`` — remove the `## Related Documents` はADR文書のみ必須... clause.

## Compatibility considerations

- `check_tool_descriptions_sync.py` compares this file against `tools/*.py`. After editing,
  re-run it so the description-to-source mapping stays consistent. No source file changes
  here — only the description text.

## Security considerations

N/A: documentation-only description text.

## Rollback considerations

Revert `tools/TOOL_DESCRIPTIONS.md` to the pre-this-change commit.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `TOOL_DESCRIPTIONS.md` | Consistency | `uv run python tools/check_tool_descriptions_sync.py` | Passes; no drifted/missing description for the three tools |
| `TOOL_DESCRIPTIONS.md` | Manual | Read the three edited cells | No mention of the removed `## Related Documents` block; `## Implementation References` shown as top-level; `check_known_deviation_sync.py` no longer lists the subsection |

## Completion criteria

- The `check_known_deviation_sync.py` cell no longer describes parsing the `### Known
  Issues` subsection.
- The `check_adr_structure.py` cell describes the drift warning on the top-level
  `## Implementation References`.
- The `check_docs_structure.py` cell no longer states that `## Related Documents` is
  required for ADRs.
- `check_tool_descriptions_sync.py` passes.

## Out of scope

- The three tool source files; `routing.md` (separate row); other tool descriptions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261007-133507 | 20261007-133507 | Description changes landed via commit 4316bc537; verified this session |
| 2 | Add or update tests per Validation plan | N/A | — | — | description-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261007-133507 | 20261007-133507 | check_tool_descriptions_sync.py: no issues found |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | |

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
- **Requirement ID**: `REQ-005` — tool descriptions reflect the new top-level `## Implementation References` and the dropped subsection (AC-5)
- **Source issue**: `issues/20261005-144150_rel002_remove-the-adr-body-related-documents-block-and-update-adr-rules-and-tools.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-084759_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-130122
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`
