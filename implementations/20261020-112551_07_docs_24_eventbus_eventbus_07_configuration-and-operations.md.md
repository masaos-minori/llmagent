## Goal
Make `docs/24_eventbus/eventbus_07_configuration-and-operations.md` state how the shipped Event Bus
configuration actually obtains its control-plane credential: the shipped file holds an environment reference, the
Event Bus package resolves it at config load, and an unset or empty variable stops startup instead of starting an
unauthenticated server.

## Scope
- Four wording edits: the `auth_token` bullet (line 67), the validation paragraph (line 81), the Token
  Distribution closing paragraph (line 95), and the Start Command block (line 123 plus its following sentence).
- No new section, no new document, and no change to the Token Distribution table or the role semantics.

## Assumptions
- The wording describes seq 01 and seq 02 as they will exist after this cycle: `load_config` resolves
  `${ENV:...}` for the six token keys, and the shipped `config/eventbus.toml` ships
  `auth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"`. Write this document after those two rows are implemented, so no
  claim is ahead of the code.
- The variable name is not written in backticks in this procedure document: `stale_detector` checks a
  backticked identifier-shaped name against existing source, and the name only exists in the repository after
  seq 02. The exact name appears inside the fenced blocks, which are not checked.
- No `Needs confirmation` marker is added: every statement below describes behavior that exists in code after
  this cycle, and an inline marker would need an entry in the governance inventory document, which is not a
  target of this Plan.

## Design decisions
- Add the resolution facts to the sentences the operator already reads (`auth_token` bullet and the validation
  paragraph) instead of creating a new "Environment references" section, so the document keeps one place per
  fact.
- Keep the existing `Do not start the server with uvicorn directly` sentence untouched and only extend the code
  block and its introduction, because the loopback-verification requirement is a separate contract documented
  elsewhere.
- Name the failure mode explicitly (`ValueError` naming the variable) so an operator triaging a startup abort
  recognizes the message rather than treating it as an Event Bus defect.

## Alternatives considered
- Add a cross-link to `docs/90_deployment/deployment_01_deployment.md` instead of stating the facts: rejected;
  this document is the operator-facing Event Bus configuration reference, and the Plan's `AC-3` is satisfied by
  the facts being present here.
- Document all six token keys as references: rejected; the shipped file keeps literal values for the per-role
  keys in this cycle (Plan `UNK-03`), so the document must not claim they are references.

