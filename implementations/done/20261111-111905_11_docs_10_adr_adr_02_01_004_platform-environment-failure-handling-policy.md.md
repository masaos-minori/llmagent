## Goal

Register the two remaining dedup-store degradation paths as approved ADR-004 exceptions with written rationale (`REQ-002`, `REQ-006`): (1) the retryable fail-open (overlay-only `store_error`) and (2) the post-open write-failure warning-only path for retryable tools. The maintainer approval record is written by a maintainer, not fabricated here (`REQ-006`).

## Scope
**Release unit**: N/A: documentation alignment (Plan Implementation steps, Phase 5).

## Assumptions
- ADR-004 is the single authority for how a fail-open must be registered (Plan Reference Files).
- Open (flag, do not fabricate): the exact current wording of the Exceptions section at implementation time (UNK-04); re-read in Step 2.
- The maintainer approval record is a maintainer artifact (`REQ-006`; Plan Risks). This Procedure writes the exception entries and their rationale only; it fabricates no approval record.

## Design decisions
- **Edit the `## Exceptions` section, which the preservation checker does not guard.** `check_adr_preservation.py` ERRORs on changes to front matter, H2 heading sequence, an `INV-NN` invariant, a Related-ADR/Implementation-Reference item, a `path.py::test` citation, or the `## Known Deviations` / `## Approval` text; it WARNs on `Decision`/`Failure Policy`/`Data Ownership and Persistence`/`Invariants` text changes and on a decreased normative-keyword count. The `## Exceptions` section is in NEITHER list, so adding bullets there produces no ERROR and no WARNING — the cleanest way to register the exceptions.
- **Follow the existing PENDING pattern.** The Group 1 registered exception (L67) describes the exception, locates its rationale, and marks it `PENDING (Needs confirmation)` while the maintainer rationale is outstanding. These two entries carry written rationale (the degradation is intentional and justified by replayability) and note that the maintainer approval record is written by a maintainer.
- **Byte-scoped edit.** Every other byte of ADR-004 stays identical.

## Alternatives considered
- **Add the exceptions under `## Decision` (e.g. a new Group item).** Rejected: that changes the guarded `Decision` section (WARNING) and risks altering the numbered decision sequence; the `## Exceptions` section is the designated home for fail-open registrations and is unguarded.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Procedure
1. In the `## Exceptions` section (L244-246), after the existing subprocess-spawn bullet (L246), add two bullets, one per degradation path:

   - **Retryable fail-open (overlay-only `store_error`).** For a *retryable* dispatch-capable MCP tool whose `mcp_dedup.sqlite` is unavailable, lost, or freshly recreated, the shared MCP dispatcher proceeds overlay-only with a `store_error` marker instead of failing closed. Registered exception with rationale: a retryable tool is safely replayable on recovery, so a fail-open that records `store_error` and allows the call to replay preserves availability without risking a silent, unreplayable duplicate effect; the non-retryable counterpart fails closed (see ADR-008). Applies to the empty-store and lookup-exception paths (`scripts/mcp_servers/dispatch.py`). Maintainer approval record: written by a maintainer (`REQ-006`); not fabricated here.

   - **Post-open write-failure warning-only (retryable).** For a *retryable* tool, a failed write to `mcp_dedup.sqlite` after a successful open (e.g. a failed `record_pending`) is warning-only rather than fail-closed. Registered exception with rationale: the pending record for a retryable call is not authoritative — the call is replayable, so a warning-only failure does not risk a silent unreplayable duplicate; the non-retryable counterpart fails closed (`scripts/shared/mcp_dedup.py` `_write()` / `scripts/mcp_servers/dispatch.py` `_store_op`). Maintainer approval record: written by a maintainer (`REQ-006`); not fabricated here.
2. Do NOT modify: the H2 heading sequence (no new `## ` headings), any `INV-NN` (L218-235), the `## Decision` numbered groups (L61-132), the `## Known Deviations` (L308-310), the `## Approval` section (L328-346), the Related ADRs list (L348-352), or the Implementation References list (L354-366). None of these may change.
3. Do NOT fabricate a maintainer approval record or approval date. The two bullets state that the record is a maintainer artifact (`REQ-006`).
4. Re-run `check_adr_preservation.py docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` against `HEAD` and confirm no ERROR.

### Method
- Edit-only: append two bullets under the existing `## Exceptions` H2. No guarded-section change.

### Details
- Keep each bullet to one paragraph so the table-of-contents-style scan stays readable.
- The additions introduce new backtick path tokens (e.g. `scripts/mcp_servers/dispatch.py`); adding tokens is permitted (only *removed* `/`-bearing tokens warn). Do not remove any existing path/symbol token.
- Do not reduce the MUST/MUST NOT/SHOULD/MAY count; the prose adds justifications but deletes none.

## Compatibility considerations
- ADR-004 is read broadly as the failure-handling authority. The byte-scoped Exceptions addition keeps `check_adr_preservation.py`, `check_adr_structure.py`, and `check_adr_authority.py` passing.
- The exceptions registered here correspond to the code paths implemented in `mcp_dedup.py` (seq 01) and `dispatch.py` (seq 02).

## Security considerations
- Low-medium: registering a fail-open makes an intentional availability trade-off explicit and auditable rather than implicit. Both exceptions are scoped to *retryable* tools (safely replayable); the non-retryable guarantee stays fail-closed, so the safety input is not weakened.

## Rollback considerations
Revert the commit. No state or schema changes.

## Validation plan
- `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`: no ERROR.
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`: pass.
- `uv run python tools/stale_detector.py` on this procedure.
- Full validation sequence.

## Completion criteria
- The retryable fail-open and the post-open write-failure warning-only path are listed as ADR-004 exceptions with rationale.
- No maintainer approval record is fabricated (stated as a maintainer artifact, `REQ-006`).
- `check_adr_preservation.py` shows no ERROR.

## Out of Scope
- Classifying the store in ADR-008 (seq 10).
- Implementing the fail-closed rejection (`dispatch.py`, seq 02) or out-of-band detection (`mcp_dedup.py`, seq 01).
- ADR-008 matrix, `db_01`/`db_08`, `db_03_07` (seq 10, 12, 13, 14).
- Config isolation (seq 03-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the two dedup degradation paths as ADR-004 exceptions with rationale | Pending | — | — | Byte-scoped; maintainer approval record not fabricated |
| 2 | Add or update tests per Validation plan | Pending | — | — | none (doc) |
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
- **Requirement ID**: `REQ-002`, `REQ-006` — ADR-004 exception registry for the retryable fail-open and post-open write-failure
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Companion test files
- none (documentation change; verified by `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_authority.py`).
- Validation: preservation check shows no ERROR.
