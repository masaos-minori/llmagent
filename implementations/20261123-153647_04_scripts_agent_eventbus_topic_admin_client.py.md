## Goal

Retire the unused agent-side module `scripts/agent/eventbus_topic_admin_client.py` (`EventBusTopicAdminClient`, the admin topics-authorization client) as the maintainer decided on 2026-11-23, together with its only importer, `tests/agent/test_eventbus_topic_admin_client.py`.

## Scope
**Release unit**: eventbus-client-retirement

In scope: deleting `tests/agent/test_eventbus_topic_admin_client.py` first and then `scripts/agent/eventbus_topic_admin_client.py`. The sibling module and the generated artifacts are other procedures of the same release unit.

## Assumptions

- Maintainer decision (2026-11-23, recorded in the Plan): retire both client modules; the EventBus service and NC-003 stay unchanged.
- Verified in this cycle: `rg` over scripts, tests, tools, deploy, config, and .github finds `eventbus_topic_admin_client` only in its own test file and in generated reference text; no runtime component imports it.
- The removed code stays recoverable from Git history (`60aad9290`, `0effc5b08`).

## Design decisions

- Delete the test before the module so no import breaks at any point.
- No shim, alias, or stub is left behind.

## Alternatives considered

Rejected: keeping the module with a note (the maintainer chose retirement).

## Implementation
### Target file
`scripts/agent/eventbus_topic_admin_client.py`

### Procedure
1. Delete `tests/agent/test_eventbus_topic_admin_client.py` (companion).
2. Delete `scripts/agent/eventbus_topic_admin_client.py`.
3. Run the import scan from Validation plan; it must list no match.

### Method
Use `git rm` through the normal edit flow (a plain file removal staged by the commit); do not touch other files.

### Details
- Do not edit generated documents or the manifest here; the regeneration procedures of the same unit own them.
- Run the targeted tests after both deletions land together with the sibling module procedure (release unit).

### Companion test files
- `tests/agent/test_eventbus_topic_admin_client.py`
  - Procedure: delete the file (retired together with its subject)
  - Validation: collection of `tests/agent` succeeds and the import scan lists nothing

### Companion test files
- `tests/agent/test_eventbus_topic_admin_client.py`
  - Procedure: delete the file (retired together with its subject)
  - Validation: collection of `tests/agent` succeeds and the import scan lists nothing

## Compatibility considerations

Removes public classes from the Agent API manifest; nothing else imports them.

## Security considerations

N/A: removes unused client code; no credential handling changes.

## Rollback considerations

Restore the two files from Git history (`git checkout <commit> -- <path>` for the single paths) and revert the commit.

## Validation plan

- `rg "eventbus_subscriber|eventbus_topic_admin_client" scripts tests tools` lists nothing after both module procedures
- `uv run pytest tests/agent -q` collects without import errors
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools` and `PYTHONPATH=scripts uv run lint-imports` stay clean

## Completion criteria

- `scripts/agent/eventbus_topic_admin_client.py` and `tests/agent/test_eventbus_topic_admin_client.py` no longer exist and no file references them.

## Out of Scope

The sibling module, generated artifacts, documents, and the EventBus service.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (retire the two modules and match the documents), `REQ-002` (remove modules, tests, and generated entries)
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111218_gov004_eventbus-client-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-153647
- **Related target files**: `scripts/agent/eventbus_topic_admin_client.py`, `tests/agent/test_eventbus_topic_admin_client.py`
