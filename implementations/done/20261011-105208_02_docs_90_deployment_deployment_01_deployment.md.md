## Goal

Document, in `docs/90_deployment/deployment_01_deployment.md`, the remote LLM service
prerequisites and the deploy-time validation steps (REQ-003), keeping them consistent
with the updated `setup_services.sh` that now validates remote health (post-REQ-001 /
REQ-002) instead of merely echoing service names.

## Scope

- Modify only `docs/90_deployment/deployment_01_deployment.md`, Section 2.3
  ("Starting Services") and its inline validation example.
- Reference files (read-only): `deploy/setup_services.sh` (for the post-change behavior
  to describe), `config/agent.toml` (for the exact config keys). No other file is a
  modification target.

## Assumptions

- The remote LLM prerequisites and validation steps are partially documented already;
  the procedure focuses on closing the specific gaps identified in adversarial
  verification (see Details), not rewriting existing content.
- The config keys `embed_url` / `llm_url` live in `config/agent.toml` (verified: lines
  10 and 23). The health-path convention is `<base>/health`.

## Design decisions

- **Keep the "repo validates, does not spawn" framing.** The doc already correctly
  states the LLM services must run before the agent and are started outside the repo
  (tracked as DEPLOY-001). Preserve this; it is the core of REQ-003.
- **Reference the actual config keys, not placeholders.** Replace the `<host>:<port>`
  illustrative example with a pointer to the real config keys (`embed_url`, `llm_url` in
  `config/agent.toml`) so operators know where to read the values.
- **Preserve the model-dimension prerequisite** (line 66, referencing
  `scripts/db/store_protocols.py::get_embedding_dims()`).

## Alternatives considered

- **Rewrite the whole "Starting Services" section.** Rejected: most of it is correct;
  targeted edits avoid churn and risk.
- **Add the systemd-unit question (UNK-01) here.** Rejected: UNK-01 is out of scope;
  the doc already defers the start procedure to DEPLOY-001.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`

### Procedure
1. **Verify REQ-003 prerequisites are present.** Confirm the embedding-model dimension
   prerequisite (line 66, referencing `scripts/db/store_protocols.py::get_embedding_dims()`)
   and the "services must run before the agent; started outside the repo (DEPLOY-001)"
   statement (line 106) are present. (Both are.)
2. **Update line 104 to reflect the post-REQ-001 script.** It currently says
   setup_services.sh "only echoes their names and later queries their health endpoints";
   reword it to state that it now validates the remote `/health` endpoints (config-driven,
   retry-bounded) before the agent starts.
3. **Tighten the validation example (lines 119-127).** Replace the `<host>:<port>`
   placeholders with a reference to the actual config keys (`embed_url`, `llm_url` in
   `config/agent.toml`), keeping the illustrative curl form but pointing operators at the
   real source of truth.

### Method
- Read `config/agent.toml` to cite the exact keys (`embed_url` line 10, `llm_url` line
  23) and confirm the health-path convention (`<base>/health`).
- Make minimal, localized edits to Section 2.3 ("Starting Services"); do not restructure
  the surrounding sections.
- Keep the doc's existing English prose style and cross-reference format (e.g. the
  `> **Canonical source**` note pattern used elsewhere in the file).

### Details
- Evidence (adversarial verification against current source): line 66 documents the
  embedding-model dimension prerequisite; line 104 states setup_services.sh does not
  start LLM services and only echoes their names + queries health; line 106 states no
  repo artifact starts the LLM services and the start procedure is tracked as DEPLOY-001
  in `governance_03_issue-and-uncertainty-management.md`; lines 119-127 contain validation
  steps but use `<host>:<port>` placeholders ("Illustrative: use the hosts/ports from
  llm.llm_url and rag.embed_url in config/agent.toml").
- The doc already substantially satisfies REQ-003; the implementation should focus on the
  two gaps above (line 104 consistency with the changed script, placeholder tightening),
  not rewrite existing content.
- Note: line 122 references `llm.llm_url` / `rag.embed_url` (nested-table notation);
  confirm this matches the actual `config/agent.toml` structure (`embed_url` / `llm_url`
  appear at lines 10 / 23) and correct any mismatch while editing.

## Compatibility considerations

- This doc is read-only in the deploy pipeline; changes have no runtime effect. Ensure
  any statement about setup_services.sh stays consistent with the changed script (doc 1)
  to avoid contradiction.

## Security considerations

- The config URLs contain internal IPs only (no secrets). Do not hardcode live
  credentials; point operators to the config file.

## Rollback considerations

- Revert `docs/90_deployment/deployment_01_deployment.md` to the previous committed
  version (single file). No schema or config impact.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `docs/90_deployment/deployment_01_deployment.md` | Documentation review | Review Section 2.3 | Remote LLM prerequisites (model dimension, must-run-before-agent) and deploy-time validation steps are present and reference the real config keys; no contradiction with the changed setup_services.sh |

## Completion criteria

- Line 104 reflects that setup_services.sh validates the remote `/health` endpoints
  (post-REQ-001), not merely echoes.
- Validation steps reference the actual `embed_url` / `llm_url` config keys rather than
  `<host>:<port>` placeholders.
- Embedding-model dimension prerequisite remains documented (line 66).
- No statements contradict the changed `setup_services.sh`.

## Out of scope

- Starting / spawning the LLM services (remote; tracked as DEPLOY-001).
- Creating repo-local systemd units for the remote hosts (UNK-01).
- Changing the LLM services' own `/health` endpoints.
- Editing LLM configuration files.
- Any file other than `docs/90_deployment/deployment_01_deployment.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261011-124509 | 20261011-124509 | Section 2.3 updated: remote /health gate behavior; corrected embed_url/llm_url config-key refs (was nested llm.llm_url/rag.embed_url) |
| 2 | Add or update tests per Validation plan | Completed | 20261011-124509 | 20261011-124509 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261011-124509 | 20261011-124509 | check_docs quality/structure/content-policy/japanese clean; consistency --domain deployment clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261011-124509 | 20261011-124509 |  |

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
- **Source issue**: issues/done/20261007-154048_llmsvc01_provide-reproducible-startup-for-llm-services.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162838_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-105208
- **Related target files**: docs/90_deployment/deployment_01_deployment.md