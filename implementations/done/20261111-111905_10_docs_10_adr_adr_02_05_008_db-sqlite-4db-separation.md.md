## Goal

Classify `mcp_dedup.sqlite` as a disposable cache in ADR-008 (owner = shared MCP dispatcher layer, recovery by recreation, no backup) and add its post-recreation rule to the Recovery Policy Matrix (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: documentation alignment (Plan Implementation steps, Phase 5). Blocks adrrev009, which records the matrix outcome this Procedure produces — Freeze the classification here before adrrev009 implements it.

## Assumptions
- The maintainer's 2026-11-09 decision stands: `mcp_dedup.sqlite` is a disposable cache (Option B); recovery is recreation; no backup.
- Open (flag, do not fabricate): the exact current wording of ADR-008's matrix rows and the "Derived Stores" section at implementation time (UNK-04); re-read the file in Step 2.
- Overlap (flag, do not resolve): adrrev009 / adrrev012 / adrrev014 also touch ADR-008. This Plan owns the frozen `mcp_dedup.sqlite` classification and its matrix row; adrrev009 aligns the recovery procedure to it. Coordinate so adrrev009 does not re-open the classification.

## Design decisions
- **Classify via prose + matrix, not via the Implementation References list.** `check_adr_preservation.py` reports ERROR when an *Implementation References* or *Related ADRs* list item is added or changed, and when a `path.py::test` citation is added. So classify `mcp_dedup.sqlite` in the "Derived Stores Outside the Four Domains" prose and the Recovery Policy Matrix only — do NOT add a bullet to the Implementation References list (that would trip the ERROR).
- **Byte-scoped edit.** Every other byte of ADR-008 stays identical. The checker ERRORs on any change to front matter, H2 heading sequence, an `INV-NN` invariant, a Related-ADR/Implementation-Reference item, a `path.py::test` citation, or the `## Known Deviations` / `## Approval` text; it WARNs on `Decision`/`Failure Policy`/`Data Ownership and Persistence`/`Invariants` text changes and on a decreased normative-keyword count. This edit lands in the `Decision` section (WARNING only) and must not touch the ERROR-guarded sections.

## Alternatives considered
- **Add `mcp_dedup.sqlite` to the four-domain matrix as a fifth column.** Rejected as primary: the store is explicitly *outside* the four domains (like `mdq.sqlite`), so the "Derived Stores Outside the Four Domains" prose is the correct classification home. The matrix still gets a row/column for the post-recreation rule per the plan; see Procedure.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. **Classify in prose.** In "Derived Stores Outside the Four Domains" (currently L135-138), add a second bullet after the `mdq.sqlite` bullet (L137) and before the "Adding a system of record..." sentence (L138):

   > - `mcp_dedup.sqlite` is owned by the shared MCP dispatcher and holds only the dedup ledger (`tool_call_state`). It is a **disposable cache**, not a system of record: it is recreated (empty) after loss or corruption, is not backed up or restored by `recover_corruption()` or `rotate_all_dbs()`, and after recreation non-retryable tools are rejected (fail closed) until an operator resolves the state. Its schema migration is the dispatcher service's own responsibility.

   This states owner, disposable-cache classification, recovery-by-recreation, and no-backup without copying config values.
2. **Add the post-recreation rule to the Recovery Policy Matrix** (Decision section, header L88; 19 field rows L90-108; columns `rag.sqlite` … `eventbus.sqlite`). Append a fifth column `mcp_dedup.sqlite` to the header (L88) and one cell to each field row (L90-108). Values (disposable cache, dispatcher-owned): persistence-domain identifier = outside the four domains (dispatcher-owned dedup store); database file = `mcp_dedup.sqlite`; system of record = none (disposable `tool_call_state` ledger); derived/rebuildable = none (recreated empty); owning component = Shared MCP dispatcher layer; required service stop scope = shared MCP dispatcher process; supported diagnosis path = none automated; supported recovery source = none (no backup, recreation); automatic restore prohibited; manual restore = not applicable (recreation, not restore); operator approval = required to resolve lost/recreated state before non-retryable replay; backup retention = none; WAL/checkpoint = not applicable; physical integrity verification = not applicable; logical verification = none automated; service restart = dispatcher restart after recreation; rollback = not applicable; audit requirement = same (error/audit excludes row-level content); data-loss disclosure = not applicable (disposable; completed non-retryable replay is blocked, not restored).
3. **Do not** add `mcp_dedup.sqlite` to the Implementation References list (L396-411), the Related ADRs list (L388-394), any `INV-NN` (L246-265), the `## Known Deviations` (L347-349), the `## Approval` section (L368-386), or any `path.py::test` citation in the Verification table (L303-314). None of these may change.
4. Re-run `check_adr_preservation.py docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` against `HEAD` and confirm only a `Decision`-section WARNING (with a sentence-level mapping) — no ERROR.

### Method
- Edit-only prose + one matrix column, all inside the `## Decision` section. No front-matter, H2-sequence, invariant, reference, or approval change.

### Details
- The matrix edit increases the `Decision` section size; provide the sentence-level mapping in the change report (the checker's WARNING contract).
- Do not reduce any normative-keyword (MUST/MUST NOT/SHOULD/MAY) count; the additions can add MAY/MUST prose but must not delete existing ones.
- Keep the matrix cells terse so the table stays aligned.

## Compatibility considerations
- ADR-008 is read by `check_db_separation.py`, `check_docs_consistency.py --domain db`, `check_adr_authority.py`, `check_adr_structure.py`, and `check_adr_preservation.py`. The byte-scoped edit must keep all of those passing.
- adrrev009 records the matrix outcome; this frozen classification is what adrrev009 aligns to.

## Security considerations
- Low: documentation only. The classification makes the recovery behaviour explicit (disposable cache → recreate; non-retryable fail closed until resolved), which strengthens, not weakens, the non-retryable guarantee.

## Rollback considerations
Revert the commit. No state or schema changes.

## Validation plan
- `uv run python tools/check_adr_preservation.py docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`: only a `Decision`-section WARNING; no ERROR.
- `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`: pass.
- `uv run python tools/check_db_separation.py`, `check_docs_consistency.py --domain db`: pass; store classified identically as disposable cache (also in `db_03_07`, `db_08`).
- `uv run python tools/stale_detector.py` on this procedure.
- Full validation sequence.

## Completion criteria
- `mcp_dedup.sqlite` is classified as a disposable cache (owner, recovery by recreation, no backup) in ADR-008.
- The Recovery Policy Matrix carries the post-recreation rule for non-retryable tools.
- `check_adr_preservation.py` shows no ERROR; the store appears in `db_08` and the dependency graph.

## Out of Scope
- Implementing the fail-closed rejection (`dispatch.py`, seq 02) or the out-of-band detection (`mcp_dedup.py`, seq 01).
- Registering the ADR-004 exceptions (seq 11).
- The maintainer approval record: written by a maintainer, not fabricated here (REQ-006).
- Config isolation (seq 03-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Classify `mcp_dedup.sqlite` as disposable cache in ADR-008 prose + Recovery Policy Matrix | Pending | — | — | Byte-scoped; blocks adrrev009 |
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
- **Requirement ID**: `REQ-005`, `REQ-006` — ADR-008 disposable-cache classification and Recovery Policy Matrix row
- **Source issue**: `issues/20261109-112844_adrrev008_mcp-dedup-ownership.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261110-230633_adrrev008_mcp-dedup-ownership.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-111905
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Companion test files
- none (documentation change; verified by `check_adr_preservation.py`, `check_adr_structure.py`, `check_adr_authority.py`, `check_db_separation.py`, `check_docs_consistency.py --domain db`).
- Validation: preservation check shows no ERROR.
