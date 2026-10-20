## Goal
Make `docs/90_deployment/deployment_01_deployment.md` state that the Event Bus credential is supplied through the
operator `.env` file and gated by `deploy/setup_services.sh`, so an operator sets the variable before running the
deployment script instead of editing a deployed configuration file that the next deploy replaces.

## Scope
- Five narrow wording edits: the Starting Services paragraph (line 157), the pre-flight responsibility list
  (line 164), the `.env` loader paragraph (line 208), the sample `.env` block (lines 222-223), and the Deployment
  Checklist (lines 320-321).
- No new heading, no new section, and no change to section 2.5's MCP token wording beyond the sentences named
  below. `check_docs_structure.py` link reachability is unaffected because no heading is renamed.

## Assumptions
- The wording is written after seq 03 and seq 04 are implemented, so every claim describes code that exists.
- Byte budget, measured: the file is 23527 bytes and `check_docs_structure.py` enforces a 24576 byte limit for it
  (it has no entry in `SIZE_EXCEPTIONS`), so the edits added by this procedure must stay under roughly 900 bytes.
  The wording below is drafted to that budget; `wc -c` is a completion criterion rather than an after-the-fact
  discovery.
- The Plan's Documentation Impact bullet asks to "remove any wording that implies editing the deployed TOML".
  Measured against the current file: it contains no `eventbus.toml` mention and no instruction to edit a deployed
  Event Bus configuration, so there is nothing to remove; the added sentences are the whole change.
