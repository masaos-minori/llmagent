Generated at: 20261124-093930

# Regenerate references and run cross-document validation for the ADR and memory documentation changes

## Priority
Low

## Summary
After the substantive ADR and documentation changes, regenerate all affected ADR and API reference content, remove obsolete current-specification terminology, and run the complete documentation and ADR validation suite with saved evidence.

## Background
Source: `memo-issue.md`. ADR and documentation changes here are tied to generated guarded blocks, the authority graph, invariant matrix, API manifests (`registry/manifests/`), canonical-source declarations (`config/documentation_canonical_sources.toml`), internal links, and source/document consistency checks. The final pass follows issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md, issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md, and issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md.

## Problem
Correct prose changes can still leave the repository inconsistent when generated output and cross-document references are stale. The redesign removes terms and contracts that may remain scattered across current specifications, tests, examples, generated references, and operations guidance, and historical records must be told apart from obsolete current text.

## Reason for Change
Non-blocking consistency work; its timing is fixed only by its dependence on the three substantive issues.

## Implementation Intent
Make generated references reflect the approved model, remove obsolete current-specification terminology without rewriting historical evidence, detect broken paths, nonexistent test citations, duplicate authority, and stale generated content, and finish with reproducible validation evidence.

## Target Files or Areas
- `docs/10_adr/adr_01_index.md`, `config/adr_authority.toml`, `config/documentation_canonical_sources.toml`
- `registry/manifests/` (`eventbus_api.yaml`, `memory_api.yaml`, `agent_api.yaml` among others) and the generated EventBus and Agent memory reference documents
- `tools/generate_reference_table.py`, `tools/generate_adr_authority.py`

## Required Changes
- [ ] Regenerate the ADR authority graph, guarded ADR index sections, and invariant verification matrix; update the EventBus API manifest and the Agent memory/reference manifest and regenerate their references; do not edit generated blocks directly.
- [ ] Remove JSONL-related functions, metrics, and APIs from generated references; add approved retention, health, replay-floor, Repository Context, and Episodic Memory symbols only after their source or implementation issue is authoritative.
- [ ] Search for Agent Memory JSONL terms (`JsonlMemoryStore`, `import_from_jsonl`, `memory_jsonl_dir`, `/memory`, memory rebuild, memory prune, pin/unpin, Semantic Memory, User Semantic), EventBus JSONL terms (`events.jsonl`, `eventbus_jsonl_append_failure_total`, JSONL append failure, JSONL replica, SQLite/JSONL comparison, JSONL rebuild), and `4DB`, `four-database`, `SQLite 4DB separation`.
- [ ] Classify each hit as current specification, historical record, archived issue, migration record, test fixture, or removed-name check; correct obsolete terms only in current specifications and preserve historically accurate records.
- [ ] Run Markdown lint, internal-link and path validation, canonical-source conflict checks, the ADR structure/authority/reference/preservation/invariant-matrix checks, generated-reference drift checks, CLI definition/help/completion/documentation consistency checks, EventBus documentation/config/source consistency checks, and DB-separation documentation and test validation; confirm all cited files and test nodes exist; save the commands and results as pull request evidence.

## Constraints
- Historical and archived records (for example under `issues/done/`, `plans/done/`) are not rewritten.
- New symbols are added to generated references only once authoritative.

## Acceptance Criteria
- [ ] Removed symbols do not appear in generated current references; new approved symbols appear under the correct owner module.
- [ ] Generated ADR content matches the authority configuration.
- [ ] No obsolete term remains in current specifications; historical and archived records remain accurate.
- [ ] No nonexistent path, configuration key, function, or test node is cited.
- [ ] All required documentation, ADR, authority, generated-reference, and link checks pass, and validation evidence is attached to the pull request.

## Testing Expectations
Documentation-only validation: `uv run python tools/generate_reference_table.py --check`, `uv run python tools/check_docs_consistency.py --domain eventbus` and `--domain agent`, the five ADR checkers, `uv run python .github/run_cited_adr_tests.py`, `uv run pre-commit run --all-files`, and the checkers in `rules/tool-gates.md`.

## Documentation Impact
Yes. Generated sections of the ADR index and the EventBus and Agent references; terminology corrections in current specifications. Record the classification of each searched term hit.

## Out of Scope
- Substantive ADR or documentation rewrites (owned by issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md, issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md, issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md).
- Rewriting historical or archived records.

## Dependencies
- Depends on issues/20261124-093927_adrdoc001_adr-eventbus-memory-amendment.md, issues/20261124-093928_adrdoc002_eventbus-docs-sqlite-retention.md, and issues/20261124-093929_adrdoc003_agent-memory-docs-episodic.md.

## Unresolved Questions
- `不明`: which CI workflows beyond the documented gates run the documentation, ADR, and generated-reference checks (workflow files not read in this pass).
- `不明`: the complete documentation-check configuration to run as a suite.

## AI Implementation Instruction
Run the generators and checkers; do not edit generated blocks by hand. Change current-specification text only, never historical records. Do not implement code. Stop and report if a dependency issue is unresolved.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261124-093930
- **Related target files**: `docs/10_adr/adr_01_index.md`, `config/adr_authority.toml`, `config/documentation_canonical_sources.toml`, `registry/manifests/eventbus_api.yaml`, `registry/manifests/memory_api.yaml`, `registry/manifests/agent_api.yaml`, `tools/generate_reference_table.py`, `tools/generate_adr_authority.py`
