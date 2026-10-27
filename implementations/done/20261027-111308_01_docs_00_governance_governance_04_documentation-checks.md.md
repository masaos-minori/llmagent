## Goal

Classify the unimplemented context-aware case of the removed-name check (`GV-017`) once, as an Accepted Limit, so the check description, the `GV-017` matrix row, `Follow-up Work Needed` and `Accepted Limits` agree (`REQ-001` to `REQ-004`: reword, add the limit, align the row, keep the register consistent).

## Scope

- Edit four known locations of the target file only: the second detection case under "Removed-name reintroduction detection", the `GV-017` row, `### Follow-up Work Needed` (confirm only), and `## Accepted Limits`.
- Do not change the `GV-014` row, any other matrix row, or `tools/check_compat_shims.py`.

## Assumptions

- Accepted Limit is the classification; the repository owner's decision (UNK-01) is recorded on the Plan before the edit. If the owner decides on a tracked follow-up, stop and report `Plan Gap`.
- The re-evaluation condition uses "reviewed quarterly" plus an event condition (a stale name presented as current found by manual review), per UNK-02's default.
- Step 3a evidence: the second case reads "Not yet implemented (follow-up)"; `Follow-up Work Needed` says none is tracked; the two existing Accepted Limits use the Owner text `Repository owner (reviewed quarterly)`; the `GV-017` row has Status `Existing`; `tools/check_compat_shims.py` states in a comment that the context-aware check is not attempted.
- Plan overlap check: no other Frozen Plan targets this file.
- Size gate (measured in Step 3a, `tools/check_docs_structure.py`, UTF-8 bytes): the file is 24573 B against the default limit of 24576 B with no per-file exception (headroom 3 B). The Plan did not account for this. The new Accepted Limit alone is likely several hundred bytes, so the edit cannot fit unless existing text in this file shrinks by the same amount.

## Design decisions

- The `GV-017` Status cell stays `Existing` (the matrix defines no other Status value); only the Follow-up cell is extended to point to `Accepted Limits`.
- The new Accepted Limit reuses the existing form: current behavior, Owner, Rationale, plus a re-evaluation condition.

## Alternatives considered

N/A: the Plan (Design section) already chose Accepted Limit over a tracked follow-up, because the case needs a current-specification section analysis that a name search cannot provide and manual review already covers it.

## Implementation
### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

1. Replace the sentence "Not yet implemented (follow-up)." under the second detection case with a statement that this case is a documented limit of the automated check, detected only by manual review (see `Accepted Limits`).
2. Append a bullet to `## Accepted Limits`: bold title naming the context-aware removed-name case, current behavior stated factually (a name that remains defined in source but is no longer the production path is not detected by `--check-removed-names`; manual review covers it), `Owner: Repository owner (reviewed quarterly).`, `Rationale:` (needs analysis of whether a current-specification section presents the name as production, which a name search cannot provide; no issue ever tracked it), and `Re-evaluate when:` a stale name presented as current is found by manual review.
3. In the `GV-017` row, keep the existing Follow-up text and extend it to state that the second detection case is an Accepted Limit (see `Accepted Limits`). Leave every other cell unchanged.
4. Confirm `### Follow-up Work Needed` still reads correctly with the new classification; edit it only if it contradicts the Accepted Limit.

### Method

Exact-string edits. Keep the file's line wrapping style in the first two locations.

### Details

- Size gate (`Needs confirmation`, evidence in Assumptions): Before editing, estimate the net growth. Net growth MUST be at most 3 B after the edit (`wc -c` and `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md`). Preferred order:
  1. Condense the three locations this row already touches (the second detection case, the new bullet, the `GV-017` cell) to the shortest accurate wording.
  2. If that is not enough, stop and report `Plan Gap: size gate`. Do not condense other rows or raise the ceiling in `tools/check_docs_structure.py` without a Plan amendment: that file is not a target file of the Plan, so adding it is an additional-target-file discovery, which needs the owner's decision (condense unrelated prose, or add a per-file ceiling).

- Wording of the reworded sentence MUST NOT contain "follow-up" as a status of this case.
- Follow `skills/DESIGN.md` Docs content policy: no implementation-location mapping (do not write "implemented in `check_compat_shims.py`" as a claim); naming the tool and flag as the check's identity is acceptable.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: no secret or credential is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`.
- `uv run python tools/check_docs_structure.py docs/00_governance/governance_04_documentation-checks.md`.
- `uv run python tools/check_docs_content_policy.py --strict`.
- `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The second detection case is described once as a documented limit detected only by manual review, and no sentence calls it follow-up.
- `Accepted Limits` contains the case with Owner, Rationale and a re-evaluation condition.
- The `GV-017` Follow-up cell states the same classification and its Status cell is `Existing`.
- `Follow-up Work Needed` is consistent, and the four checkers report no finding.

## Out of Scope

- Implementing the second detection case in `tools/check_compat_shims.py`.
- Changing the `GV-014` rule text, other matrix rows, or any ADR.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword the second case, add the Accepted Limit, update the `GV-017` row, confirm `Follow-up Work Needed` | Completed | 20261027-123717 | 20261027-123802 | Owner decision (UNK-01) recorded first Blocked: Plan Gap: size gate. Measured dry-run (no file written): the file is 24573 B vs limit 24576 B (headroom 3 B); the three permitted locations condensed to the shortest accurate wording still add +220 B (second case -219, new Accepted Limit +403, GV-017 cell +36); even a minimal bullet leaves at least +48 B. Needs the owner's decision (see Blocker Log). Resumed after the user directed condensing unrelated and duplicated prose in this document to free the size headroom (option b of the Blocker Log). Changed: docs/00_governance/governance_04_documentation-checks.md. Planned edits applied (second case reworded, Accepted Limit added, GV-017 cell extended). Beyond the procedure, at the user's direction: removed six Usage code blocks (duplicate of routing.md and --help), merged three overlapping statements in section 17, and added one clause to section 12 describing the new warning rules of check_adr_invariant_matrix.py. Size 24573 B -> 23305 B (limit 24576 B). Headings and matrix rows other than GV-017 unchanged. |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261027-123802 | 20261027-123802 | Pass: docs_quality, docs_structure, content_policy --strict, japanese, auto_check_inventory (GV-014), known_deviation_sync, issue_inventory_conformance, needs_confirmation_inventory, tool_descriptions_sync; related pytest 38 passed. Step 4: N/A (documentation-only; no source or test file changed). |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Plan Gap: size gate. The target is 24573 B against the 24576 B default limit with no per-file exception. The edit needs about 220 B net even after condensing its three locations. Options for the owner: (a) add a per-file ceiling for this document to `tools/check_docs_structure.py` (additional target file, needs a Plan amendment), (b) condense about 250 B of unrelated prose in this document (needs a Plan amendment), (c) keep the Accepted Limit text shorter than the Plan's required elements allow (not possible within the form of the existing limits). Resolved by option (b), directed by the user: duplicated prose in this document was condensed (six `**Usage:**` code blocks that duplicate the `routing.md` Tools table and each tool's `--help`, and three overlapping statements in section 17), which freed about 1.2 KB. | Yes | 20261027-123802 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (reword second case), `REQ-002` (Accepted Limit), `REQ-003` (`GV-017` row), `REQ-004` (register consistent, checkers clean)
- **Source issue**: issues/20261027-101728_govrev001_governance-followup-state-conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103907_govrev001_governance-followup-state-conflict.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111308
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md