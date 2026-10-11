---
title: "Issue and Uncertainty Management"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - overview_00_document-guide.md
---

# Issue and Uncertainty Management

## Purpose

This document defines how to track currently active discrepancies between documentation and implementation (Known Issues) and currently active unverified claims, tracked as Needs Confirmation items. It ensures unconfirmed statements are trackable and actionable, preventing them from being silently accepted as facts.

## Part 1: Known Issues

### Entry Template

Each active Known Issue entry must contain these 17 fields: ID, Title, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Summary, Current Description, Observed Implementation, Impact, Recommended Action, Resolution Target.

### Status Values

- **open** — Issue acknowledged but not yet investigated
- **investigating** — Investigation underway
- **deferred** — Resolution postponed to future work

An item is removed from this active inventory once it is resolved or no longer
applies to the current system; it is not retained here with a closed-out status.

### Type Values

document-code-mismatch, document-document-mismatch, obsolete-description, missing-documentation, ambiguous-behavior, implementation-bug (code does not match documented intent), design-gap, operational-gap.

### Severity Values

High (safety or critical functionality; immediate attention), Medium (correctness or clarity; address soon), Low (minor inconsistency; can be deferred).

### Owner Values

Unassigned, a specific person (`[Name]`), or Team.

### First Found and Related Values

`First Found` names the activity that surfaced the issue (for example, a documentation review); it is not a date. `Related` is `None` or a comma-separated list of Known Issue IDs and repository-relative document paths.

### Area Values

Overview, Deployment, RAG, MCP, Agent, EventBus, Shared/DB, Governance

### Review Cadence

Part 1 entries are reviewed quarterly, as are Part 2 items and "Proposed" ADRs (`governance_01_documentation-policy.md`, Maintenance Rules).

### Active Items

Active Items follow an ordering convention: entries are grouped by ID-prefix (RAG-*, DESIGN-*, AGENT-*, MCP-*, DEPLOY-*, EVENTBUS-*, SHARED-*, CI-*), each group's entries in ascending numeric order.

| ID | Title | Status | Severity | Area | Type |
|----|-------|--------|----------|------|------|
| RAG-002 | Japanese sentences with empty normalized text are dropped with their original text | open | Low | RAG | implementation-bug |
| RAG-006 | Refiner settings in config/agent.toml are validated but never read by the Agent | open | Low | RAG | design-gap |
| RAG-007 | chunks_vec has no foreign key to chunks | open | Low | RAG | design-gap |
| AGENT-002 | No regression test for ADR-014 INV-02 | open | Low | Agent | operational-gap |
| AGENT-004 | A non-required subprocess MCP server aborts startup when it fails to spawn | open | Medium | Agent | design-gap |
| AGENT-005 | Approval and audit operation-type classification reads static tool-name sets before RuntimeToolRegistry | open | Medium | Agent | design-gap |
| AGENT-006 | Secret masking of MCP subprocess output recognizes only key=value forms | open | Medium | Agent | design-gap |
| AGENT-007 | A diagnostic row that fails to decrypt is returned as ciphertext with only a warning | open | Low | Agent | design-gap |
| AGENT-008 | /undo after a compressed session reload can undo fewer turns than expected | open | Low | Agent | design-gap |
| AGENT-009 | /skill messages lose the _ephemeral marker during append validation | open | Low | Agent | design-gap |
| DEPLOY-001 | LLM service start procedure is not provided by any repository script | open | Medium | Deployment | operational-gap |
| DEPLOY-002 | Production uv run does not exclude the dev dependency group | open | Medium | Deployment | operational-gap |
| EVENTBUS-008 | Consumer-role token without a consumer_id allowlist skips consumer-identity validation | open | Medium | EventBus | design-gap |
| EVENTBUS-015 | Shared auth_token and admin_token grant every role | open | Medium | EventBus | design-gap |
| EVENTBUS-016 | Two EventBus DDL sources define slightly different schemas | open | Low | EventBus | design-gap |
| SHARED-001 | shared/security package has no importers | open | Low | Shared/DB | design-gap |

#### RAG-002

- **ID**: RAG-002
- **Title**: Japanese sentences with empty normalized text are dropped with their original text
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: implementation-bug
- **Source**: `scripts/rag/ingestion/chunk_japanese.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-009-rag-fts5-text-separation.md`
- **Related**: None
- **Summary**: Sentences that normalize to nothing are dropped, so `content` is lost for them.
- **Current Description**: ADR-009 INV-11 says a sentence whose normalized text is empty keeps its original text in `content`.
- **Observed Implementation**: `_split_into_ja_sentences()` drops a pair whose normalized text is empty, together with the original sentence.
- **Impact**: Original text of such sentences is missing from the index.
- **Recommended Action**: Keep the original sentence in `content` when normalization is empty.
- **Resolution Target**: `content` keeps every original sentence, covered by a test.

