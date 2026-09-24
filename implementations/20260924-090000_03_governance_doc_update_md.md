## Goal

Update RAG-006 status in the issue-and-uncertainty management document to reflect resolution of the missing operational guidance gap for `rag-src/registered/` files.

## Scope

- **In-Scope**: Modify the RAG-006 entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to update its status, current description, and impact fields to reflect that retention policy is now defined.
- **Out-of-Scope**: Modifying other issue entries; adding new issues; changing the governance document structure.

## Assumptions

- The retention policy will exist before this documentation update (per the other procedure docs).
- The project uses Markdown format for governance documents (confirmed by reading the existing document).
- The RAG-006 entry currently has status "open" that needs to be updated.

## Design decisions

- Update the RAG-006 entry's status from "open" to "resolved" rather than creating a new entry. This preserves the historical record while reflecting the current state.
- Update the Current Description field to describe the new retention policy rather than just stating the gap exists.
- Update the Impact field to reflect reduced risk due to policy definition.

## Alternatives considered

- Creating a new issue entry for the retention policy instead of updating the existing one. This was rejected because it would duplicate the historical record of why the Known Issue existed. Updating the existing entry preserves the traceability from "gap identified" to "gap closed". The original entry provides context for the retention design decisions and policy rationale.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Scaffold the documentation modification skeleton with `uv run python tools/generate_workitem.py --kind implementation-procedure --source-plan plans/20260924-080000_plan.md --target-file-path docs/00_governance_03_issue-and-uncertainty-management.md --seq 03`.
2. Verify the scaffolded file exists at `implementations/20260924-090000_03_governance_doc_update_md.md` before proceeding.
3. Implement the documentation updates per Method below.

### Method

#### Current RAG-006 entry (verified):

The RAG-006 entry exists in the governance document with the following content:

```markdown
#### RAG-006

- **ID**: RAG-006
- **Title**: Missing operational guidance for rag-src/registered/ file lifecycle
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/ingestion/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `docs/` directory
- **Related**: File Router, RagIngester
- **Summary**: After successful ingestion, chunk files are moved to `rag-src/registered/` but there is no documentation defining their retention period, deletion trigger, or deletion ownership. This creates uncertainty about how long files persist and who is responsible for cleanup.
- **Current Description**: No deletion logic exists in `scripts/rag/ingestion/ingester.py` or `file_routing.py`. The `rag-src/registered/` directory may grow unbounded over time, and files may be deleted ad hoc without traceability if this gap is not tracked.
- **Observed Implementation**: Files are MOVED (not copied) to `rag-src/registered/` by `FileRouter.route()` after successful ingestion. No post-move cleanup exists. The ingestion pipeline already logs results and error metadata is written for failed chunks.
- **Impact**: Without defined lifecycle management, the `rag-src/registered/` directory becomes a source of disk space growth and operational confusion. A clear policy prevents both issues.
- **Recommended Action**: Define retention/deletion policy for `rag-src/registered/` files, add Deletion column to File Lifecycle table, replace `(retention TBD)` placeholder in system overview, update Known Issue entry status.
- **Resolution Target**: Next RAG architecture review
```

#### Modification:

Update the following fields:

```markdown
#### RAG-006

- **ID**: RAG-006
- **Title**: Missing operational guidance for rag-src/registered/ file lifecycle
- **Status**: resolved
- **Severity**: Low
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/ingestion/`
- **Owner**: Team
- **First Found**: 2026-08-22
- **Target**: `docs/` directory
- **Related**: File Router, RagIngester
- **Summary**: After successful ingestion, chunk files are moved to `rag-src/registered/` but there is no documentation defining their retention period, deletion trigger, or deletion ownership. This creates uncertainty about how long files persist and who is responsible for cleanup.
- **Current Description**: Retention policy defined via `plans/20260924-080000_plan.md`. Retention period is configurable via `config/ingester.toml`; default 30 days. Cleanup mechanism design is out of scope — requires separate design decision. File Lifecycle table updated with Deletion column in `docs/03_rag_02_01_ingestion_pipeline-overview.md`. `(retention TBD)` placeholder replaced in `docs/03_rag_01_system_overview.md`.
- **Observed Implementation**: Files are MOVED (not copied) to `rag-src/registered/` by `FileRouter.route()` after successful ingestion. No post-move cleanup exists. The ingestion pipeline already logs results and error metadata is written for failed chunks.
- **Impact**: Reduced — retention policy documented; operations teams can configure retention via `config/ingester.toml`. Remaining risk: cleanup mechanism implementation later may conflict with documented policy.
- **Recommended Action**: Monitor retention configuration during operations; adjust retention period periodically based on operational requirements (audit trail vs. disk space). Include retention policy update procedure in acceptance criteria for future `rag-src/registered/` changes.
- **Resolution Target**: Next RAG architecture review
- **Resolved At**: 2026-09-24
- **Resolution Evidence**: `plans/20260924-080000_plan.md`, `docs/03_rag_02_01_ingestion_pipeline-overview.md`, `docs/03_rag_01_system_overview.md`
```

#### Alternative approach considered:

Creating a new issue entry for the retention policy instead of updating the existing one. This was rejected because:
- It would duplicate the historical record of why the Known Issue existed.
- Updating the existing entry preserves the traceability from "gap identified" to "gap closed".
- The original entry provides context for the retention design decisions and policy rationale.

## Compatibility considerations

- The documentation update follows the existing Markdown format used throughout the governance document.
- The field names and structure match the existing RAG-006 entry.
- No changes to other issue entries or the governance document structure.

## Security considerations

- Documentation updates do not introduce security risks beyond what the enforcement mechanism itself introduces.
- The retention period configuration is documented as configurable via `config/ingester.toml` — no speculative additions to the configuration schema.

## Rollback considerations

- If the retention period definition needs revision once operational data shows actual disk usage patterns, the documentation can be updated independently of the enforcement mechanism.
- This documentation update can be rolled back independently of the enforcement mechanism.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_03_issue-and-uncertainty-management.md` | Manual: documentation review | Read RAG-006 section | Status reflects resolution |
| `docs/adr/ADR-002-config-isolation.md` | Manual: documentation review | Read REQ-003 context | Consistent with REQ-003 update |
| `docs/adr/ADR-008-sqlite-4db-separation.md` | Manual: documentation review | Read REQ-003 context | Consistent with REQ-003 update |
| `tests/agent/test_tool_policy.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_policy.py -v` | All tests pass |
| `tests/agent/test_tool_approval_preflight.py` | Regression: existing tests pass | `uv run pytest tests/agent/test_tool_approval_preflight.py -v` | All tests pass |
| New preflight gate tests | Unit: new tests pass | `uv run pytest tests/agent/ -k preflight -v` | All new tests pass |

## Completion criteria

- AC-01: RAG-006 status reflects resolution (REQ-003)
- AC-02: Current Description documents the new retention policy (REQ-003)
- AC-03: Impact reflects reduced risk due to policy definition (REQ-003)
- AC-04: Resolution evidence is listed (REQ-003)
- AC-05: Documentation follows existing Markdown format (REQ-003)

## Out of scope

- Modifying other issue entries; adding new issues; changing the governance document structure; implementing automated cleanup mechanism.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260924-054355_rag006_missing-operational-guidance-rag-src-registered-file-lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-080000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-090000
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