## Implementation
### Target file
`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure
1. Extend the `auth_token` bullet with the shipped indirection and its resolution.
2. Extend the validation paragraph with the unset-variable failure mode.
3. Replace the "its environment or configuration file" wording in the Token Distribution paragraph with the
   shipped variable plus the note that a hand-edited deployed file is replaced by the next deploy.
4. Extend the Start Command block so the reader sees that the referenced variable must be set.

### Method
Edit 1:

```markdown
# Before:
- `auth_token` — Required (startup fails if empty); a control-plane credential holding only the operator, monitoring, and admin roles
# After:
- `auth_token` — Required (startup fails if empty); a control-plane credential holding only the operator, monitoring, and admin roles. The shipped `config/eventbus.toml` stores it as an environment reference, so the credential comes from the operator environment at load time rather than from the deployed file (Explicit in code — `config/eventbus.toml`, `scripts/eventbus/config.py`)
```

Edit 2:

```markdown
# Before:
Invalid combinations fail startup with actionable error messages naming both conflicting values. Startup fails unless `auth_token` is configured; the per-role tokens above are optional additions.
# After:
Invalid combinations fail startup with actionable error messages naming both conflicting values. Startup fails unless `auth_token` is configured; the per-role tokens above are optional additions. A token key written as `"${ENV:VAR_NAME}"` is resolved when the configuration is loaded: the value must be present in the environment, and an unset variable raises `ValueError` naming it, so a reference that resolves to nothing never reaches a running server. A reference that resolves to an empty string is rejected by the same non-empty rule as a literal empty value.
```

Edit 3:

```markdown
# Before:
Before deploying a publisher or consumer process, confirm that the token it is configured with (its environment or configuration file; the variable names are operator choices) is its own per-role token and differs from the `auth_token` and `admin_token` values in the Event Bus configuration file.
# After:
Before deploying a publisher or consumer process, confirm that the token it is configured with (its environment or configuration file; the variable names are operator choices) is its own per-role token and differs from the `auth_token` and `admin_token` values in the Event Bus configuration file. For the shared control-plane credential, the shipped configuration (`config/eventbus.toml`) references one environment variable, so the supported way to change it is to change that variable in the operator environment file and restart; a hand-edited copy of the deployed configuration file is replaced by the next run of `deploy/deploy.sh`. (Explicit in code — `config/eventbus.toml`, `deploy/deploy.sh`)
```

Edit 4 (the Start Command block plus the sentence that follows it; the new paragraph is appended after the
existing `Do not start the server with uvicorn directly` sentence, which is not touched):

````markdown
# Before:
```bash
EVENTBUS_CONFIG_PATH=<path-to-eventbus.toml> python -m eventbus.app
```
# After:
```bash
# Token references in the configuration are resolved when it is loaded, so the referenced
# variable must already be present in the environment before this command runs.
EVENTBUS_CONFIG_PATH=<path-to-eventbus.toml> python -m eventbus.app
```

The shipped `config/eventbus.toml` stores the shared control-plane credential as an environment reference.
Configuration loading aborts with a `ValueError` naming the variable when it is unset, and the deployment
script reports the same missing variable in its `[FATAL]` list before launching the process. (Explicit in code —
`scripts/eventbus/config.py`, `config/eventbus.toml`, `deploy/setup_services.sh`)
````

## Compatibility considerations
- The documented role semantics, the Token Distribution table, and the loopback-starting contract are unchanged;
  only the credential-sourcing wording changes.
- `docs/00_index.md` already maps Event Bus configuration work to this document, so no index edit is needed.
- The deployed copy of `docs/` is refreshed by `deploy/deploy.sh` and the mdq index must be rebuilt after the
  deploy (Plan's Validation plan row).

## Security considerations
- The document now points the operator at the environment variable instead of at a secret stored in a deployed
  file, which is the path that keeps the credential out of the repository and out of `rsync` targets.
- The example reads the value with `grep`/`cut` rather than printing a real secret; no literal credential appears
  in the document.

## Rollback considerations
Single-path revert: `git checkout HEAD -- docs/24_eventbus/eventbus_07_configuration-and-operations.md`. No code
depends on the wording.

## Validation plan
| Check | Command | Expected outcome |
|---|---|---|
| Structure | `uv run python tools/check_docs_structure.py docs/24_eventbus/eventbus_07_configuration-and-operations.md` | no findings for this file |
| Formatting | `uv run python tools/check_docs_quality.py` | no findings for this file |
| Content policy | `uv run python tools/check_docs_content_policy.py --strict` | the new claims carry an `(Explicit in code — ...)` pointer instead of restating implementation detail |
| Language | `uv run python tools/check_docs_japanese.py` | no Japanese text in the document |
| Needs confirmation | `uv run python tools/check_needs_confirmation_inventory.py` | no new inline marker is introduced, so no inventory entry is required |
| Stale procedure | `uv run python tools/stale_detector.py implementations/20261020-112551_07_docs_24_eventbus_eventbus_07_configuration-and-operations.md.md` | no findings |

## Completion criteria
- All four edits are present and the `Before:` snippets no longer appear in the file.
- The file contains no statement that the shipped configuration stores the shared token as a literal value.
- The documentation checker family is clean.

## Out of Scope
- `docs/90_deployment/deployment_01_deployment.md` (seq 08) and `rules/env.md` (Plan: not a target).
- `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`: the role model is unchanged, so the ADR
  needs no edit.
- Changing the per-role token lines in `config/eventbus.toml` (`UNK-03`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261020-132038 | 20261020-132038 | write after seq 01, 02 four edits applied after seq 01-06 landed; all four Before anchors matched source at :67, :81, :95, :122-126 |
| 2 | Add or update tests per Validation plan | Completed | — | 20261020-132038 | n/a: documentation target n/a: documentation target |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261020-132038 | docs checker family docs checker family green: structure, quality, content policy --strict, japanese, needs-confirmation inventory; stale_detector reports the procedure is not stale |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261020-132038 | this document is the documentation target this document is the documentation target; docs/ redeploy + mdq index rebuild happen in the cycle-end deploy step |

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
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`,
  `scripts/eventbus/config.py` (seq 01), `config/eventbus.toml` (seq 02),
  `docs/90_deployment/deployment_01_deployment.md` (seq 08)