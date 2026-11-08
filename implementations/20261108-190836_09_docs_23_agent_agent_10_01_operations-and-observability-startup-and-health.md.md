## Goal
Reword one `Key Constraints` bullet in the startup-and-health document so it states the same startup policy without the phrase order the strict COMPAT scan flags (`REQ-002`).

## Scope
**Release unit**: wfaudit012-full

- Covers Plan `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md` row 9 only: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`.

## Assumptions
- Procedure 01 (`implementations/20261108-190836_01_tools_check_compat_shims.py.md`) lands in the same change unit; this line is the only `docs/` finding the 2026-11-08 census found, so no exemption mechanism is introduced (`REQ-002`).
- The scanned text is the line as written: `scripts/agent/audit...`-style exclusions do not apply, and `docs/*.md` files under a `done/` path component are skipped by the checker's file selection — this file is an active document, so it is scanned.
- The claim itself stays true and must stay true: workflow definitions are always loaded at startup, and there is no path that runs a turn without a loaded definition.

## Design decisions
- Reword the sentence instead of deleting it: the constraint is current policy, and the flagged text is the phrase order `direct`+separator+`execution` followed by `fallback` (pattern `direct-execution fallback phrase`, `tools/check_compat_shims.py` L111). Reversing the order — "There is no fallback to direct execution." — states the same policy and matches no pattern.
- Keep the bullet's first two sentences byte-identical and keep the bullet count in `Key Constraints` unchanged (L49-52), so the document's structure and the docs checkers' bullet/table rules are unaffected.
- No new backtick-quoted symbol is introduced, so the `--check-doc-symbols` stage has nothing new to resolve.

## Alternatives considered
- Delete the sentence: rejected — the constraint is load-bearing documentation for the no-fallback startup policy; the plan fixes wording, not policy.
- Add a docs-path exemption to `tools/compat_exceptions.toml`: rejected — the census shows this is the only docs line affected, and the plan adds no exemption mechanism (`REQ-002`, repo rule against speculative code).
- Reword to "Workflow-mode fallback is not supported.": rejected — `workflow_mode field reference` / fallback-phrase patterns make the wording riskier, and it names a removed field vocabulary rather than the behavior.

## Implementation
### Target file
`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure
Replace the last sentence of the second `Key Constraints` bullet (L50).

### Method
Change L50 from

`- Workflow definition files must always be loaded at startup. If they are missing or invalid, startup fails. Direct execution fallback is not supported.`

to

`- Workflow definition files must always be loaded at startup. If they are missing or invalid, startup fails. There is no fallback to direct execution.`

### Details
- L49, L51 and L52 (the Bearer-token, health-probe, and embedding-dimension bullets) stay byte-identical, as does the `## Key Constraints` heading (L47).
- The same page's L37 and L78 sentences about startup failure closing resources are untouched: they name no COMPAT pattern.

## Compatibility considerations
- Documentation-only change: no code, config, or symbol reference changes, and `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` keeps its front matter, keywords, and `Related Documents` sections.
- After this edit the file produces no COMPAT finding in the strict run, which is what keeps the docs scan clean without an exemption (`REQ-002`).

## Security considerations
- No security claim changes: the Bearer-token constraint bullet (L49) and the health-probe failure policy (L51) are untouched.

## Rollback considerations
- Revert the commit restores the original sentence. Rolling this back while procedure 01 stays landed re-opens the `agent_10_01_operations-and-observability-startup-and-health.md:50` finding, so a rollback here must be followed by the census gate re-run.

## Validation plan
- Checker gate: `uv run python tools/check_compat_shims.py --check-removed-names --check-doc-symbols` reports no finding for this file (COMPAT and removed-names stages) and no unresolved doc symbol; the full run exits 0 only after procedures 03-09 and `wfaudit008` have all landed.
- Docs gates for an edited `docs/*.md` file per `routing.md`: `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`, `uv run python tools/check_docs_content_policy.py --strict`, and `uv run python tools/check_docs_consistency.py --domain agent`.
- Content check: `grep -rn "no fallback to direct execution" docs/` shows the reworded bullet once, and `grep -rniE "direct.execution fallback" docs/` returns nothing.
- No test change is required: the sentence is prose, and the startup behavior it describes is covered by the existing startup tests already green at HEAD.

## Completion criteria
- L50 states the startup no-fallback policy in the reversed phrase order, the bullet and section structure are unchanged, and the strict checker plus the docs gates report nothing for this file.

## Out of Scope
- Other bullets in `Key Constraints` and the rest of the document.
- Adding a docs-path exemption mechanism to `tools/compat_exceptions.toml` (`REQ-002`).
- The checker semantics flip and the source-code census fixes (procedures 01-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | one sentence at L50 |
| 2 | Add or update tests per Validation plan | Pending | — | — | no test change: prose-only edit |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | repo-clean gate depends on procedures 03-09 and `wfaudit008` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | this document is the docs procedure |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261107-203225_wfaudit012_shim-checker-case-gap.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084013_wfaudit012_shim-checker-case-gap.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-190836
- **Related target files**: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`