- The Plan's `UNK-01` (whether the Event Bus is mandatory for a production deployment) stays a Plan-level
  unknown. No `Needs confirmation` marker is added here: an inline marker requires a matching entry in
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md`, which is not a target of this Plan, and
  the sentences added below only restate verified script behavior, so none of them is an unverified claim.
- Section 2.5.1's heading keeps its wording even though the Event Bus token is now mentioned under it, because
  renaming a heading would require re-checking every link and `related:` entry that names it.

## Design decisions
- Extend the sentences the operator already reads (2.3 and 2.5.1) instead of adding an Event Bus subsection, which
  is what keeps the byte budget.
- Name the helper file only where it changes what the operator must do, and state plainly that
  `deploy/start_agent.sh` still keeps its own inline copy of the same rules; claiming both scripts already share
  the loader would be false in this cycle (`UNK-02` records the consolidation follow-up).
- The checklist item is phrased as an observed script outcome ("reported no `[FATAL]` credential error"), not as
  an instruction to edit a file.

## Alternatives considered
- Add a new "2.5.2 Event Bus token" subsection: rejected on the measured byte budget and on the link-reachability
  check that a new heading drags in.
- Document every Event Bus token variable: rejected; only the shared control-plane credential ships as a
  reference in this cycle (`UNK-03`).
- State that the Event Bus must always be running in production: rejected; that is exactly what `UNK-01` has not
  established, so the added text stays silent about it.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. Add the credential check to the Starting Services description and the pre-flight list.
2. Add the Event Bus variable to the `.env` loader paragraph and to the sample file block.
3. Add the checklist item.

### Method
Edit 1:

```markdown
# Before:
`deploy/setup_services.sh` runs the workflow pre-flight checks and starts the Event Bus.
# After:
`deploy/setup_services.sh` runs the workflow pre-flight checks, verifies the Event Bus credential, and starts the Event Bus.
```

Edit 2:

```markdown
# Before:
- The Event Bus is started **only if** all workflow checks pass — a failure here aborts before any service is spawned
# After:
- The Event Bus is started **only if** all workflow checks pass — a failure here aborts before any service is spawned
- The Event Bus credential is checked against the variables its configuration references; a missing or empty one aborts with a `[FATAL]` list before the process is spawned
```

Edit 3:

```markdown
# Before:
Before launching, the startup script validates that every variable referenced by the deployed configuration (`${ENV:...}` entries in `config/agent.toml` and the per-server `*_mcp_server.toml` files) is set and non-empty. Any missing variable aborts startup with a `[FATAL]` message that lists exactly which variables are unset, instead of producing a deep traceback later.
# After:
Before launching, the startup script validates that every variable referenced by the deployed configuration (`${ENV:...}` entries in `config/agent.toml` and the per-server `*_mcp_server.toml` files) is set and non-empty. Any missing variable aborts startup with a `[FATAL]` message that lists exactly which variables are unset, instead of producing a deep traceback later. `deploy/setup_services.sh` reads the same file before it starts the Event Bus, through the shared `deploy/load_env.sh`, and gates on the variables the Event Bus configuration references; the shipped file references EVENTBUS_AUTH_TOKEN for its control-plane credential. `deploy/start_agent.sh` still carries its own inline copy of these rules (Explicit in code — `deploy/start_agent.sh`, `deploy/load_env.sh`, `deploy/setup_services.sh`, `config/eventbus.toml`).
```

Edit 4 (the last two lines of the sample block; the Event Bus line is appended after them):

```markdown
# Before:
MCP_RAG_PIPELINE_AUTH_TOKEN=
MCP_MDQ_AUTH_TOKEN=
# After:
MCP_RAG_PIPELINE_AUTH_TOKEN=
MCP_MDQ_AUTH_TOKEN=
EVENTBUS_AUTH_TOKEN=
```

Edit 5:

```markdown
# Before:
- [ ] `setup_services.sh` passed pre-flight checks
# After:
- [ ] `setup_services.sh` passed pre-flight checks
- [ ] `setup_services.sh` reported no `[FATAL]` Event Bus credential error, meaning EVENTBUS_AUTH_TOKEN is set in the environment file or shell
```

## Compatibility considerations
- The Event Bus token distribution wording (the existing checklist item that points at
  `eventbus_07_configuration-and-operations.md`, Token Distribution) is unchanged: this document adds how the
  shared credential is supplied, not how per-role tokens are distributed.
- The MCP token paragraphs keep their meaning; only the shared-loader sentence is appended.
- `rules/env.md` is not a target (Plan's Documentation Impact section), and nothing added here contradicts its
  `config/eventbus.toml` row.
- `deploy.sh` rsyncs `docs/` to `/opt/llm/docs/`, so the mdq index must be rebuilt after the deploy (Plan's
  Validation plan row).

## Security considerations
- The document directs the credential to the `.env` file, which is gitignored and mode 600, instead of to a file
  under the install root that `deploy/deploy.sh` rewrites on every deploy.
- The sample line is an empty placeholder: no real credential appears in the document, and no command that prints
  one is added.

## Rollback considerations
Single-path revert: `git checkout HEAD -- docs/90_deployment/deployment_01_deployment.md`.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Size | `wc -c docs/90_deployment/deployment_01_deployment.md` | at or below 24576 bytes, with margin |
| Structure | `uv run python tools/check_docs_structure.py docs/90_deployment/deployment_01_deployment.md` | no findings, in particular no size finding |
| Formatting | `uv run python tools/check_docs_quality.py` | no findings for this file |
| Content policy | `uv run python tools/check_docs_content_policy.py --strict` | new claims carry an `(Explicit in code — ...)` pointer |
| Domain consistency | `uv run python tools/check_docs_consistency.py --domain deployment` | no claim contradicts `config/agent.toml` or `scripts/` |
| Language | `uv run python tools/check_docs_japanese.py` | no Japanese text in the document |
| Needs confirmation | `uv run python tools/check_needs_confirmation_inventory.py` | no new inline marker, so no inventory entry is required |
| Stale procedure | `uv run python tools/stale_detector.py implementations/20261020-112551_08_docs_90_deployment_deployment_01_deployment.md.md` | no findings |

## Completion criteria
- All five edits are present and none of the `Before:` snippets still appears in the file.
- The file is still within the 24576 byte limit with at least 200 bytes of margin.
- The document states that the supported way to supply the Event Bus credential is the environment file, and
  nowhere instructs editing a deployed Event Bus configuration file.

## Out of Scope
- `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (seq 07) and `rules/env.md`.
- `deploy/start_agent.sh` consolidation onto `deploy/load_env.sh` (`UNK-02`).
- The embed-llm health gate wording, which describes behavior ebops002 will change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-132438 | 20261020-132438 | write after seq 03, 04 five edits applied after seq 03, 04 landed; all five Before anchors matched source at :157, :164, :208, :222-223, :320 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-132438 | n/a: documentation target n/a: documentation target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-132438 | docs checker family docs checker family green including check_docs_consistency --domain deployment (exit 0, no issues); first pass measured 24400 B (margin 176, below the 200 B completion criterion), so three added sentences were trimmed 36 B to 24364 B (margin 212) and the trimmed wording was mirrored into this doc's After blocks |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-132438 | this document is the documentation target this document is the documentation target; docs/ redeploy + mdq index rebuild happen in the cycle-end deploy step |

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
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20261019-210937_ebsec001_eventbus_auth_token_startup_block.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261020-111348_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261020-112551
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`, `deploy/load_env.sh` (seq 03),
  `deploy/setup_services.sh` (seq 04), `config/eventbus.toml` (seq 02),
  `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (seq 07)