#### RAG-006

- **ID**: RAG-006
- **Title**: Refiner settings in config/agent.toml are validated but never read by the Agent
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/agent/config_builders.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/21_rag/rag_05_01-configuration-reference.md`
- **Related**: `docs/10_adr/ADR-010-rag-fallback.md`
- **Summary**: `use_refiner` and the `refiner_*` keys in `config/agent.toml` are not read by any Agent code path.
- **Current Description**: The keys appear as Agent RAG settings.
- **Observed Implementation**: Only `embed_url` is read from `AgentConfig.rag`; the rag-pipeline MCP server uses `config/rag_pipeline_mcp_server.toml`.
- **Impact**: Editing these keys has no effect on refiner behavior.
- **Recommended Action**: Remove the unused keys from `config/agent.toml` and `RAGConfig`, or wire them to a consumer.
- **Resolution Target**: Every refiner key in `config/agent.toml` has a consumer, or the keys are removed.

#### RAG-007

- **ID**: RAG-007
- **Title**: chunks_vec has no foreign key to chunks
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: design-gap
- **Source**: `scripts/db/schema_sql.py`
- **Owner**: Unassigned
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/ADR-005-rag-source-derived-index-relationships.md`
- **Related**: None
- **Summary**: The `sqlite-vec` virtual table `chunks_vec` cannot declare a foreign key to `chunks`.
- **Current Description**: ADR-005 requires derived index rows to follow their source rows.
- **Observed Implementation**: Orphaned vector rows can exist after document deletion if the explicit `chunks_vec` deletion step is skipped; all deletion paths perform it.
- **Impact**: A deletion path that omits the explicit step leaves orphaned vector rows.
- **Recommended Action**: Keep the ordering invariant tested, and revisit when `sqlite-vec` supports foreign keys.
- **Resolution Target**: `sqlite-vec` supports foreign keys, or the limitation is recorded as accepted.

#### AGENT-002

- **ID**: AGENT-002
- **Title**: No regression test for ADR-014 INV-02
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: operational-gap
- **Source**: `scripts/agent/orchestrator.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-014-agent-control-plane-responsibility-boundaries.md`
- **Related**: None
- **Summary**: ADR-014 INV-02 (only the component that drives the LLM/tool-call loop creates `LlmTurnExecutor`) has no automated test.
- **Current Description**: ADR-014 lists the test as not yet written.
- **Observed Implementation**: `Orchestrator.__init__` creates only `_llm_executor` and passes it to the workflow adapter; no test asserts this.
- **Impact**: A regression could go unnoticed.
- **Recommended Action**: Add a unit test that `Orchestrator` constructs exactly one `LlmTurnExecutor`.
- **Resolution Target**: A test covers ADR-014 INV-02.

#### AGENT-004

- **ID**: AGENT-004
- **Title**: A non-required subprocess MCP server aborts startup when it fails to spawn
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/startup_mcp_starter.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-004-environment-failure-handling-policy.md`
- **Related**: None
- **Summary**: The spawn path never reads `required`, so `required=false` does not disable the server.
- **Current Description**: ADR-004 disables a non-mandatory component and continues startup.
- **Observed Implementation**: `McpServerStarter` retries once and raises a fatal error; `required` is applied only during discovery.
- **Impact**: A non-required server can still block startup.
- **Recommended Action**: Apply `required` to spawn failures, or record the exception in ADR-004.
- **Resolution Target**: Spawn failures follow `required`, or ADR-004 records the exception.

#### AGENT-005

- **ID**: AGENT-005
- **Title**: Approval and audit operation-type classification reads static tool-name sets before RuntimeToolRegistry
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/tool_policy.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-003-runtime-tool-registry-routing-authority.md`
- **Related**: `docs/22_mcp/mcp_03_01_dispatch-and-routing.md`
- **Summary**: `classify_operation_type()` reads the frozensets in `shared/tool_constants.py` first and uses `RuntimeToolRegistry` only for READ versus UNKNOWN.
- **Current Description**: ADR-003 INV-03 requires approval and auditing to reference the same `RuntimeTool` attributes as routing.
- **Observed Implementation**: The operation type does not read the `RuntimeTool` write attribute.
- **Impact**: A tool name missing from the static sets and registered as a write tool in `RuntimeToolRegistry` is classified READ for approval and audit.
- **Recommended Action**: Derive the operation type from `RuntimeTool`, or record the static-set classification as an accepted exception in ADR-003.
- **Resolution Target**: Approval and audit classification reference `RuntimeTool`, or ADR-003 records the exception.

