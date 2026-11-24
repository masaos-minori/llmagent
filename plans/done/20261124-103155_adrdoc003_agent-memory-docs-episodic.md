## Goal
- Rewrite eleven Agent documents under `docs/23_agent/` so the CLI, reload, diagnostics, context-budget, Session DB, and memory documentation consistently describe the amended ADR-008 model: Repository Context (loaded from configured repository files, never persisted) and Episodic Memory (the only persistent Agent memory, stored only in `session.sqlite`, with no user-facing CRUD). The Semantic Memory model, memory JSONL, pin and unpin, manual memory writes, `/memory` as a contract, and JSONL rebuild are removed from current guidance. Where the code and CLI do not yet match, each statement cites the Known Issue that tracks the difference, and no configuration key, diagnostic field, category name, or policy is invented.

## Priority
Medium

## Scope
- **In-Scope**: the CLI reference index, command registry, hot-reload, session and MCP commands, context and plan commands, workflow and debug commands, and the memory-and-other commands document; the Session DB data-layer document; the memory overview, data-model, and module-reference documents; Repository Context and Episodic Memory definitions; the `/reload`, `/stats`, `/context`, `/debug verbose`, and `/session recover` responsibilities; the context-budget rules; the Session DB backup and recovery statements.
- **Out-of-Scope**: ADR changes (done); implementation of Repository Context, Episodic Memory, `/reload` changes, diagnostics, or the removal of `/memory` in code; the generated memory reference document and the memory and agent API manifests (derived from `scripts/agent/`, which this Plan does not change); other Agent documents that still describe the old model (configuration, state, platform databases, operations, system overview) and the DB, deployment, and security documents, which the follow-up issue adrdoc004 sweeps; the EventBus documents (adrdoc002, done); file renames, which the open issue cliplc014 owns.
- **Dependencies**: Depends on the ADR-006 and ADR-008 amendment (adrdoc001), which is complete and archived, so it needs no ordering bullet. Blocks the follow-up issue adrdoc004 (named by id). Compatible overlaps with the open issues cliplc005 (staged reload transaction; its documentation row is the hot-reload document), cliplc011 (command contracts), and cliplc014 (CLI documentation consolidation, Low priority, which should follow this Plan): this Plan changes the ADR-driven content, those issues change code behavior or consolidate structure, and neither is a precondition.

## Background
The Issue was filed from `memo-issue.md`. The amended ADR-008 (Decision Details 23 to 25, INV-20 to INV-22) is committed, and its Known Deviations cite SHARED-003 (the Agent code still implements the old Semantic/Episodic model, memory JSONL, and `/memory`) and SHARED-004 (lifecycle policies left undecided, including Episodic Memory retention and its Session DB schema-mismatch handling). Repository evidence checked on 2026-11-24:
- The eleven target documents exist under `docs/23_agent/`. They describe the old model: `agent_11_01` (semantic versus episodic memory, pinned entries, `/memory status` modes, JSONL persistence order, `/memory rebuild`), `agent_11_02` (`MemoryEntry` stored in JSONL and SQLite, a JSONL Format section), `agent_11_03` (`JsonlMemoryStore`, `import_from_jsonl()`, default `max_semantic`), `agent_07_10` (the whole Memory Category: status, list, delete, pin, unpin, prune, reindex, rebuild), `agent_07_03` (the `/memory` row of the command index), `agent_07_07` (Session and Memory Separation, `/undo` and `/clear` memory statements, `/session recover`, `/stats`, `/reload`), `agent_09_01` (Memory Table Ownership, JSONL archive, `/memory prune` retention), and `agent_07_01` (index entry "Slash commands: Memory and Other").
- Repository Context exists nowhere in code or configuration: no loader, no configuration key, no `/reload` snapshot, and none of the diagnostics. `scripts/agent/memory/` still holds `jsonl_store.py`, `pin_ops.py`, `write_ops.py`, `import_ops.py`, and `rebuild_ops.py`, and `command_defs_list.py` still registers `/memory`.
- `tools/check_docs_consistency.py --domain agent` runs `check_command_coverage`, an ERROR check that every command registered in `_COMMANDS` appears in the command index of `agent_07_03` and is mentioned in a chapter among `agent_07_07` to `agent_07_10`. `/memory` is still registered, so deleting it from the documents entirely would fail that check; `tests/docs/test_command_docs_sync.py` also asserts `/memory` is registered.
- The generated memory reference (`agent_11_04`) and the API manifests derive from `scripts/agent/memory/*.py` and `scripts/agent/*.py` (`tools/generate_reference_table.py`), so they follow the code and need no edit now.
- Memory documentation that is not in the Issue's list also describes the old model (`agent_08_03`, `agent_04_01` to `agent_04_03`, `agent_10_06`, `agent_01`, `agent_02`, `agent_08_01`, `agent_09_02`, `agent_12` to `agent_14`, plus DB, deployment, security, and overview documents).
- `tools/check_docs_consistency.py --domain agent` and the Needs Confirmation inventory check pass on the current tree (the `/db` warning in the generated subpackage reference is pre-existing).

