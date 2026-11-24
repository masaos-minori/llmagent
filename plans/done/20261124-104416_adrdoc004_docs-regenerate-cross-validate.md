## Goal
- Finish the ADR-006 and ADR-008 documentation change set: confirm that generated references, the ADR authority graph, and the invariant matrix match the approved model; remove the retired memory, JSONL, and four-database terminology from the remaining current-specification documents (sixteen files); and run the complete documentation, ADR, link, and generated-reference validation suite with saved evidence. Historical records, tests, code, and generated references that follow code stay unchanged, and each is classified.

## Priority
Low

## Scope
- **In-Scope**: the remaining current-specification documents that still describe the retired memory model (Semantic/Episodic, memory JSONL, `/memory` operations, pinned memories, `memory prune`), the JSONL-based memory recovery runbooks, or a four-database label of ADR-008; the repository-wide terminology search with a classification of every hit; the regeneration and drift confirmation of the ADR and reference generators; the validation suite and its saved evidence.
- **Out-of-Scope**: the ADR, EventBus, and Agent memory and CLI documents already changed by the earlier plans; code, tests, configuration, scripts, and tool baselines (they carry the retired names until the implementation issues SHARED-003 and EVENTBUS-001 land); generated reference documents and manifests (they follow the code); archived issues, plans, and procedures; the ADR-008 file rename; the open implementation work on the retired features.
- **Dependencies**: Depends on the ADR amendment (adrdoc001), the EventBus documentation rewrite (adrdoc002), and the Agent memory and CLI documentation rewrite (adrdoc003), all complete and archived, so no ordering bullet is needed. Compatible overlaps with the open issues mdqmcp004, mdqmcp006, and the unknowns file 20261123-120131_02 (they edit the MDQ parts of the DB migration document), and mcpai012 (it edits the ADR-004 and MCP design documents): this Plan edits different lines and neither is a precondition.

## Background
The Issue was filed from `memo-issue.md` as the final cross-document pass. The three earlier plans are implemented and pushed: ADR-006 and ADR-008 are amended (Known Issues EVENTBUS-001, EVENTBUS-002, SHARED-003, SHARED-004 track where code differs), the EventBus documents are rewritten, and the eleven Agent memory and CLI documents are rewritten. Repository evidence checked on 2026-11-24:
- Generated content already matches: `uv run python tools/generate_reference_table.py --check` and `uv run python tools/generate_adr_authority.py --check` report no drift, and `tools/check_adr_*`, `check_known_deviation_sync`, and the Needs Confirmation inventory checks pass. The EventBus and memory API manifests, and the generated reference documents `agent_11_04`, `agent_13`, and `agent_14`, are derived from `scripts/eventbus/*.py`, `scripts/agent/memory/*.py`, and `scripts/agent/*.py`, which are unchanged, so they still list the JSONL and `/memory` symbols.
- A refined terminology search (the `/memory` pattern excluding the `agent/memory/` path) finds retired memory terms in nine non-generated Agent documents, three DB documents, and the deployment document: `agent_01` (MemoryServices described as a semantic memory layer), `agent_04_01` (long-term memory changed by `/memory` and recovered from the JSONL archive), `agent_04_02` (a "Memory JSONL / memories table" persistence row), `agent_04_03` (memory table ownership, `JsonlMemoryStore`, `prune_old_memories()` called from `/memory`), `agent_08_01` and `agent_08_03` (memory configuration keys `memory_jsonl_dir`, `memory_min_importance`, `memory_retention_days`, `memory_max_pinned`), `agent_09_02` (session access patterns and memory operations), `agent_10_06` (a "Memory Status (`/memory status`)" section with a pinned count), `agent_12` ("Optional persistent semantic memory subsystem"), `db_03` (recover memory from the JSONL archive with `/memory rebuild`), `db_05` and `db_06` (memory store and `prune_old_memories`), and `deployment_01` (recovery step "Recover memory" with `/memory rebuild`).
- The four-database label survives in three places: `db_03_07` ("a fifth database file outside the original four-database set"), `db_08` (the link text "Separating SQLite into Six Databases"), and `adr_02_01_004` (the Related ADRs entry "SQLite Four-Database Separation"). The 4db file name tokens in links and front matter are path tokens that stay until the rename. Other "four platform databases" statements (`deployment_01`, `shared_01`, ADR-008 Review Triggers) are accurate and stay.
- Hits that are not current specifications stay unchanged: the ADR texts, the governance ledger and Known Issues, and the ADR index matrix (they state the removal or cite the deviation); the generated references; tests, scripts, `tools/*_baseline.txt` files, `requires/done/`, and archived issues, plans, and procedures.
- `ADR-004` sits 19 bytes below its `tools/check_docs_structure.py` size ceiling (36248 of 36267), so the Related ADRs label there must not grow by more than that.
- The CI jobs that cover documentation: `.github/workflows/ci.yml` runs the reference-table and ADR authority checks, and the per-domain workflows `agent-docs-consistency.yml`, `deployment-docs-consistency.yml`, `governance-docs-consistency.yml`, `mcp-docs-consistency.yml`, `overview-docs-consistency.yml`, and `rag-docs-consistency.yml` run `check_docs_consistency.py --domain`. All eight domains (agent, eventbus, db, deployment, overview, shared, rag, mcp) pass today, with one pre-existing warning in the generated `agent_14`.