#### AGENT-006

- **ID**: AGENT-006
- **Title**: Secret masking of MCP subprocess output recognizes only key=value forms
- **Status**: open
- **Severity**: Medium
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/secrets_masker.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
- **Related**: None
- **Summary**: Masking of MCP subprocess output matches only `key=value` forms.
- **Current Description**: Documented only as a chapter-level limitation in agent_10_01.
- **Observed Implementation**: `_mask_secrets()` matches `password`, `api_key`, `secret` and `token` as `key=value`; a Bearer header is not masked.
- **Impact**: Other secret shapes can reach logs and reports.
- **Recommended Action**: Extend the patterns or reuse the shared redaction registry.
- **Resolution Target**: Registered secrets in subprocess output are masked, tested.

#### AGENT-007

- **ID**: AGENT-007
- **Title**: A diagnostic row that fails to decrypt is returned as ciphertext with only a warning
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/diagnostic_store.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_09_01_data-layer-session-db.md`
- **Related**: None
- **Summary**: A failed decryption leaves the ciphertext in the returned row.
- **Current Description**: Documented only as a chapter-level limitation in agent_09_01.
- **Observed Implementation**: The loader logs a warning and keeps the Fernet token in `content`.
- **Impact**: A wrong or rotated key is not surfaced to the caller.
- **Recommended Action**: Mark the row undecryptable or raise, or record it as accepted.
- **Resolution Target**: A decryption failure is visible to the caller, or the tolerance is recorded.

#### AGENT-008

- **ID**: AGENT-008
- **Title**: /undo after a compressed session reload can undo fewer turns than expected
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/services/undo_service.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_04_02_state-and-persistence-history-compression.md`
- **Related**: None
- **Summary**: Compression replaces original messages with a summary, so fewer turns are undoable.
- **Current Description**: Documented only as a chapter-level limitation in agent_04_02.
- **Observed Implementation**: `undo_last_turn()` removes the last turn from history and DB rows and only warns when it removes a summary.
- **Impact**: Original messages cannot be recovered after compression.
- **Recommended Action**: Keep originals recoverable, or record the limitation as accepted.
- **Resolution Target**: The undo range after compression is defined and tested.

#### AGENT-009

- **ID**: AGENT-009
- **Title**: /skill messages lose the _ephemeral marker during append validation
- **Status**: open
- **Severity**: Low
- **Area**: Agent
- **Type**: design-gap
- **Source**: `scripts/agent/commands/cmd_skill.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/23_agent/agent_07_10_cli-and-commands-slash-commands-memory-other.md`
- **Related**: None
- **Summary**: The `/skill` message carries `_ephemeral` and `_skill_ephemeral`, but only `_skill_ephemeral` survives history validation.
- **Current Description**: Documented only as a chapter-level Known Limitation in the CLI skill-command chapter.
- **Observed Implementation**: `TRUSTED_SOURCES["skill_mixin"]` authorizes only `_skill_ephemeral`, so `append_message()` removes `_ephemeral` with a warning log.
- **Impact**: The orchestrator's generic `_ephemeral` pre-turn clearing does not remove injected skill messages at the start of the next turn.
- **Recommended Action**: Authorize `_ephemeral` for the skill source, or make the pre-turn clearing also handle `_skill_ephemeral`, or record the behavior as accepted.
- **Resolution Target**: Skill messages are cleared by one defined mechanism, with a test.

#### DEPLOY-001

- **ID**: DEPLOY-001
- **Title**: LLM service start procedure is not provided by any repository script
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/setup_services.sh`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/90_deployment/deployment_01_deployment.md`
- **Related**: None
- **Summary**: No repository script, unit file or configuration starts `embed-llm` and `agent-llm`.
- **Current Description**: The deployment document gives no start procedure for the LLM services.
- **Observed Implementation**: `setup_services.sh` only echoes the service names and queries their health endpoints; its header comment says they are agent-managed subprocesses, but the agent starts only MCP servers.
- **Impact**: An operator has no documented way to start the LLM services.
- **Recommended Action**: Decide where the procedure lives, document it, and correct the script header comment.
- **Resolution Target**: The deployment document describes how both LLM services are started.

