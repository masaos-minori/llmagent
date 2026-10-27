## Goal

Add an additive subsection to `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` stating the all-or-nothing apply guarantee of the reload subcommand introduced by this Plan: when a reloadable field is invalid, the whole reload is rejected and the live config is left byte-for-byte unchanged with services not re-synced, rather than applying some sections and skipping others. The subsection sits with the existing change-classification discussion and does not alter any existing section.

## Scope

- **In-Scope** (`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` only):
  - Insert one new subsection under the Design Intent area describing the all-or-nothing apply behavior and the failure outcome (live config unchanged, no service re-sync, actionable error naming the failing field).
  - Preserve the front matter, existing headings, cross-references, and the Change Classification table.
- **Out-of-Scope**:
  - The source reorder (`scripts/agent/services/config_reload.py`, row 01) and the prepare/apply split (`scripts/agent/services/config_section_reload.py`, row 02).
  - The regression tests (row 03).

## Assumptions

- The doc is an existing canonical source under `docs/23_agent/`; edits must preserve its front matter and heading hierarchy.
- The all-or-nothing guarantee concerns the reloadable subset of settings: among the fields that reload subcommand can apply, either all valid ones apply together or, if any reloadable field fails validation, none are applied. Startup-only fields remain detected-but-not-applied as documented today.
- Content policy forbids implementation-detail warnings that point away from a canonical source; the subsection stays at the behavioral-contract level and references the error surface rather than internal phases or flags.

## Design decisions

- **Additive subsection, no rewrite.** Insert a new `###` subsection titled "Apply Atomicity" immediately after the existing "Change Classification" table within "## Design Intent", so it reads as part of the classification discussion without altering any existing section.
- **Contract-level language.** State the observable behavior (what happens on success, on a single invalid field, and on the failure signal) without embedding method names, line numbers, or internal phase names.
- **Reconcile with "as much as possible".** The existing "Role of reload subcommand" describes applying reloadable changes; the new subsection narrows that to the atomic guarantee: the reloadable set is applied atomically, so a single invalid reloadable field yields zero partial application.

## Alternatives considered

- **New standalone doc.** Rejected: `docs/00_index.md` maps the CLI chapter so the reload apply behavior belongs with the existing hot-reload classification doc, not as a sibling.
- **Fold it into the Change Classification table.** Rejected: the table lists categories per output tag; the atomicity guarantee is a cross-cutting apply rule, not a category, and would not fit the table shape.

## Implementation

### Target file

`docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` (existing; extended)

### Procedure

1. Open `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` and locate the "### Change Classification" table near the end of the "## Design Intent" area.
2. Insert a new "### Apply Atomicity" subsection directly after that table and before the "## Responsibility Boundary" heading.
3. Write the subsection to cover exactly three points: (a) successful reload applies every reloadable change together; (b) a single invalid reloadable field rejects the whole reload, leaving the live config byte-for-byte unchanged and services unre-synced; (c) the failure is reported as an actionable error that names the failing field, with no partial application.
4. Confirm the front matter, existing headings, cross-references, and the Change Classification table are unchanged.
5. Run the doc validation sequence (`routing.md`).

### Method

The current doc orders the Design Intent area as: "### Role of reload subcommand", then "### Change Classification". The new subsection slots between the table and the next top-level "## Responsibility Boundary" heading, preserving the existing hierarchy.

Proposed subsection text (adapt wording; keep it contract-level):

```
### Apply Atomicity

The reloadable set of settings is applied atomically. A successful reload applies
every reloadable change together; there is no partial application.

- On a single invalid reloadable field, the entire reload is rejected: the live
  configuration is left byte-for-byte unchanged, no service is re-synced, and the
  failure is reported as an actionable error that names the offending field.
- This differs from startup-only settings, which are detected but never applied by
  the reload subcommand regardless of validity.
- Restart remains required for the "Requires restart" category; atomicity governs
  only the reloadable fields applied within a single reload.
```

### Details

- **`REQ-001` / `REQ-003`:** the subsection states the all-or-nothing apply behavior and the failure outcome (live config unchanged, no service re-sync, actionable error naming the failing field).
- **Backward compatibility:** the Change Classification table, the role description, and all existing sections are unchanged; the new subsection is purely additive.

## Compatibility considerations

- Additive subsection; front matter, headings, and existing cross-references preserved. No change to sibling docs.

## Security considerations

- Documentation-only; no new input surface or secret handling.

## Rollback considerations

- Revert the doc edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| structural integrity | Format / headings / fences / front matter | `uv run python tools/check_docs_quality.py` | Clean |
| structure | File size, H1 count, front matter, Related Docs, link reachability | `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md` | Clean |
| content policy | No implementation-detail warnings pointing away from canonical source | `uv run python tools/check_docs_content_policy.py --strict` | Clean |
| domain consistency | Doc claims match `scripts/` and `config/agent.toml` | `uv run python tools/check_docs_consistency.py --domain agent` | Clean |

## Completion criteria

- The doc has an additive "### Apply Atomicity" subsection covering the successful-all, single-invalid-field-rejects-all, and actionable-error-failure behaviors, clearly scoped to the reloadable set.
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, and `check_docs_consistency.py --domain agent` all pass clean.

## Out of Scope

- Source reordering (`scripts/agent/services/config_reload.py`, row 01; `scripts/agent/services/config_section_reload.py`, row 02).
- The regression tests (row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Prepare/apply split (row 02) | Pending | — | — | Dependency |
| 2 | Two-phase reorder (row 01) | Pending | — | — | Dependency |
| 3 | Regression tests (row 03) | Pending | — | — | Dependency |
| 4 | Hot-reload doc (this row) | In Progress | — | — | REQ-001, REQ-003 |
| 5 | Run validation sequence | Pending | — | — | Doc checkers |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: `issues/20261026-224903_config001_make-config-reload-atomic.md`
- **Source plan**: `plans/20261027-073638_config001_make-config-reload-atomic.md`
- **Generated at**: 20261027-113958
- **Related target files**: `docs/23_agent/agent_07_06_cli-and-commands-hot-reload.md`