## Problem
Correct prose changes in the ADRs and in the three rewritten document sets can still leave the repository inconsistent: obsolete current-specification text remains in sixteen other files, including recovery runbooks that tell operators to recover memory from a JSONL archive that the ADR no longer recognizes, and the validation evidence for the whole change set has not been collected in one place.

## Reason for Change
The runbook statements are a wrong-action risk (an operator follows `/memory rebuild` after a Session DB recreation), but they are no longer the only recovery guidance in the ADRs and the Agent documents, so the urgency is low and the work is a consistency finish. The change set is complete only when the cross-document checks pass together.

## Implementation Intent
Keep generated content generator-owned, and touch only current-specification prose. For each retired term, remove or correct it where it describes current behavior, and keep it where it is a historical or test or code artifact. Where code still implements the retired feature (SHARED-003, EVENTBUS-001), a document names the feature as retired and cites the Known Issue, as the earlier plans do. Recovery runbooks state the ADR-008 rule: the Session DB is recovered only from a verified backup, and Episodic Memory is not carried over after a schema-mismatch recreation (the undecided part cites SHARED-004). Then run the full validation suite and keep the commands and results as evidence for the commit.

## Requirements
- `REQ-001`: The Agent documents `agent_01`, `agent_04_01`, `agent_04_02`, `agent_04_03`, `agent_09_02`, `agent_10_06`, and `agent_12` describe Episodic Memory and Repository Context (or the retired feature) consistently with ADR-008, with no Semantic Memory, memory JSONL as a store or recovery source, `/memory` operation, pin, or manual-write description as current behavior.
- `REQ-002`: The configuration documents `agent_08_01` and `agent_08_03` mark the memory configuration keys that belong to the retired model (`memory_jsonl_dir`, `memory_min_importance`, `memory_retention_days`, `memory_max_pinned`) as retired by ADR-008 and scheduled for removal (SHARED-003), without describing their former effect, and keep the keys that still apply to Episodic retrieval.
- `REQ-003`: The recovery runbooks in `db_03`, `deployment_01`, and the memory-related statements in `db_05` and `db_06` state the ADR-008 rule: no JSONL archive and no `/memory rebuild`; the Session DB is recovered from a verified backup; Episodic Memory is not carried over after a schema-mismatch recreation, and the final policy is undecided (SHARED-004).
- `REQ-004`: The four-database labels in `db_03_07`, `db_08`, and `adr_02_01_004` are updated to the six-store wording, and the ADR-004 label stays within the file's size ceiling.
- `REQ-005`: The generators and manifests are confirmed current: `tools/generate_adr_authority.py`, `tools/generate_reference_table.py --check`, and the contract manifests show no drift; no JSONL or `/memory` symbol is hand-removed from a generated reference, and no unapproved retention, health, replay-floor, Repository Context, or Episodic Memory symbol is added to one.
- `REQ-006`: Every hit of the retired terms across the repository is classified as a current specification, historical record, archived issue, migration record, test fixture, code, or removed-name statement; only current specifications are edited.
- `REQ-007`: The full validation suite runs and its commands and results are saved: documentation lint and quality, internal links and paths, canonical-source conflicts, the ADR checks, generated-reference drift, CLI command and usage coverage, the EventBus, DB, deployment, overview, shared, RAG, and MCP consistency domains, the DB-separation check, and the existence of every cited file and test node.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_01_system-overview.md` | Modify: component table row for the memory services | Replace "Optional semantic memory layer" with the Episodic Memory wording | REQ-001; AC-01 | Component table row at line 62 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Modify: session and memory boundary text | Replace the `/memory` and JSONL recovery statements with the Episodic rule | REQ-001; AC-01 | Lines 155 to 157 name `/memory` operations and the JSONL archive (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Modify: persistence table row | Replace the "Memory JSONL / memories table" row with the SQLite-only Episodic row | REQ-001; AC-01 | Row at line 139 lists JSONL plus SQLite (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify: DB ownership, memory note, logical ownership, retention | Replace the memory table ownership, the JSONL store note, and the `/memory` prune statement | REQ-001; AC-01 | Lines 46 to 65 name the memory tables, `JsonlMemoryStore`, and `prune_old_memories()` (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Modify: configuration key table rows | Mark the retired memory keys | REQ-002; AC-02 | Rows at lines 175 to 186 (`memory_jsonl_dir`, `memory_min_importance`, `memory_retention_days`, `memory_max_pinned`) (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Modify: memory configuration constraints | Mark the retired keys and the `/memory prune` and pin statements | REQ-002; AC-02 | Lines 72 and 73 describe `/memory prune` and the pin cap (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | Modify: session and memory access statement | Replace the memory operations wording with the Episodic boundary | REQ-001; AC-01 | Line 63 names memory operations beside session operations (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Modify: Memory Status section | Replace the `/memory status` section (mode, pinned count) with the diagnostics owner (`/stats`, SHARED-003) | REQ-001; AC-01 | Section at lines 53 to 58 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_12_reference-api.md` | Modify: MemoryServices role description | Replace "Optional persistent semantic memory subsystem" | REQ-001; AC-01 | Role line at line 209 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify: Session DB recreation procedure and recovery table | Replace the `/memory rebuild` and JSONL recovery steps with the ADR-008 rule | REQ-003; AC-03 | Steps at lines 36 to 41 and the table row at line 85 (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify: store inventory sentence | Replace "a fifth database file outside the original four-database set" with the six-store wording | REQ-004; AC-04 | Sentence at line 35 (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_05_api_and_operations-protocol-and-backend.md` | Modify: memory store note | Remove the JSONL-related and memory-table statements for the retired model | REQ-003; AC-03 | Memory store paragraph at line 34 (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Modify: maintenance functions list | Describe `prune_old_memories` as removal-pending, not a supported maintenance operation | REQ-003; AC-03 | Lines 24 and 26 list `prune_old_memories` (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/41_db/db_08_active_databases.md` | Modify: ADR-008 link text | Replace "Separating SQLite into Six Databases" with the amended title | REQ-004; AC-04 | Link text at line 118 (checked in Step 3) | `tools/check_docs_consistency.py --domain db` | Verified |
| `docs/90_deployment/deployment_01_deployment.md` | Modify: Session DB recreation runbook | Replace the "Recover memory" step and the pinned-memory note with the ADR-008 rule | REQ-003; AC-03 | Steps at lines 314 and 319 (checked in Step 3) | `tools/check_docs_consistency.py --domain deployment` | Verified |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify: Related ADRs label of ADR-008 | Replace "SQLite Four-Database Separation" with a six-store label no longer than 12 bytes longer, to stay under the size ceiling | REQ-004; AC-04 | Label at line 363; file size 36248 against the ceiling 36267 in `tools/check_docs_structure.py` (checked in Step 3) | `tools/check_adr_reference.py`, `tools/check_docs_structure.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Amended source of the memory model, schema-mismatch rule, and recovery decisions | REQ-001, REQ-003 |
| `docs/10_adr/adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` | Amended EventBus decisions, for the classification of EventBus hits | REQ-006 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issues SHARED-003, SHARED-004, EVENTBUS-001, EVENTBUS-002 that the documents cite | REQ-001 to REQ-003 |
| `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | The rewritten memory overview that the Agent documents link to | REQ-001 |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | The Session DB recovery scope that the runbooks restate | REQ-003 |
| `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Generated memory reference; follows the code, no change | REQ-005 |
| `docs/23_agent/agent_13_reference-api-generated.md` | Generated Agent reference; follows the code, no change | REQ-005 |
| `docs/23_agent/agent_14_reference-api-subpackages-generated.md` | Generated Agent subpackage reference; follows the code, no change | REQ-005 |
| `registry/manifests/memory_api.yaml` | Memory API manifest derived from code, no change | REQ-005 |
| `registry/manifests/eventbus_api.yaml` | EventBus API manifest derived from code, no change | REQ-005 |
| `registry/manifests/agent_api.yaml` | Agent API manifest derived from code, no change | REQ-005 |
| `tools/generate_reference_table.py` | Generator and drift checker for the references | REQ-005 |
| `tools/generate_adr_authority.py` | Generator of the guarded ADR index sections | REQ-005 |
| `tools/check_docs_structure.py` | Per-file size ceilings that limit label growth | REQ-004 |
| `config/documentation_canonical_sources.toml` | Canonical-source declarations used by the conflict check | REQ-007 |
| `.github/workflows/ci.yml` | CI job commands that the evidence must cover | REQ-007 |

## Acceptance Criteria
- `AC-01` (REQ-001): no current-specification Agent document among the seven targets describes Semantic Memory, memory JSONL as a store or recovery source, `/memory` operations, or pinned memories as current behavior.
- `AC-02` (REQ-002): the memory configuration documents mark the retired keys as retired by ADR-008 and scheduled for removal (SHARED-003).
- `AC-03` (REQ-003): no recovery runbook recommends `/memory rebuild` or a JSONL archive; each states the verified-backup rule and the undecided Episodic handling (SHARED-004).
- `AC-04` (REQ-004): no current document labels ADR-008 as a four-database ADR or with its old title, and `tools/check_docs_structure.py` passes without a ceiling change.
- `AC-05` (REQ-005): `generate_adr_authority.py --check`, `generate_reference_table.py --check`, and the contract manifest checks pass, and the generated references and manifests are unchanged by this Plan.
- `AC-06` (REQ-006): the classification of every retired-term hit is recorded in the implementation report, and only current-specification documents were edited.
- `AC-07` (REQ-007): all documentation, ADR, authority, generated-reference, command and usage coverage, domain consistency, link, and citation checks pass, with the commands and results recorded as evidence.

## Tests
- `REQ-001` to `REQ-004`: documentation-only, so no automated test is added; evidence is the domain consistency checks and the documentation checks in the Validation plan.
- `REQ-005`: `uv run python tools/generate_reference_table.py --check`, `uv run python tools/generate_adr_authority.py --check`, and `uv run python tools/check_adr_authority.py`.
- `REQ-006`: the terminology search commands and their classified result list.
- `REQ-007`: the full suite in the Validation plan, plus `uv run python .github/run_cited_adr_tests.py` for the existence and result of every cited test node.

## Documentation Impact
Yes. The sixteen target documents are the documentation, reached through `docs/00_index.md` for the Agent, DB, and deployment areas. They record the Episodic and Repository Context boundary, the recovery rule, the retired configuration keys, and Known Issue citations (SHARED-003, SHARED-004). The generated references change only when the code changes.

## Assumptions
- The documents cite SHARED-003 (code still implements the retired memory model, keys, and `/memory`) or SHARED-004 (Episodic recovery and retention policy undecided) instead of describing code behavior as supported; no `Needs Confirmation` marker is added, because each marker needs an inventory entry.
- Hits in code, tests, scripts, tool baselines, `requires/done/`, and archived issues, plans, and procedures are historical, test, code, or removed-name artifacts and are not edited by this Plan.
- The generated references (`agent_11_04`, `agent_13`, `agent_14`) and the manifests follow the code and are not edited; the pre-existing `/db` warning in `agent_14` is a code and generator matter and stays.
- The Related ADRs label in ADR-004 uses a short six-store label because the file has 19 bytes of headroom under its size ceiling; the full ADR-008 title is not required there.
- "Four platform databases" statements that name the four platform-domain databases are accurate under ADR-008 and stay.
- The 4db file name in links and front matter stays until the rename follow-up.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The supported recovery step for memory after a Session DB recreation | ADR-008 states Episodic Memory is not carried over and records the destructive-recreation policy as undecided | The runbooks state the verified-backup rule and the ADR-008 not-carried-over statement and cite SHARED-004 | False |
| UNK-02 | Whether the retired configuration keys will be removed from `config/agent.toml` and the dataclasses | No implementation issue defines it | The documents mark the keys retired and scheduled for removal (SHARED-003) and do not describe their effect | False |
| UNK-03 | Removal of the JSONL and `/memory` symbols from the generated references | They follow the code, which still holds them (EVENTBUS-001, SHARED-003) | The generators refresh the references when the code issues land; this Plan only confirms no drift | False |
| UNK-04 | Overlap with the open issues mdqmcp004, mdqmcp006, the unknowns file 20261123-120131_02, and mcpai012 on the DB migration and ADR-004 documents | Those issues are open and not yet planned against these documents | Compatible overlap: this Plan edits only the memory and label lines | False |
| UNK-05 | Whether CI runs documentation checks beyond the ones named in `.github/workflows/` and `rules/tool-gates.md` | The workflow files were read only by name and command grep | The validation evidence covers every command found; a gap is reported rather than assumed | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_01_system-overview.md` | Modify | Low | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Modify | Medium (cited as the session and memory boundary) | 6 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Modify | Low | 1 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | Medium | 3 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Modify | Medium (configuration key table) | 4 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Modify | Medium | 7 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | Modify | Low | 1 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Modify | Low | 1 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_12_reference-api.md` | Modify | Low | 1 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | High (recovery runbook; churn 14 in 30 days) | 14 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Modify | Low | 2 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/41_db/db_05_api_and_operations-protocol-and-backend.md` | Modify | Low | 2 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Modify | Medium | 7 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/41_db/db_08_active_databases.md` | Modify | Low | 3 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/90_deployment/deployment_01_deployment.md` | Modify | High (operator runbook) | 9 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Modify | Medium (at its size ceiling) | 13 | 2 authors in 365 days | not applicable (rsynced) |

## Design
Classification: Path B (sixteen target rows, more than three).

Analysis (documentation only; no Python target, so the radon, vulture, and bandit baseline is `N/A: no Python target`):
- Search method: a terminology search over `docs/` with the retired memory terms, using a pattern that excludes the valid `agent/memory/` path, then the EventBus JSONL terms and the four-database labels; hits outside `docs/` are classified without edits.
- Classification table (recorded in the implementation report, not as a repository file): current specification (edit), historical record, archived issue, migration record, test fixture, code, removed-name statement (the ADR texts, ledger, Known Issues, and index matrix rows that state the removal).
- Coupling: `check_docs_consistency.py` domains (agent, db, deployment) verify links, `scripts/` paths, backticked function references, config keys of the form `*_db_path`, and command coverage; the Agent config key tables (`agent_08_01`, `agent_08_03`) describe keys that still exist in `config/agent.toml` and the dataclasses, so the rows are kept and marked retired rather than deleted.
- Content policy and size: edits mostly shorten text; the only growth-limited file is ADR-004 (19 bytes of headroom).
- Consumer scan and predictable fallout check: no persisted schema, public API, shared constant, or code symbol changes, so `tools/scan_change_consumers.py` is not applicable. Pinned counts: no test asserts a documentation count; tool inventory and module size: `not affected`; generated blocks: unchanged by design (`generate_reference_table.py --check` is a validation step); size ceilings: only ADR-004 is within headroom, handled by the short label.
- Operational check: no process or database is touched (not run, documentation only). Persisted schema check (`rules/persisted-schema-change.md`): not applicable, no DDL or migration changes.

Decisions:
- Retired configuration keys stay in the key tables as marked rows (they still exist in code) instead of being deleted.
- Runbooks state the verified-backup rule once and link to the Session DB document instead of repeating the full policy.
- The validation evidence is produced during implementation and reported in the final report and the commit message; no evidence file is added to the repository.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. All steps edit documentation text only.

1. **Phase 1: Agent documents**
   - [ ] Replace the retired memory descriptions in the Agent overview, state, platform-database, access-pattern, diagnostics, and reference documents (REQ-001; `docs/23_agent/agent_01_system-overview.md`, `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `docs/23_agent/agent_09_02_data-layer-access-patterns.md`, `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`, `docs/23_agent/agent_12_reference-api.md`)
   - [ ] Mark the retired memory configuration keys (REQ-002; `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`)
2. **Phase 2: DB, deployment, and label updates**
   - [ ] Replace the JSONL and `/memory rebuild` recovery text with the ADR-008 rule (REQ-003; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, `docs/90_deployment/deployment_01_deployment.md`)
   - [ ] Update the four-database labels (REQ-004; `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_08_active_databases.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`)
3. **Phase 3: Classification and validation**
   - [ ] Run the terminology search, classify every hit, confirm the generators and manifests show no drift, and run the full validation suite with its evidence recorded (REQ-005, REQ-006, REQ-007; all target files)

### Release units
**Unit**: terminology-sweep | **Phases**: 1, 2 | **Reason**: the Agent, DB, and deployment documents link to each other and to the rewritten memory documents, and the domain consistency checks validate links and references across them, so changing a runbook while a linked document still describes the retired model, or changing a label before the checks run together, can fail the cross-document checks; the phases land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All sixteen target documents | Domain consistency (links, paths, references, command coverage) | `uv run python tools/check_docs_consistency.py --domain agent`, `--domain db`, `--domain deployment`, `--domain overview`, `--domain shared`, `--domain eventbus`, `--domain rag`, `--domain mcp` | No new findings (one pre-existing generated `/db` warning) |
| All sixteen target documents | Structure, quality, content policy, metadata, language | `uv run python tools/check_docs_structure.py`, `tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_metadata_field_policy.py`, `tools/check_docs_japanese.py` | No findings |
| ADR files and governance | ADR checks and citations | `uv run python tools/check_adr_structure.py`, `check_adr_authority.py`, `check_adr_reference.py`, `check_adr_invariant_matrix.py`, `check_known_deviation_sync.py`, `check_needs_confirmation_inventory.py` | No findings |
| Generated content | Drift of generated blocks and manifests | `uv run python tools/generate_adr_authority.py --check`, `uv run python tools/generate_reference_table.py --check` | No drift |
| ADR-cited tests | Existence and result of every cited node | `uv run python .github/run_cited_adr_tests.py` | All cited tests pass |
| DB separation | Static check and tests | `uv run python tools/check_db_separation.py`, `uv run pytest tests/tools/test_check_db_separation.py -q` | Pass |
| CLI command and usage coverage | Documented commands match the registry | `uv run pytest tests/docs/test_command_docs_sync.py -q` | Pass |
| All sixteen target documents | Gate runner for the changed files | `uv run python tools/run_validation_gates.py` | No `Fail` or `Blocked` |
| Terminology | Classified search result | `rg` with the retired-term patterns over the repository | Every hit classified; no current-specification hit remains |

## Risks
- **Risk**: A runbook edit removes the only recovery instruction an operator has for memory → **Mitigation**: the runbook states the ADR-008 rule (verified backup, Episodic Memory not carried over) and links to the Session DB document, and SHARED-004 marks the undecided part.
- **Risk**: The retired configuration keys still exist in `config/agent.toml`, so a reader may think they were removed → **Mitigation**: rows are kept and marked retired by ADR-008 and scheduled for removal (SHARED-003).
- **Risk**: An edit grows ADR-004 beyond its size ceiling and fails `check_docs_structure.py` → **Mitigation**: use the short six-store label and run the structure check before commit; do not change the ceiling in this Plan.
- **Risk**: The terminology search over-matches valid names (the `agent/memory/` path, `USER MEMORY` framing, mode names) and removes valid text → **Mitigation**: the refined pattern and the classification table; only retired-feature descriptions are edited.
- **Risk**: High churn on `db_03` (14 commits in 30 days) and overlap with open issues causes merge conflicts → **Mitigation**: edit only the memory lines, sync immediately before the commit, and re-run the DB consistency check after any rebase.
- **Risk**: Generated references still list retired symbols, so a reader sees them as supported → **Mitigation**: UNK-03; the retired list in the module reference and the Known Issues make the status explicit, and the generators refresh them when the code changes.
- **Risk**: A `Needs Confirmation` marker added without an inventory entry fails the inventory check → **Mitigation**: no such marker is written; Known Issue citations are used.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Agent documents: retired memory descriptions and configuration keys | Completed | — | 20261124-110729 |  |
| 2 | DB, deployment, and label updates | Completed | — | 20261124-110729 |  |
| 3 | Terminology classification, generator confirmation, and full validation suite | Completed | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261124-105117_01_docs_23_agent_agent_01_system-overview.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_02_docs_23_agent_agent_04_01_state-and-persistence-state-model.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_03_docs_23_agent_agent_04_02_state-and-persistence-history-compression.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_04_docs_23_agent_agent_04_03_state-and-persistence-platform-databases.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_05_docs_23_agent_agent_08_01_configuration-loading-agent-config.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_06_docs_23_agent_agent_08_03_configuration-tools-memory.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_07_docs_23_agent_agent_09_02_data-layer-access-patterns.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_08_docs_23_agent_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_09_docs_23_agent_agent_12_reference-api.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-105117_10_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_11_docs_41_db_db_03_07_mcp-dedup-and-execution-snapshot.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_12_docs_41_db_db_05_api_and_operations-protocol-and-backend.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_13_docs_41_db_db_06_api_and_operations-maintenance-and-rotation.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_14_docs_41_db_db_08_active_databases.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_15_docs_90_deployment_deployment_01_deployment.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-105117_16_docs_10_adr_adr_02_01_004_platform-environment-failure-handling-policy.md.md | 2 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261124-093930_adrdoc004_docs-regenerate-cross-validate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261124-104416
- **Related target files**: `docs/23_agent/agent_01_system-overview.md`, `docs/23_agent/agent_04_01_state-and-persistence-state-model.md`, `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `docs/23_agent/agent_08_01_configuration-loading-agent-config.md`, `docs/23_agent/agent_08_03_configuration-tools-memory.md`, `docs/23_agent/agent_09_02_data-layer-access-patterns.md`, `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`, `docs/23_agent/agent_12_reference-api.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md`, `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`, `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md`, `docs/41_db/db_08_active_databases.md`, `docs/90_deployment/deployment_01_deployment.md`, `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes B; agent_01 line 62 | `docs/23_agent/agent_01_system-overview.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_04_01 lines 155 to 157 | `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_04_02 line 139 | `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_04_03 lines 46 to 65 | `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_09_02 line 63 | `docs/23_agent/agent_09_02_data-layer-access-patterns.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_10_06 lines 53 to 58 | `docs/23_agent/agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes B; agent_12 line 209 | `docs/23_agent/agent_12_reference-api.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-002 | Required Changes B; agent_08_01 lines 175 to 186 | `docs/23_agent/agent_08_01_configuration-loading-agent-config.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-02) |
| REQ-002 | Required Changes B; agent_08_03 lines 72 and 73 | `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-02) |
| REQ-003 | Required Changes B; db_03 lines 36 to 41 and 85 | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain db` | Needs confirmation (UNK-01) |
| REQ-003 | Required Changes B; db_05 line 34 | `docs/41_db/db_05_api_and_operations-protocol-and-backend.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain db` | Derived from confirmed evidence |
| REQ-003 | Required Changes B; db_06 lines 24 and 26 | `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain db` | Derived from confirmed evidence |
| REQ-003 | Required Changes B; deployment_01 lines 314 and 319 | `docs/90_deployment/deployment_01_deployment.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain deployment` | Needs confirmation (UNK-01) |
| REQ-004 | Required Changes B; db_03_07 line 35 | `docs/41_db/db_03_07_mcp-dedup-and-execution-snapshot.md` | Phase 2 | AC-04 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Required Changes B; db_08 line 118 | `docs/41_db/db_08_active_databases.md` | Phase 2 | AC-04 | `check_docs_consistency.py --domain db` | Confirmed by repository evidence |
| REQ-004 | Required Changes B; adr_02_01_004 line 363 | `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md` | Phase 2 | AC-04 | `check_adr_reference.py`, `check_docs_structure.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes A; generators report no drift | `docs/23_agent/agent_01_system-overview.md` | Phase 3 | AC-05 | `generate_reference_table.py --check`, `generate_adr_authority.py --check` | Confirmed by repository evidence |
| REQ-006 | Required Changes B; terminology search | `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Phase 3 | AC-06 | classified `rg` result | Derived from confirmed evidence |
| REQ-007 | Required Changes C; validation suite | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 3 | AC-07 | Validation plan checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261124-105117 -->