#### DEPLOY-002

- **ID**: DEPLOY-002
- **Title**: Production uv run does not exclude the dev dependency group
- **Status**: open
- **Severity**: Medium
- **Area**: Deployment
- **Type**: operational-gap
- **Source**: `deploy/deploy.sh`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/90_deployment/deployment_01_deployment.md`
- **Related**: `DEPLOY-001`
- **Summary**: The deployment scripts call `uv run` without excluding the `dev` dependency group.
- **Current Description**: deployment_01 section 1.2 states that no script passes such a flag.
- **Observed Implementation**: The deploy scripts call `uv run` with `UV_SYSTEM_CERTS=true` only; `pyproject.toml` has a `dev` group.
- **Impact**: Development dependencies can be installed in production.
- **Recommended Action**: Exclude the dev group in the production scripts, or document a separate production sync.
- **Resolution Target**: Production excludes the dev group, or the production sync is documented.

#### EVENTBUS-008

- **ID**: EVENTBUS-008
- **Title**: Consumer-role token without a consumer_id allowlist skips consumer-identity validation
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Unassigned
- **First Found**: ADR Known Deviations review
- **Target**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- **Related**: `docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`
- **Summary**: A principal without a consumer_id allowlist is not restricted to any consumer_id.
- **Current Description**: ADR-013 INV-02 forbids acting as another `consumer_id`.
- **Observed Implementation**: A `consumer_token` without `consumer_authorization` is rejected at startup. With empty `consumer_authorization` and `topic_authorization` mappings, the CONSUMER token gets `allowed_consumer_ids=None` (unrestricted), as do `auth_token` and `admin_token`.
- **Impact**: An unrestricted principal can use any `consumer_id`.
- **Recommended Action**: Deny all consumers on an empty mapping, or reject it at startup.
- **Resolution Target**: Every CONSUMER token has a non-empty allowlist or is denied, covered by a test.

#### EVENTBUS-015

- **ID**: EVENTBUS-015
- **Title**: Shared auth_token and admin_token grant every role
- **Status**: open
- **Severity**: Medium
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/eventbus/auth.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`
- **Related**: `EVENTBUS-008`
- **Summary**: The mandatory shared token and the admin token map to every role, so per-role separation holds only for callers that hold per-role tokens.
- **Current Description**: ADR-013 defines five roles, each granted a fixed set of routes.
- **Observed Implementation**: The principal map assigns every role to `auth_token` and to `admin_token`.
- **Impact**: A publisher or consumer process given `auth_token` can call operator and admin routes.
- **Recommended Action**: Keep these tokens operator-only and enforce that no publisher or consumer process receives them (for example by a deployment check against ADR-013 INV-07), or make per-role tokens sufficient so the every-role tokens are not needed.
- **Resolution Target**: ADR-013 and the deployment practice agree, or per-role tokens suffice.

Other Known Issue IDs are not tracked here: a resolved or no-longer-applicable item is removed from this inventory.


#### EVENTBUS-016