## Problem
The Agent documentation presents Semantic and Episodic memories as sibling persistent types, user-facing memory operations, memory JSONL as an archive and rebuild source, `/memory` as part of the CLI contract, and no Repository Context. Session DB backup and recovery text does not say that Episodic Memory is restored with the whole Session DB while Repository Context is reloaded from source files, and `/stats`, `/context`, `/debug verbose`, and `/reload` do not own the diagnostic responsibilities previously held by `/memory`.

## Reason for Change
Updating only the memory overview would leave the CLI, Session DB, reload, context budgeting, and operations guidance inconsistent with each other and with ADR-008, and operators could keep relying on memory JSONL as a recovery source. The ADR amendment is complete, so this work can proceed now.

## Implementation Intent
Present two separated mechanisms. Repository Context: read from explicitly configured repository files (the source files stay authoritative), not stored in SQLite or JSONL, no persistent FTS or Vector index, reloaded atomically at startup or through `/reload`, selected sections injected only for the active turn. Episodic Memory: the only persistent long-term memory, generated internally from reusable work events rather than generic Q&A, stored in `session.sqlite` with derived indexes, with no user-facing add, list, search, pin, delete, prune, or rebuild, managed by internal retention, consistency, backup, and recovery. The documents state the contract and cite SHARED-003 or SHARED-004 wherever code or policy is missing; no `Needs Confirmation` marker is written, because unregistered markers fail the inventory check. `/memory` is documented as retired and not an alias, in a form the command-coverage check still accepts while the code registers it.

