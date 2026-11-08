## Goal
- Clarify `docs/10_adr/adr_02_01_002_platform-config-isolation.md` so the general `restrict_to()` rule and the EventBus exception are immediately identifiable, file isolation is separated from key validation, and security claims state only what the loader and the deployment actually provide.

## Priority
Medium

## Scope
- **In-Scope**: edits to ADR-002 only: Decision Details item 9 and its note, the Per-Process Required Files and Keys lead-in and table, Rationale 1, Assumptions, Security Consequences, Exceptions, Implementation Notes, and any other statement found to claim physical isolation.
- **Out-of-Scope**: loader refactoring; secret-management redesign; EventBus authentication changes; changing `load_config()` or `get_config_path()`; adding operating-system or secret-management mechanisms; changing any invariant text, decision, or ownership.
- **Dependencies**: blocks the final mapping step of `issues/20261107-050705_adrver001_align-invariant-verification-claims.md`. No dependency on another Plan or Issue; no other Plan or Issue targets this file (overlap tool checked in Step 8b).

## Background
Verified against the current file and source (checked in Step 2):
- The Per-Process lead-in (L81) says each process restricts itself via `ConfigLoader.restrict_to()`, and Exceptions (L187) calls the restriction "otherwise unconditional", while EventBus loads through the shared loader without `restrict_to()` (L70, L90, L185). The Issue's "Decision item 81" is a line number, not a Decision item.
- Rationale 1 (L114) says access to other processes' Secrets "is physically blocked".
- The Required Keys table (L83-L90) mixes the loader's file restriction (the "Required Config File" column) with key validation by the loader or validators (the "Required Keys" column).
- `ConfigLoader.restrict_to()` (`scripts/shared/config_loader.py` L41-61) sets a process-wide allowed-basename set, once per process; `_check_permission()` (L117-126) raises `ConfigPermissionError` only for loads that go through `ConfigLoader`, and does nothing when the set is `None`. It does not prevent reading a file by any other means. Call sites: the Agent (`scripts/agent/context.py` L388), MCP servers (`scripts/mcp_servers/server.py` L291 and `scripts/mcp_launcher.py` L145), crawler, chunk_splitter and ingester.
- The EventBus invariant is weaker than the ADR says. Implementation Notes (L257) state `load_config()` "accepts only the path returned by `get_config_path()`". The docstring of `load_config()` (`scripts/eventbus/config.py` L327-334) says it does not itself restrict the path; callers must pass `get_config_path()`, and a call-site test (`tests/eventbus/test_eventbus_config.py::test_load_config_call_sites_pass_get_config_path`) locks that. `_load_config_from_path()` builds a `ConfigLoader` without `restrict_to()`, so no permission check runs. `get_config_path()` returns `$EVENTBUS_CONFIG_PATH` when set, an operator-facing override documented in `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (L51, L124) and exported by `deploy/setup_services.sh` (L166-185). Decision item 6 ("The EventBus reads only `config/eventbus.toml`") does not mention the override.
- No operating-system control is established by the repository: `deploy/` scripts only warn when the `.env` file permissions are looser than 600 (`deploy/start_agent.sh`, `deploy/load_env.sh`), and no `chmod`, `chown`, or service-user separation for `config/*.toml` was found. The `config/*.toml` files carry `auth_token` values (for example `config/agent.toml`, `config/eventbus.toml`).

## Problem
A universal statement followed by an exception can lead an implementer to remove the deliberate EventBus exception or to add mechanisms the ADR does not need. File selection and key validation answer different risks. "Physically blocked" overstates a process-internal check. The EventBus exception is described as a path-accepting invariant that the code only keeps by call-site convention, and its operator override is not stated.

## Reason for Change
An inaccurate security assurance can mislead operators and reviewers. It is Medium because it is a wording and precision change; the underlying mechanisms stay as they are and nothing is time-sensitive.

## Implementation Intent
Describe the existing configuration model with its limits. State the general rule first and the EventBus exception beside it. Distinguish permitted configuration files, key validation, the shared loader's role, the EventBus-local controls, and operating-system access restrictions. Replace the physical-isolation claim with the mechanism-specific guarantee, and state which assumptions depend on deployment controls outside the loader. Leave invariant text unchanged so no preservation finding arises.

## Requirements
- `REQ-001`: The general rule (the loader rejects a non-permitted configuration file for a process that called `restrict_to()`) and the EventBus exception are stated together, each identifiable in Decision item 9, the Per-Process lead-in, and Exceptions, and "otherwise unconditional" is limited to what the loader enforces.
- `REQ-002`: The Per-Process section separates file isolation (which file a process may load, by which mechanism) from key validation (which keys the loader or validator requires); the EventBus row names its different isolation mechanism.
- `REQ-003`: The EventBus-local controls are described as verified: the default path, the documented `EVENTBUS_CONFIG_PATH` operator override, that `load_config()` does not itself restrict the path, that call sites passing `get_config_path()` are locked by a regression test, and that no `ConfigLoader` permission check runs; the Implementation Notes sentence that `load_config()` "accepts only" that path is corrected, and Decision item 6 is qualified.
- `REQ-004`: Rationale and Security Consequences replace "physically blocked" with the mechanism-specific guarantee and state that the loader check does not prevent a process from reading other files by other means.
- `REQ-005`: The ADR states, as an explicit assumption, that confining each process's Secrets also depends on deployment controls outside the loader (operating-system file permissions and service-user separation), and that the repository does not establish them.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Authoritative configuration-isolation ADR | Reconcile rule and exception wording, separate file isolation from key validation, correct the EventBus invariant description, replace the physical-isolation claim, state deployment assumptions | `REQ-001` to `REQ-005` / AC-01 to AC-06 | L70, L81, L90, L114, L185-L187, L257 (checked in Step 2); `scripts/eventbus/config.py` L20-L34, L327-L334 and `scripts/shared/config_loader.py` L41-L61, L117-L126 (checked in Step 3) | `tests/shared/test_config_loader.py`, `tests/eventbus/test_eventbus_config.py`, `tests/agent/test_config_permission_cross_server.py` (existing, run unchanged) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/shared/config_loader.py` | Defines what `restrict_to()` and `_check_permission()` enforce | `REQ-001`, `REQ-004` |
| `scripts/eventbus/config.py` | `get_config_path()`, `_load_config_from_path()` and the `load_config()` docstring | `REQ-003` |
| `scripts/eventbus/app.py` | The two call sites that pass `get_config_path()` (L85, L391) | `REQ-003` |
| `scripts/mcp_servers/server.py` | MCP server `restrict_to(self.own_config_file)` call (L291) | `REQ-001` |
| `scripts/agent/context.py` | Agent `restrict_to("agent.toml")` call (L388) | `REQ-001` |
| `tests/eventbus/test_eventbus_config.py` | Holds the call-site regression test that the ADR cites | `REQ-003` |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Documents the `EVENTBUS_CONFIG_PATH` override (L51, L124) | `REQ-003` |
| `deploy/setup_services.sh` | Exports `EVENTBUS_CONFIG_PATH` (L166-L185) | `REQ-003` |
| `deploy/start_agent.sh` | Shows that only `.env` permissions produce a warning, no config-file control (L110-L115) | `REQ-005` |
| `deploy/load_env.sh` | Same `.env` permission warning (L22) | `REQ-005` |

## Acceptance Criteria
- AC-01 (`REQ-001`): Decision item 9, the Per-Process lead-in and Exceptions each name both the general rule and the EventBus exception, and no sentence calls the restriction unconditional beyond what the loader enforces.
- AC-02 (`REQ-002`): The Per-Process section names the file-isolation mechanism and the key-validation owner separately for every process, including the EventBus row.
- AC-03 (`REQ-003`): The ADR states the `EVENTBUS_CONFIG_PATH` override, that `load_config()` does not restrict the path, and the call-site test; the sentence "accepts only the path returned by `get_config_path()`" no longer appears.
- AC-04 (`REQ-004`): "Physically blocked" no longer appears; the replacement names the loader-level rejection and states its limits.
- AC-05 (`REQ-005`): The deployment-control assumption is present and says the repository does not establish those controls.
- AC-06: Invariant identifiers and text, decisions and ownership are unchanged; `check_adr_preservation.py` reports no ERROR; the document checkers pass.

## Tests
- Documentation-only; no new test. `uv run pytest tests/shared/test_config_loader.py tests/eventbus/test_eventbus_config.py` runs once to confirm the cited mechanisms still behave as the ADR now states (`REQ-001`, `REQ-003`).
- Review the complete document for universal claims that conflict with exceptions or exceed the stated controls (`REQ-001` to `REQ-005`).

## Documentation Impact
Yes; this Plan is the documentation change. Target: ADR-002 only (located through `docs/10_adr/adr_01_index.md`). Driven by `REQ-001` to `REQ-005`. Document boundaries, constraints, security guarantees and deployment assumptions. English only.

## Assumptions
- The code and the cited test describe the mechanisms; the ADR is the side to correct (falsifiable by an owner statement that the EventBus path must be locked to `config/eventbus.toml`, which would be a code change outside this Plan).
- No operating-system control is assumed to exist; the ADR states only what the repository evidences (falsifiable by host configuration not visible from the repository, see UNK-01).
- Invariant text is left unchanged, so `check_adr_preservation.py` should report no ERROR; the clarifications live in Decision, Rationale, Consequences, Exceptions and Implementation Notes.
- The ADR is 20519 bytes, under the 24576-byte default size limit, so the added statements fit if they stay concise.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any operating-system or deployment control (file permissions, service users) restricts access to `config/*.toml` on the deployed host | Host configuration is not in the repository; `deploy/` shows only a `.env` permission warning | The ADR states that the repository establishes no such control and that confinement depends on the deployment; an operator may confirm later | False |
| UNK-02 | Whether the `EVENTBUS_CONFIG_PATH` override and the unenforced path invariant of `load_config()` are an accepted part of the EventBus exception or a deviation to register | An owner decision; the override is documented in `eventbus_07` but ADR-002 Decision item 6 omits it | The ADR states the facts; registering a Known Deviation or changing `load_config()` is a separate owner decision and Issue | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Modify | Medium | N/A | N/A | not applicable (rsynced) |

## Design
Classification: Path A (1 target file, no interface or schema change); architecture, dependency, historical and operational analyses are skipped. Direct verification of consumers: the ADR is referenced by the ADR index and document guides, and its cited tests exist (checked in Step 3). Validation quality baseline: `N/A: no Python target`.

Decisions:
1. Invariants stay untouched; precision is added in Decision item 9, the Per-Process section, Rationale, Security Consequences, Exceptions and Implementation Notes, so no preservation ERROR arises. Alternative considered: rewording INV-02 ("Access to non-permitted configuration files is rejected") to name the loader; rejected because it would trigger an ERROR and the clarification fits in Exceptions.
2. The EventBus exception is kept and made more exact, not removed; the facts (default path, override, no `ConfigLoader` check, call-site test) are stated as Explicit in code.
3. The deployment-control assumption is added to Assumptions and referenced from Security Consequences, so a reader sees the dependency where the trust boundary is stated.

## Implementation steps
1. **Phase 1: Rule and exception wording**
   - [ ] Reconcile Decision item 9, the Per-Process lead-in and Exceptions; qualify Decision item 6 (`REQ-001`, `REQ-003`; `docs/10_adr/adr_02_01_002_platform-config-isolation.md`)
2. **Phase 2: File isolation versus key validation**
   - [ ] Restructure the Per-Process lead-in and table so isolation mechanism and key validation are separate, including the EventBus row (`REQ-002`; same file)
3. **Phase 3: EventBus controls and security claims**
   - [ ] Correct the Implementation Notes EventBus description (`REQ-003`; same file)
   - [ ] Replace "physically blocked" in Rationale and Security Consequences (`REQ-004`; same file)
   - [ ] Add the deployment-control assumption (`REQ-005`; same file)
4. **Phase 4: Verification**
   - [ ] Read the complete ADR for universal claims; run the Validation plan commands (`REQ-001` to `REQ-005`; same file). No deploy step: no `scripts/` or `config/` file changes.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ADR-002 | Documentation structure, quality, policy, language | `uv run python tools/check_docs_quality.py`; `uv run python tools/check_docs_structure.py docs/10_adr/adr_02_01_002_platform-config-isolation.md`; `uv run python tools/check_docs_content_policy.py`; `uv run python tools/check_docs_japanese.py` | No findings |
| ADR-002 | ADR preservation and structure | `uv run python tools/check_adr_preservation.py`; `uv run python tools/check_adr_structure.py`; `uv run python tools/check_adr_invariant_matrix.py` | No ERROR; invariants unchanged |
| Cited mechanisms | Regression | `uv run pytest tests/shared/test_config_loader.py tests/eventbus/test_eventbus_config.py` | Pass |

## Risks
- **Risk**: The corrected EventBus description is read as a newly found defect and prompts an unplanned code change → **Mitigation**: the ADR states the facts neutrally and UNK-02 routes the decision to the owner; no code change is made here.
- **Risk**: Added statements push the ADR over the size limit → **Mitigation**: keep each addition to one or two sentences; run the structure checker.
- **Risk**: A security-limit statement is read as a new guarantee or a new requirement → **Mitigation**: phrase it as an assumption that the repository does not establish, with UNK-01 for later confirmation.
- **Risk**: Restructuring the Per-Process table changes meaning or breaks an anchor → **Mitigation**: keep the heading, add wording or one column only, and run the structure and invariant-matrix checkers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rule and exception wording | Completed | — | 20261108-113256 |  |
| 2 | File isolation versus key validation | Completed | — | 20261108-113256 |  |
| 3 | EventBus controls and security claims | Completed | — | 20261108-113256 |  |
| 4 | Verification | Completed | — | 20261108-113256 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261108-111529_01_docs_10_adr_adr_02_01_002_platform-config-isolation.md.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261107-050704_adrcfg001_clarify-adr-002-isolation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-092140
- **Related target files**: `docs/10_adr/adr_02_01_002_platform-config-isolation.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; ADR L69-L70, L81, L185-L187 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 1 | AC-01 | Full read-through; `check_adr_structure.py` | Confirmed by repository evidence |
| REQ-002 | Required Changes 2; ADR L79-L92 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 2 | AC-02 | Full read-through; `check_docs_quality.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 3; `eventbus/config.py` L20-L34, L327-L334; `eventbus_07` L51 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 1, Phase 3 | AC-03 | `tests/eventbus/test_eventbus_config.py`; full read-through | Confirmed by repository evidence |
| REQ-004 | Required Changes 4-5; ADR L114; `config_loader.py` L117-L126 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 3 | AC-04 | Full read-through; `check_docs_content_policy.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 6; Unresolved Questions; `deploy/start_agent.sh` L110-L115 | `docs/10_adr/adr_02_01_002_platform-config-isolation.md` | Phase 3 | AC-05 | Full read-through | Needs confirmation |