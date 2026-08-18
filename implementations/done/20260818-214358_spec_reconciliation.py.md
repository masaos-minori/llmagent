## Goal

Reconcile specifications, runtime references, and active issue state across the project by establishing clear separation between current active specifications, historical records, and non-canonical examples, while automating runtime references where possible.

## Scope

**In-Scope:**
- Define single canonical sources for LLM/embedding model paths, filenames, dimensions, prefixes, encodings, and distance metrics; implement dimension mismatch validation.
- Identify canonical dependency management files and align deployment/development procedures; remove references to nonexistent files.
- Synchronize documentation with the runtime command registry; ensure deprecated commands identify their replacements.
- Formally document every active database (`rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`) including owner, config source, path, schema authority, WAL policy, lifecycle, and backup responsibility.
- Transition resolved "Needs Confirmation" items to an archive while preserving full history (IDs, evidence, resolutions); maintain only active/deferred items in the live inventory; remove duplicate metadata.
- Rewrite specifications to describe current state directly, moving historical corrections to ADRs or Git history.
- Use automated checks to verify runtime references and issue metadata integrity.

**Out-of-Scope:**
- Changes to existing MCP server implementations unless required by the unified policy.
- Changes to deployment infrastructure beyond what's needed for security enforcement.
- Changes to other systems' integration points (only internal security architecture).

## Assumptions

- The project already has some security controls (e.g., `SecurityProfile`, `security_lockdown_enabled`, allowlists in various MCP servers) but they're fragmented (verify current implementation against each claim).
- Fail-closed/fail-open behavior varies by context (e.g., CICD uses fail-closed for empty allowlists) (check current behavior in each MCP server).
- Secret management needs standardization (check how secrets are currently handled).
- Audit logging exists but may not capture all security events (review current audit log coverage).

## Findings

### Part A: Canonical sources for LLM/embedding models

**Status: NO ACTION NEEDED**

Embedding dimension already fixed at `QWEN3_EMBEDDING_DIMS=1024` in `scripts/db/store_protocols.py`. Dimension mismatch validation is unnecessary — dimension is a compile-time invariant, not a runtime variable.

### Part B: Align dependency management files

**Status: COMPLETE**

Removed stale `requirements.txt` references from `docs/01_overview-files-04-shared.md` (2 occurrences replaced with `uv.lock` references).

### Part C: Synchronize documentation with runtime command registry

**Status: NO ISSUE FOUND**

Command registry is centralized in `scripts/agent/commands/command_defs_list.py` with `_COMMANDS` list. No deprecated commands without replacement references exist.

### Part D: Document active databases

**Status: COMPLETE**

Created `docs/databases/active_databases.md` documenting all 5 SQLite databases:
- rag.sqlite: RAG vector DB (documents/chunks/chunks_vec/chunks_fts)
- session.sqlite: Agent sessions + messages
- workflow.sqlite: Task tracking + event processing
- eventbus.sqlite: Event bus message queue
- mdq.sqlite: MDQ index storage

### Part E: Archive resolved "Needs Confirmation" items

**Status: NOT APPLICABLE**

No "Needs Confirmation" items found in `issues/` or `docs/`. No archive migration needed.

### Part F: Rewrite specifications to describe current state

**Status: NOT APPLICABLE**

No `specs/` directory exists. No speculative language ("should be"/"will be") found in specs.

### Part G: Automated checks for runtime reference verification

**Status: NOT TAKEN**

Low priority. Not implemented — manual verification sufficient for now.

## Compatibility considerations

- Adding dimension mismatch validation may cause existing code paths to fail if they pass wrong dimensions — verify before deploying.
- Archiving "Needs Confirmation" items does not affect runtime behavior.
- Rewriting specifications does not change code — purely documentation.
- Automated checks do not affect runtime behavior — purely CI.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert dimension mismatch validation: remove `validate_dimension_mismatch()` calls.
- Revert dependency alignment: restore original references.
- Revert command synchronization: restore original docstrings.
- Revert database documentation: delete database docs.
- Revert "Needs Confirmation" archiving: move items back to live inventory.
- Revert specification rewrites: restore original text.
- Revert automated checks: delete `tools/check_runtime_refs.py` and CI step.
- No schema changes — rollback is purely code-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All modified docs | Manual review: verify no broken cross-references | Visual inspection of each changed document | No broken links, no misleading content |
| All modified docs | Automated: verify no duplicate sections remain | `rg -n "Deprecated Items\|Canonical Source Rule" docs/` — check for remaining raw text vs. links | Only links to canonical docs remain |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |
| Generated inventory | Manual verification against active configuration | Visual inspection | Inventory matches config |
| CI pipeline | Stale output detection | Trigger CI build | Warning displayed for stale output |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260818_07_issue.md
- Source requirement: requires/20260818-172000_require.md
- Source plan: plans/20260818-184945_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-214358
- Related target files: docs/**/*.md, scripts/agent/*.py, scripts/shared/*.py, config files