## Requirements
- `REQ-001`: Memory architecture documents remove Semantic Memory and User Semantic, the dual persistent model, `MemoryType` and `SourceType` explanations that imply it, Memory JSONL, JSONL import and rebuild, pin and unpin, manual writes, and user CRUD; define Episodic Memory as the only persistent Agent memory (stored in `session.sqlite`, indexes derived, recovered only from a verified SQLite backup); state that generic Q&A and Assistant-generated proposals are not persisted as durable rules; and state supported Episodic event categories only if their final names are confirmed (they are not, so none are named).
- `REQ-002`: The memory overview defines Repository Context as read-only context from explicitly configured repository files: not persisted, not backed up in the Session DB, not persistently indexed, reloaded atomically, injected per active turn, and mentions authority values such as `canonical` and `observed` only as undefined pending approval.
- `REQ-003`: CLI documents remove the Memory Category and the `/memory` contract from the reference, help, registry, examples, and completion text, and state that `/memory` is not retained as a compatibility alias; the registered command is described as retired and scheduled for removal (SHARED-003) so the command-coverage check keeps passing.
- `REQ-004`: `/reload` documents Repository Context reload with atomic behavior (all sources loaded into a candidate snapshot, the complete reload rejected on a validation failure, the active snapshot preserved, the new snapshot applied only to subsequent turns); `/stats` documents Repository Context and Episodic Memory aggregate state; `/context` documents Repository Context and Episodic Memory token usage beside the system prompt, conversation, tool schemas, and response reserve; `/debug verbose` documents source and section selection, exclusion, fallback, and budget diagnostics; and diagnostics expose aggregate state only, never individual Episodic contents, IDs, secrets, or personal information. Each is marked as not yet implemented (SHARED-003) and no field name is invented.
- `REQ-005`: Session DB backup and recovery text states that Episodic Memory is inside the Session DB backup and full recovery scope and that Repository Context is reloaded from configured files; removes JSONL-based memory recovery; states the ADR-008 schema-mismatch rule (archive and recreate with `/session export` first, Episodic Memory not carried over) and cites SHARED-004 for the undecided parts; clarifies `/session recover` for a full Session DB restore; and states that `/clear`, `/undo`, session deletion, and session purge give no user-level Episodic deletion semantics.
- `REQ-006`: Context-budget documentation covers final-payload budgeting across the system prompt, Repository Context, Episodic Memory, conversation history, tool schemas, current input, and response reserve; the reduction order (low-ranked Episodic Memory, then low-ranked Repository Context sections, then older conversation history); that mandatory canonical Repository Context is never silently removed; and that the failure behavior when mandatory input exceeds the limit is undefined (SHARED-004).
- `REQ-007`: The memory module reference retires the JSONL store, import, pin, manual-write, rebuild, and `/memory` command APIs (they exist in code only until SHARED-003 is resolved), renames the Memory Layer wording to Episodic Memory Layer where appropriate, and keeps the generated reference and manifests unchanged.
- `REQ-008`: The edited documents pass the Agent documentation checks, command-coverage and links stay valid, and no current target document describes Semantic Memory, memory JSONL as a backup or recovery source, or `/memory` operations as a supported contract.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Modify: chapter index entry for the memory-and-other chapter | Replace "Slash commands: Memory and Other" with a description that names the retired memory commands and the remaining Help command | REQ-003; AC-03 | Index line 39 names "Memory and Other" (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Modify: Built-in Command Index rows and notes | Change the `/memory` row to a retired entry, update the `/stats`, `/context`, `/reload`, `/debug` descriptions for the new diagnostics | REQ-003, REQ-004; AC-03, AC-04 | `/memory` row at line 58, `/stats` line 48, `/context` line 49, `/reload` line 52 (checked in Step 3) | `tests/docs/test_command_docs_sync.py`, `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Modify: Role of reload and Apply Atomicity | Document Repository Context reload as an atomic candidate snapshot | REQ-004; AC-04 | Apply Atomicity section covers configuration only (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Modify: `/clear`, `/undo`, `/session recover`, Session and Memory Separation, `/stats`, `/reload` | State the Episodic Memory scope of recovery and the absence of user-level Episodic deletion semantics; update `/stats` and `/reload` rows | REQ-004, REQ-005; AC-04, AC-05 | `/undo` memory statement at line 40, `/session recover` row at line 66, separation section lines 75 to 80, `/stats` and `/reload` rows at lines 97 and 98 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` | Modify: `/context` description and context budgeting | Add the token-usage components and the budget reduction order | REQ-004, REQ-006; AC-04, AC-06 | `/context` row at line 38 shows history size, budget, system prompt, and mode only (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Modify: `/debug verbose` row | Document the selection, exclusion, fallback, and budget diagnostics | REQ-004; AC-04 | `/debug verbose` row at line 41 only sets the log level (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` | Modify: Memory Category and Other Category | Remove the Memory Category contract; keep a short retired-command notice and the `/help` entry | REQ-003; AC-03 | Memory Category with eight subcommands and the JSONL rebuild text (checked in Step 3) | `tests/docs/test_command_docs_sync.py`, `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify: store inventory, Memory Table Ownership, retention, recovery | Replace the memory tables and JSONL archive with Episodic Memory in `session.sqlite`, and state the backup, recovery, and schema-mismatch scope | REQ-001, REQ-005; AC-01, AC-05 | Inventory row line 29, Memory Table Ownership lines 50 to 61, JSONL statement line 89, retention line 48 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Modify: title framing, Design Intent, Key Constraints, modes, persistence note, Operational Notes; add Repository Context and Context Budget sections | Replace the Semantic/Episodic model and JSONL persistence with the two-mechanism model; add Repository Context and the budget rules | REQ-001, REQ-002, REQ-006; AC-01, AC-02, AC-06 | Semantic versus episodic text, pinned entries, `on_session_stop` JSONL order, `/memory status` modes (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_11_02_memory-gate-data-model-search.md` | Modify: Data Model, JSONL Format, Operational Notes | Remove the JSONL storage and format sections and the semantic-only fields; keep the Episodic search strategies | REQ-001; AC-01 | `MemoryEntry (Stored in JSONL + SQLite)` heading at line 50 and `JSONL Format` heading at line 66 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |
| `docs/23_agent/agent_11_03_memory-module-reference.md` | Modify: module descriptions for the JSONL store, import, rebuild, pin, and write operations; Default `InjectionPolicy` | Retire those modules and the semantic fields from the module reference, naming them only as removal-pending | REQ-007; AC-07 | `JsonlMemoryStore` at line 62, `import_from_jsonl()` at line 92, default `InjectionPolicy` at line 56 (checked in Step 3) | `tools/check_docs_consistency.py --domain agent` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Amended source of the memory model, retention, schema-mismatch, and recovery decisions (Decision Details 22 to 25, INV-20 to INV-22) | REQ-001 to REQ-007 |
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Known Issues SHARED-003 and SHARED-004 that the documents cite | REQ-002 to REQ-007 |
| `docs/23_agent/agent_11_04_memory-module-reference-generated.md` | Generated memory reference; follows the code and stays unchanged | REQ-007 |
| `docs/23_agent/agent_07_02_cli-and-commands-cliview.md` | CLI view chapter; no memory-specific change needed | REQ-003 |
| `docs/23_agent/agent_08_03_configuration-tools-memory.md` | Existing memory configuration keys, to avoid contradicting existing keys | REQ-001, REQ-002 |
| `docs/23_agent/agent_04_01_state-and-persistence-state-model.md` | Session and memory boundary statement cited by the memory overview | REQ-001, REQ-005 |
| `scripts/agent/commands/command_defs_list.py` | `/memory` and the other commands are registered here | REQ-003 |
| `scripts/agent/memory/__init__.py` | Public memory API surface, for the retirement notes | REQ-007 |
| `scripts/agent/memory/jsonl_store.py` | The JSONL store the module reference retires | REQ-007 |
| `scripts/agent/memory/import_ops.py` | The JSONL import the module reference retires | REQ-007 |
| `scripts/agent/memory/rebuild_ops.py` | The JSONL rebuild the module reference retires | REQ-007 |
| `scripts/agent/memory/pin_ops.py` | The pin operations the module reference retires | REQ-007 |
| `scripts/agent/memory/write_ops.py` | The manual write operations the module reference retires | REQ-007 |
| `scripts/agent/services/config_reload.py` | Current reload behavior, for the Repository Context reload statement | REQ-004 |
| `tests/docs/test_command_docs_sync.py` | Asserts `/memory` is registered and checks documented command references | REQ-003 |
| `tools/check_docs_consistency.py` | `check_command_coverage` rule that fixes how `/memory` must stay documented | REQ-003, REQ-008 |
| `tools/generate_reference_table.py` | Shows the memory and agent manifests are derived from code | REQ-007 |

## Acceptance Criteria
- `AC-01` (REQ-001): no current target document describes the Semantic/Episodic dual persistent model, Semantic Memory, User Semantic, memory JSONL as a backup or recovery source, pin or unpin, manual memory writes, or user CRUD; Episodic Memory is defined as the only persistent Agent memory in `session.sqlite`.
- `AC-02` (REQ-002): Repository Context has its own source-of-truth, storage, reload, retrieval, and recovery description, separate from Episodic Memory.
- `AC-03` (REQ-003): `/memory` operations are absent from the CLI contract; `/memory` is stated as retired, not an alias, with SHARED-003 cited; the command-coverage check still passes.
- `AC-04` (REQ-004): `/reload`, `/stats`, `/context`, and `/debug verbose` responsibilities are stated consistently across the documents, diagnostics expose aggregate state only, and each unimplemented behavior cites SHARED-003.
- `AC-05` (REQ-005): the Session DB documents state the backup, recovery, schema-mismatch, and `/session recover` scope, and that `/clear`, `/undo`, session deletion, and session purge give no user-level Episodic deletion semantics.
- `AC-06` (REQ-006): the context-budget order, the never-silently-removed rule for mandatory Repository Context, and the undefined overflow failure behavior (SHARED-004) are documented.
- `AC-07` (REQ-007, REQ-008): the module reference retires the JSONL, import, pin, manual-write, rebuild, and `/memory` APIs; the Agent documentation checks, link checks, and Needs Confirmation inventory check pass; the generated reference and manifests are unchanged.

## Tests
- `REQ-001` to `REQ-008`: documentation-only, so no automated test is added. Evidence is the checker set in the Validation plan, `tests/docs/test_command_docs_sync.py` still passing unchanged, and the generated reference and manifests showing no drift.
- `REQ-003`: `uv run python tools/check_docs_consistency.py --domain agent` (including `check_command_coverage`) passes, which confirms `/memory` stays in the index and a chapter.

## Documentation Impact
Yes. The eleven target documents under `docs/23_agent/` are the documentation, reached through `docs/00_index.md` ("Agent" area). They record intent, boundaries, constraints, failure behavior, and Known Issue citations (SHARED-003, SHARED-004) for each point the code or policy does not yet meet. The other Agent documents that still describe the old model are updated by the follow-up issue adrdoc004.

## Assumptions
- The documents state the target contract from the amended ADR-008 and cite SHARED-003 (code and CLI still match the old model; Repository Context, its diagnostics, and its reload are not implemented) or SHARED-004 (lifecycle policies undecided) wherever current code or policy differs; they do not claim the behavior exists.
- No `Needs Confirmation` marker is added to any document, because each marker needs an inventory entry and this Plan does not edit the inventory; an undefined name, key, field, or policy is expressed by a Known Issue citation.
- `/memory` stays in the command index and in one chapter only as a retired entry, because `check_command_coverage` (an ERROR check) and `tests/docs/test_command_docs_sync.py` require every registered command to be documented while the code still registers it; removing the registration is an implementation issue.
- `agent_11_04`, the memory and agent API manifests, and the generated Agent reference documents follow the code and are not edited; removing JSONL symbols from them waits for the code change.
- Retrieval strategies (FTS5, KNN, hybrid RRF) and the embedding modes are kept in the memory documents as Episodic Memory retrieval, because ADR-008 keeps Episodic FTS and Vector indexes as derived data; semantic-only constraints (importance threshold, pin limit) are removed.
- SHARED-003 covers the missing Repository Context loader and diagnostics by citation; this Plan does not edit the governance document, which sits exactly at its size ceiling.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How `/memory` should appear in the CLI documents while the code still registers it | The Issue says to remove it entirely; `check_command_coverage` and the sync test require a registered command to be documented | Document it as a retired entry that is not an alias and cite SHARED-003; if the maintainer wants it fully absent, the code removal comes first or the checker is changed under a separate issue | False |
| UNK-02 | Repository Context configuration keys, the list of source files, and authority values (`canonical`, `observed`) | No Repository Context code, configuration, or approved design exists in the repository | The documents define the behavior and state keys and authority values as undefined (SHARED-003) | False |
| UNK-03 | Final names of the supported Episodic event categories | Not confirmed in the approved design | The documents name no category and cite SHARED-004 | False |
| UNK-04 | Names and formats of the `/stats`, `/context`, and `/debug verbose` diagnostic fields | None of the diagnostics exists in the commands | The documents describe the aggregate content and the privacy rule without field names (SHARED-003) | False |
| UNK-05 | Failure behavior when mandatory input exceeds the context limit, and Episodic retention and Session DB schema-mismatch handling for Episodic Memory | ADR-008 records these as undecided | The documents state the no-silent-removal rule and cite SHARED-004 for the rest | False |
| UNK-06 | Sequencing with the open issues cliplc005, cliplc011, and cliplc014, which also change the reload, command, and CLI documents | Those issues are open and not yet planned against these documents | Compatible overlap: this Plan lands first, and those issues re-verify the affected documents (cliplc014 follows this Plan) | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Modify | Low | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Modify | High (checked by `check_command_coverage` and the sync test) | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Modify | Medium (also targeted by the open issue cliplc005) | 1 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Modify | Medium | 3 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` | Modify | Low | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Modify | Low | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` | Modify | High (checked by `check_command_coverage` and the sync test) | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_09_01_data-layer-session-db.md` | Modify | Medium | 6 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Modify | Medium (cited as the canonical session and memory boundary) | 2 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_11_02_memory-gate-data-model-search.md` | Modify | Low | 0 | 2 authors in 365 days | not applicable (rsynced) |
| `docs/23_agent/agent_11_03_memory-module-reference.md` | Modify | Medium | 0 | 2 authors in 365 days | not applicable (rsynced) |

## Design
Classification: Path B (eleven target rows, more than three).

Analysis (documentation only; no Python target, so the radon, vulture, and bandit baseline is `N/A: no Python target`):
- Coupling: `tools/check_docs_consistency.py --domain agent` checks links, `scripts/` path references, backticked function references, and command coverage (`check_command_coverage`: every registered command is in the `agent_07_03` index and in a chapter among `agent_07_07` to `agent_07_10`). `/memory` is still registered, so the CLI documents keep one retired entry for it; all other memory-command text is removed.
- Module reference: `agent_11_03` describes existing modules. Removing their API descriptions leaves the modules undocumented while they remain in code, so the document keeps their names in one "Retired by ADR-008" list, without API descriptions, until the code removal.
- Content policy: `tools/check_docs_content_policy.py` and `skills/DESIGN.md` "Avoid implementation-reference duplication" apply; the documents cite the ADR and the Known Issue instead of restating code.
- Consumer scan and predictable fallout check: no persisted schema, public API, shared constant, or code symbol changes, so `tools/scan_change_consumers.py` is not applicable. Pinned counts: no test asserts a documentation count (`tests/docs/test_command_docs_sync.py` asserts command names only); tool inventory and module size: `not affected`; generated blocks: `agent_11_04` and the Agent reference documents follow the code and stay unchanged; size ceilings of `tools/check_docs_structure.py` (default 32768 bytes): the largest target (`agent_07_07`, 9231 bytes) stays far below it, `not affected`. Documents with old-model text outside this Plan (see Background) are `not affected` here and handled by adrdoc004.
- Operational check: no process or database is touched (not run, documentation only). Persisted schema check (`rules/persisted-schema-change.md`): not applicable, no DDL or migration changes.

Decisions:
- Repository Context gets a section inside `agent_11_01` instead of a new file, because a new chapter would also need the document guide, `docs/00_index.md`, and front matter updates that are outside this Plan.
- Document file names stay unchanged (renames belong to cliplc014); titles and descriptions are updated instead.
- The Session DB recovery statement is written once in `agent_09_01` and linked from the CLI documents.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above. All steps edit documentation text only.

1. **Phase 1: Memory architecture and Session DB**
   - [ ] Rewrite the memory overview for the two-mechanism model and add the Repository Context and Context Budget sections (REQ-001, REQ-002, REQ-006; `docs/23_agent/agent_11_01_memory-overview-and-modes.md`)
   - [ ] Remove the JSONL storage and format and the semantic-only data-model content (REQ-001; `docs/23_agent/agent_11_02_memory-gate-data-model-search.md`)
   - [ ] Replace the memory tables and JSONL archive with Episodic Memory and state the backup, recovery, and schema-mismatch scope (REQ-001, REQ-005; `docs/23_agent/agent_09_01_data-layer-session-db.md`)
   - [ ] Retire the JSONL, import, rebuild, pin, and write modules in the module reference (REQ-007; `docs/23_agent/agent_11_03_memory-module-reference.md`)
2. **Phase 2: CLI commands**
   - [ ] Remove the Memory Category contract and keep the retired notice and `/help` (REQ-003; `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`)
   - [ ] Update the command index and the CLI chapter index (REQ-003, REQ-004; `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`)
3. **Phase 3: Reload, diagnostics, and recovery commands**
   - [ ] Document the atomic Repository Context reload (REQ-004; `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`)
   - [ ] Update `/stats`, `/reload`, `/session recover`, and the session and memory separation (REQ-004, REQ-005; `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`)
   - [ ] Update `/context` token usage and budgeting (REQ-004, REQ-006; `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`)
   - [ ] Update `/debug verbose` diagnostics (REQ-004; `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`)
4. **Phase 4: Validation**
   - [ ] Run the checkers in the Validation plan and confirm the generated reference and manifests are unchanged (REQ-008; all target files)

### Release units
**Unit**: agent-memory-docs | **Phases**: 1, 2, 3 | **Reason**: the documents cross-link, and `check_docs_consistency.py --domain agent` validates links, references, and command coverage across them, so retiring a section in one document while another still links to it, or changing the command index before the chapter, fails the check; the phases land together.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All eleven target documents | Cross-document consistency, links, references, command coverage | `uv run python tools/check_docs_consistency.py --domain agent` | No new findings (the pre-existing `/db` warning is unchanged) |
| All eleven target documents | Structure, quality, content policy, metadata | `uv run python tools/check_docs_structure.py`, `tools/check_docs_quality.py`, `tools/check_docs_content_policy.py`, `tools/check_metadata_field_policy.py` | No findings |
| All eleven target documents | Known Issue and Needs Confirmation citations | `uv run python tools/check_known_deviation_sync.py`, `tools/check_needs_confirmation_inventory.py` | No findings |
| `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `agent_07_10_cli-and-commands-slash-commands-memory-other.md` | Documented commands match the registry | `uv run pytest tests/docs/test_command_docs_sync.py -q` | Pass |
| All eleven target documents | Preservation of unrelated content | `uv run python tools/check_adr_preservation.py --dir docs/23_agent` | Only intended findings, reported |
| `docs/23_agent/agent_11_03_memory-module-reference.md` and generated documents | Generated blocks and manifests unchanged | `uv run python tools/generate_reference_table.py --check` | No drift |
| All eleven target documents | Gate runner for the changed files | `uv run python tools/run_validation_gates.py` | No `Fail` or `Blocked` |

## Risks
- **Risk**: The documents describe Repository Context, Episodic-only memory, and new diagnostics that the code does not implement, so a reader may take them as current behavior → **Mitigation**: each such statement cites SHARED-003 or SHARED-004, and no field, key, category, or policy is invented.
- **Risk**: Removing `/memory` entirely fails `check_command_coverage` or `tests/docs/test_command_docs_sync.py` while the code registers it → **Mitigation**: keep one retired entry in the index and one chapter, run `check_docs_consistency.py --domain agent` before commit, and leave the code removal to an implementation issue.
- **Risk**: Other Agent, DB, deployment, and security documents still describe the old model until adrdoc004 lands, so documents disagree for a period → **Mitigation**: adrdoc004 depends on this Plan; the Background lists the affected documents.
- **Risk**: The module reference loses documentation of modules that still exist in code → **Mitigation**: keep their names in a "Retired by ADR-008" list that points to SHARED-003.
- **Risk**: Overlap with cliplc005, cliplc011, and cliplc014 on the reload and command documents → **Mitigation**: UNK-06; sequencing is recorded, and those issues re-verify the documents after this Plan.
- **Risk**: A `Needs Confirmation` marker added without an inventory entry fails `check_needs_confirmation_inventory.py` → **Mitigation**: no such marker is written; Known Issue citations are used.
- **Risk**: A removed heading breaks an anchor link from another document (for example the canonical session and memory boundary cited from `agent_00`) → **Mitigation**: keep linked headings or update the links in the same edit set; the consistency check runs before commit.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Memory architecture, Session DB, and module reference | Completed | — | 20261124-104112 |  |
| 2 | CLI commands: Memory Category retirement, command index, chapter index | Completed | — | 20261124-104112 |  |
| 3 | Reload, diagnostics, context budget, and recovery commands | Completed | — | 20261124-104112 |  |
| 4 | Validation checks and unchanged generated-reference confirmation | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261124-103504_01_docs_23_agent_agent_07_01_cli-and-commands-cli-reference.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-103504_02_docs_23_agent_agent_07_03_cli-and-commands-command-registry.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-103504_03_docs_23_agent_agent_07_06_cli-and-commands-hot-reload.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-103504_04_docs_23_agent_agent_07_07_cli-and-commands-slash-commands-session-mcp.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-103504_05_docs_23_agent_agent_07_08_cli-and-commands-slash-commands-context-plan.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-103504_06_docs_23_agent_agent_07_09_cli-and-commands-slash-commands-workflow-debug.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261124-103504_07_docs_23_agent_agent_07_10_cli-and-commands-slash-commands-memory-other.md.md | 2 | Procedure | Completed | — | — |
| implementations/20261124-103504_08_docs_23_agent_agent_09_01_data-layer-session-db.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-103504_09_docs_23_agent_agent_11_01_memory-overview-and-modes.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-103504_10_docs_23_agent_agent_11_02_memory-gate-data-model-search.md.md | 1 | Procedure | Completed | — | — |
| implementations/20261124-103504_11_docs_23_agent_agent_11_03_memory-module-reference.md.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261124-103155
- **Related target files**: `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md`, `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`, `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`, `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`, `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md`, `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md`, `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`, `docs/23_agent/agent_09_01_data-layer-session-db.md`, `docs/23_agent/agent_11_01_memory-overview-and-modes.md`, `docs/23_agent/agent_11_02_memory-gate-data-model-search.md`, `docs/23_agent/agent_11_03_memory-module-reference.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes A; agent_11_01 and agent_11_02 old-model text | `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-03) |
| REQ-001 | Required Changes A; agent_11_02 lines 50 and 66 | `docs/23_agent/agent_11_02_memory-gate-data-model-search.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-001 | Required Changes A; agent_09_01 lines 50 to 61 | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Phase 1 | AC-01 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-002 | Required Changes A; no Repository Context in code | `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Phase 1 | AC-02 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-02) |
| REQ-003 | Required Changes B; `/memory` registered in command_defs_list.py | `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md` | Phase 2 | AC-03 | `test_command_docs_sync.py` | Needs confirmation (UNK-01) |
| REQ-003 | Required Changes B; index row at line 58 | `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-01) |
| REQ-003 | Required Changes B; index line 39 | `docs/23_agent/agent_07_01_cli-and-commands-cli-reference.md` | Phase 2 | AC-03 | `check_docs_consistency.py --domain agent` | Confirmed by repository evidence |
| REQ-004 | Required Changes B; reload and atomicity text | `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-02) |
| REQ-004 | Required Changes B; `/stats` and `/reload` rows | `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-04) |
| REQ-004 | Required Changes B; `/context` row | `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-04) |
| REQ-004 | Required Changes B; `/debug verbose` row | `docs/23_agent/agent_07_09_cli-and-commands-slash-commands-workflow-debug.md` | Phase 3 | AC-04 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-04) |
| REQ-004 | Required Changes B; command registry rows | `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | Phase 2 | AC-04 | `check_docs_consistency.py --domain agent` | Derived from confirmed evidence |
| REQ-005 | Required Changes C; `/session recover` and separation text | `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | Phase 3 | AC-05 | `check_docs_consistency.py --domain agent` | Derived from confirmed evidence |
| REQ-005 | Required Changes C; Session DB retention and recovery | `docs/23_agent/agent_09_01_data-layer-session-db.md` | Phase 1 | AC-05 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-05) |
| REQ-006 | Required Changes D | `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Phase 1 | AC-06 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-05) |
| REQ-006 | Required Changes D | `docs/23_agent/agent_07_08_cli-and-commands-slash-commands-context-plan.md` | Phase 3 | AC-06 | `check_docs_consistency.py --domain agent` | Needs confirmation (UNK-05) |
| REQ-007 | Required Changes E; agent_11_03 lines 56 to 93 | `docs/23_agent/agent_11_03_memory-module-reference.md` | Phase 1 | AC-07 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-008 | Required validation; Acceptance Criteria | `docs/23_agent/agent_11_01_memory-overview-and-modes.md` | Phase 4 | AC-07 | Validation plan checkers | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261124-103504 -->
