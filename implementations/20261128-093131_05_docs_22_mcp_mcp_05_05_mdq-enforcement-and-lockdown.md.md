## Goal

State the enforcement mechanism as import-linter plus an AST call check, and replace the filename-allowlist procedure with the exception-record policy that the test enforces (`REQ-003`, `REQ-004`, `AC-3`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

- The Boundary Enforcement paragraph (line 16) states the two mechanisms and what each proves.
- "Handling False Positives" (line 38) states the exception-record policy: rule, module, reason, owner, expiry; an expired record or a record naming a module that no longer exists fails the check.
- The Allowed Access Paths and Prohibited Access Paths tables keep their content; the database-owning set they already express is what the AST rule uses.

## Assumptions

- Verified at current HEAD: lines 16 and 38 describe substring scanning and adding a filename to the `ALLOWED` set with a PR review comment — the issue's claim held.
- The exception fields are the project's Exception Record Fields convention (`docs/00_governance/governance_03_issue-and-uncertainty-management.md:741`), so the document states the policy and points to that section as the canonical source rather than restating the field definitions as a new convention.
- Enforcement point: the boundary test asserts expiry, which is the CI check (`UNK-01`, plan default); no `tools/` checker is added, so `tools/TOOL_DESCRIPTIONS.md` does not change. If the governance owner chooses a separate checker, this document must name it, and that is the alternative recorded as an Unknown.
- Content policy (`skills/DESIGN.md`): the document already names the test file; the added sentences state a rule, not an implementation-location mapping, so no file tree or symbol index is introduced.
- Front Matter, `Keywords`, and the `related:` list are unchanged; the file already passes `tools/check_docs_structure.py` as it stands.

## Design decisions

- State what each mechanism proves, and keep the claim about dynamic access out: the document must not claim more than the AST check delivers (`AC-4`).
- Keep the design-review requirement for an exception, since that part of the current procedure is still valid; what changes is that the exception is a checkable record rather than a filename.

## Alternatives considered

- `N/A: the plan names this document as the target for the enforcement mechanism and the exception policy.`

## Implementation
### Target file
`docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`

### Procedure
1. Rewrite the Boundary Enforcement paragraph: import direction is enforced by the three import-linter contracts, connection creation by an AST check of call sites outside the database-owning modules.
2. Rewrite "Handling False Positives" as the exception-record policy, naming the five fields and the two failure conditions (expired, module no longer exists), and keeping the design-review requirement.
3. Add that the two `shared` modules that create connections are recorded as exceptions for their stated reasons, so the reader can see why they are not violations.

### Method

- Two paragraph rewrites inside existing sections; no heading is added or removed.

### Details

- The failure message names the rule, the module, the owner, and the expiry, which is what the test asserts.
- The limits of static detection are stated in `docs/22_mcp/mcp_05_04_mdq-rag-boundary.md` (row 4), so this document does not repeat them.

## Compatibility considerations

- `tools/check_docs_consistency.py --domain mcp` compares the claims with `scripts/`; the mechanism stated here must match the test and `.importlinter` after rows 1 and 3 land, so the document is updated in the same change.
- `tools/_validation_gate_toolchain.py:117` and `rules/toolchain.md:169` name the test file by name, which the procedure keeps.

## Security considerations

- `N/A: documentation only.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/generate_reference_table.py --check`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The document states the enforcement mechanism and the exception-record policy, and each claim matches what the contract or the test enforces (`AC-3`, `AC-4`).

## Out of Scope

- The enforced directions and the limits of static detection (`docs/22_mcp/mcp_05_04_mdq-rag-boundary.md`, row 4).
- The exception records themselves (`tests/mcp_servers/mdq/test_mdq_rag_boundary.py`, row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 5 |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` | Pending | — | — | The "Add or update tests" step does not apply to a docs-only row |

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
- **Requirement ID**: REQ-003, REQ-004, AC-3, AC-4
- **Source issue**: `issues/20261119-142131_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-192529_mdqmcp009_mdq-rag-boundary-rules.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-093131
- **Related target files**: `docs/22_mcp/mcp_05_05_mdq-enforcement-and-lockdown.md`