- **ID**: EVENTBUS-016
- **Title**: Two EventBus DDL sources define slightly different schemas
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: design-gap
- **Source**: `scripts/db/schema_sql.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
- **Related**: `EVENTBUS-015`
- **Summary**: `eventbus.sqlite` can be created from two DDL sources that are not identical.
- **Current Description**: The database documents name both `build_eventbus_schema_sql()` (used by `create_schema()`) and `scripts/eventbus/schema.sql` (used by the EventBus service when the `events` table is missing) as DDL sources.
- **Observed Implementation**: The two differ in the `published_at` default and in one `consumer_delivery` index, which only `schema.sql` creates.
- **Impact**: A database bootstrapped by `create_schema()` can differ from one created by the service at first startup.
- **Recommended Action**: Make one source canonical and generate or load the other from it, or add a test that asserts the two stay equivalent.
- **Resolution Target**: Both bootstrap paths produce the same schema.

#### SHARED-001

- **ID**: SHARED-001
- **Title**: shared/security package has no importers
- **Status**: open
- **Severity**: Low
- **Area**: Shared/DB
- **Type**: design-gap
- **Source**: `scripts/shared/security/__init__.py`
- **Owner**: Unassigned
- **First Found**: Documentation review
- **Target**: `docs/00_governance/governance_05_change-impact-and-dependency-graphs.md`
- **Related**: None
- **Summary**: `HighRiskToolPolicy`, `SecurityMode`, and `AuditLogger` are defined but no module under `scripts/` or `tests/` imports them.
- **Current Description**: Documented only as a note in the Runtime Dependency Graph chapter.
- **Observed Implementation**: The package exports its names from `__init__.py` and nothing imports the package.
- **Impact**: No runtime path uses these classes, so any behavior they define does not take effect.
- **Recommended Action**: Wire the package into the runtime and add it to the dependency graph, or remove it and align the security documents.
- **Resolution Target**: The package is either imported by runtime code or removed.

## Part 2: Needs Confirmation Inventory

### Purpose

An inventory of active "Needs confirmation" items, so unconfirmed statements are tracked rather than silently accepted as facts.

### Inventory Entry Fields

Each entry must contain these fifteen fields: ID, Source File, Section, Line Number, Question, Evidence, Impact, Required Action, Status, Assigned To, Last Reviewed, Priority, Related NC, Resolution Target, Blocking.

### Status Values

- **open** — Acknowledged but not investigated
- **investigating** — Underway
- **deferred** — Postponed

An item is removed from the Active Items list below once it is resolved through a
code or docs update, or once it no longer applies to the current system; it is not
retained here with a closed-out status.

### Priority Values

- **High** — Must resolve before next release
- **Medium** — Resolve within sprint
- **Low** — Nice-to-have

### Extraction Process

Search `docs/` for "Needs confirmation", populate fields from context, add sequential ID, never modify source documents.

### Active Items

Each active item is listed with all fifteen Inventory Entry Fields above.

No active Needs Confirmation items remain.

## Part 3: Canonical Source Conflict

### Purpose

An inventory of active canonical source conflicts, so conflicting claims are tracked rather than silently accepted.

### Entry Template

Each active Canonical Source Conflict entry must contain these 12 fields: ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity (`High`/`Medium`/`Low`), Blocking status (`Blocking`/`Non-blocking`), Required action, Owner, Validation evidence.

### Status Values

- **open** — Conflict acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (exactly one normative source remains and validation evidence confirms the conflict is closed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Active Items

No other active Canonical Source Conflict items remain open.

## Part 4: Configuration Drift

### Purpose

An inventory of discrepancies between deployed and approved operational values.

### Entry Template

Each active Configuration Drift entry must contain these 6 fields: ID, Decision target, Deployed value description, Approved operational value description, Severity, Status.

### Status Values

- **open** — Drift acknowledged but not yet investigated
- **investigating** — Investigation underway

An item is removed from this active inventory once it is resolved (deployed and approved values agree, or the approved value has been formally changed) or no longer applies to the current system; it is not retained here with a closed-out status.

### Active Items

No active Configuration Drift items remain.

## Resolution Rules

The following resolution criteria apply across all four parts of this document:

- Known Issue resolved only when implementation and design agree, or design is formally changed
- Configuration Drift resolved only when deployed and approved values agree, or approved value is formally changed
- Needs Confirmation removed only after evidence establishes intent and the canonical source is updated
- Canonical Source Conflict resolved only when exactly one normative source remains registered
- Documentation correction complete only when validation shows no stale statement remains
- Evidence is required before any discrepancy is reclassified or removed; a documentation-only edit cannot close a design-vs-code conflict without implementation evidence

## Temporary Exception Process

Applies to any automated check finding classified `Warning` (not `Blocking`) in
`docs/00_governance/governance_04_documentation-checks.md`'s Governance Verification Matrix
— for example, `GV-017`'s removed-name reintroduction findings. A `Warning`
finding does not block merge by itself, but leaving it neither fixed nor formally
excepted is not a complete review (see `docs/00_governance/governance_04_documentation-checks.md`
`### 19. Merge Condition Validation`).

### Exception Record Fields

A temporary exception records a **Reason** (why the finding is not fixed now), an **Owner** (the person who accepted it; not `Team` or `Unassigned`) and an **Expiration Date** (when it must be re-reviewed or fixed; an exception without one is not valid).

### Recording an Exception

Record the exception inline, next to the flagged line, as:

`<!-- exception: {rule-id} — {reason} — {owner} — expires {YYYY-MM-DD} -->`

An exception past its expiration date is treated as an unexplained finding (see
`docs/00_governance/governance_04_documentation-checks.md`
`### 19. Merge Condition Validation`) — not as still-covered.

## Non-Goals

Excluded topics:

- Resolving individual items — resolution requires separate investigation
- Modifying source documents during extraction — this document is read-only relative to sources
- Defining new evidence labels beyond those already established
- Changing the common template itself

## Keywords

- known issues
- needs confirmation
- inconsistencies
- template
- evidence labels
- resolution workflow
