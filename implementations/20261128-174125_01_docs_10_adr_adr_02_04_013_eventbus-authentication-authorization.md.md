## Goal
- Correct the two mislabeled one-generation rows and add the missing evidence rows in the ADR-013 Automated Tests table so the index registration can cite only evidence the body also carries (`REQ-002` relabel; `REQ-003` route-registry, TTL-precedence, and publication evidence).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `### Automated Tests` table of `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`. No decision text changes and no approval text.

## Assumptions
- Verified at the Plan's evidence revision (`tools/check_evidence_freshness.py check`: 16 unchanged, 0 changed).
- Sequencing (Step 2): the TTL-precedence evidence needs the tests added by the admin TTL-precedence procedures (adrr001), and the publication evidence needs the tests added by the publication-boundary procedures (adrr002). Both Plans are archived, so `plan_dependency_order.py` reports this Plan ready, but their procedures are not yet executed and MUST be implemented first. Cite only test node ids that exist at implementation time; read the actual names from the merged test files.
- Overlap judgment (Step 2): the ADR-013 body is also edited by adrr001 (Decision Detail 12) and adrr002 (the `auth.py` implementation-reference line); the edits are in different sections, a sequencing dependency.
- The table already labels some rows by Decision Detail ("Decision Details #10", "Decision Details #12"), so labeling the one-generation rows "Decision Details #9" follows an existing convention and needs no new invariant.
- `tools/check_adr_invariant_matrix.py` requires body-cited test files to be covered by the index citations and index evidence to appear in the body; the index row of procedure 02 cites exactly the nodes this procedure puts in the body.

## Design decisions
- Keep one row per verified behavior; for the route-registry evidence use a single row labeled `INV-01, INV-03`.
- Cite only nodes that exist and pass; no generic `Confirmed` text.

## Alternatives considered
N/A: follows the table's existing structure.

## Implementation
### Target file
`docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`

### Procedure
1. Change the `Verifies` cell of the "One-generation publish: no empty-map window during principal map rebuild" row from `INV-01` to `Decision Details #9 (one-generation invariant)`, and of the "Failed rebuild preserves previous generation's principals" row to `Decision Details #9 (failed rebuild keeps the previous generation)`.
2. Add a row for the route-registry evidence: `Every operator and consumer route rejects a missing or unknown token with 401 and a wrong role with 403` | `INV-01, INV-03` | Integration | Yes | `tests/eventbus/test_eventbus_route_registry.py::test_operator_route_rejects_missing_unknown_and_wrong_role`, `tests/eventbus/test_eventbus_route_registry.py::test_consumer_route_rejects_missing_token_and_wrong_role`.
3. After the prerequisite procedures are implemented, add a row for Decision Detail 13 citing the test node ids that assert a stale `expected_generation` with an invalid `ttl_seconds` returns 422, and a row for Decision Details #9 and #14 citing the node ids of the forced-interleave admin test, the admin-versus-sweep race tests, and the mixed-generation test. Resolve each node id from the test files (`rg "def test_" tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_authz_generation_ttl.py`) and confirm each with `pytest <nodeid>`.

### Method
- Use the table's column order (`Test | Verifies | Type | Blocking | Implementation`) and the full `tests/...::Class::test` node format.
- If a prerequisite test does not exist yet, omit its row and report it; do not invent names.

### Details
- The two relabeled rows keep their existing `Implementation` nodes (`tests/eventbus/test_eventbus_auth.py::TestAtomicPublishAndFailedRebuild::...`).

## Compatibility considerations
N/A: documentation only.

## Security considerations
N/A: no credential content.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run every newly cited node with `pytest`; `uv run python tools/check_adr_structure.py` and `uv run python tools/check_adr_invariant_matrix.py` (run again after procedure 02).

## Completion criteria
- No row other than the INV-01 evidence is labeled `INV-01`; every cited node exists and passes; the ADR checkers report no findings (`REQ-002`, `REQ-003`).

## Out of Scope
- The index matrix (procedure 02); the manifest (procedure 03); Decision Detail 12 wording (adrr001); the implementation-reference list (adrr002).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Relabel the two one-generation rows and add the route-registry evidence row in `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Pending | — | — | |
| 2 | Add the TTL-precedence and publication evidence rows once their tests exist | Pending | — | — | |
| 3 | Run the ADR checkers and `pytest` on every newly cited node | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (relabel), `REQ-003` (evidence rows)
- **Source issue**: issues/20261125-103309_adrr003_adr013-invariant-coverage.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261128-172904_adrr003_adr013-invariant-coverage.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-174125
- **Related target files**: `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`
