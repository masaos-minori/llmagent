# Python Refactoring — Path C (Architectural Refactoring)

Load this file only after `workflow.md` Step 2 classifies the current change as Path C
(see `SKILL.md` Routing for the full classification criteria, including the Path C/Path B
tie-break rule). Path C requires at least Path B's Step 3/4 tool depth (see `path-b.md`)
in addition to everything below.

---

## Architectural Refactoring Requirements (pre-Step 3)

A Path C change requires all of the following before implementation begins:

1. Explicit approval
2. Affected-file scope
3. Current and proposed boundaries
4. Migration strategy
5. Rollback strategy
6. Documentation impact
7. ADR requirement — an ADR MUST exist, be referenced, or be presented as an inline
   draft (ADR Requirement below) and approved together with this checklist before
   implementation; this requirement does not define the ADR template or process itself

Until all seven items are satisfied and explicit approval is given, a Path C idea is a
Proposal only (`discovery.md`) and MUST NOT be transformed in `workflow.md` Step 6.

**Atomic migration group**: the explicit, enumerated set of files whose changes MUST be
applied and validated together, because no proper subset of them can independently pass
Step 7 validation while the remaining members are unchanged (e.g. relocating a module and
updating every one of its callers). Group membership MUST be declared and included in the
approval above (item 2, affected-file scope) before `workflow.md` Step 3 begins for any
member of the group.

One-file-at-a-time (`workflow.md` Multi-file processing) still applies to Path A/B and to
independent Path C files outside a group. An approved group is one logical unit: one Path
classification, one Step 3-7 pass, one Completion gate (`report-template.md`); its members
are still transformed one at a time in a fixed, declared order, never in parallel.

Membership is frozen at approval time. If an additional file turns out to be needed, stop:
it is a new Proposal requiring a new approval cycle for the amended group before any
further transformation.

---

## Architecture Baseline (Step 4 addendum)

Path C only. Before any Path C transformation (`workflow.md` Step 6), capture all eight fields:

- **Module ownership**: manual capture (no `CODEOWNERS`, ownership registry, or check
  command exists). Inspect the code; the default ownership unit is the owning layer/module
  directory of `rules/env.md` Architecture's six-layer diagram
  (`scripts/{agent,db,eventbus,mcp_servers,rag,shared}/`).
- **Dependency direction**: `pydeps` and `PYTHONPATH=scripts uv run lint-imports`
  (`.importlinter` contracts), as in `path-b.md`, cross-checked against `rules/env.md`
  Architecture's layer diagram.
- **Entry points**: manual capture: `rg "if __name__ == .__main__.":`, plus `config/agent.toml`
  service definitions and the MCP server class's `http_port` class variable
  (`scripts/mcp_servers/server.py`-derived modules).
- **Lifecycle ownership**: manual capture: `rg` for class names containing `Lifecycle` and for
  `start`/`stop`/`shutdown` method definitions in the affected module.
- **State ownership**: `validation.md` Side-Effect Inventory's "Global mutable state" item;
  MUST NOT define a second capture method.
- **Configuration dependencies**: `rg` against `config/*.toml` and `shared/config_loader.py`
  usages (`config/agent.toml` is the configuration SSOT, `rules/env.md`).
- **Routing or registration**: `rg -ln "RuntimeToolRegistry|ToolRouteResolver" scripts/`
  (`workflow.md` Special Cases; plain `|`, since ripgrep treats `\|` as a literal pipe).
  `tool_names` is not routing evidence (`RuntimeToolRegistry` is the sole authority); a change
  to that key belongs to Configuration dependencies.
- **Deployment references**: `workflow.md` Step 2's deploy-reference search, verbatim; MUST NOT
  define a second deploy-reference check.

Record the three manual-capture fields as such. A zero-match `rg` is evidence of absence
only after confirming it searched the intended scope (`rules/ai-execution.md` Repository
Tool Usage #8). MUST NOT start a Path C transformation (`workflow.md` Step 6) while any
field is missing or incomplete.

---

## Architecture Comparison Validation (Step 7 addendum)

Path C only. All eight items are required (unlike `validation.md` Conditional Validation);
only evidence availability may be `Not run`/`Blocked`. After Step 6, re-run each item's
Architecture Baseline capture method and compare with the pre-transformation baseline:

- **Before-and-after dependency comparison** — compares the dependency direction field.
- **Architecture-boundary comparison** — compares the dependency direction field,
  cross-checked against `.importlinter` contracts and `rules/env.md`'s layer diagram.
- **Ownership validation** — compares the module ownership and state ownership fields.
- **Migration validation** — verifies every declared atomic migration group member (see
  Architectural Refactoring Requirements above) was transformed and no partial-migration
  state remains.
- **Rollback validation** — verifies the rollback strategy declared in that same
  pre-implementation checklist is actually exercisable, not merely stated.
- **Route, tool, or plugin registration comparison** — compares the routing or
  registration field.
- **Configuration and deployment comparison** — compares the configuration
  dependencies and deployment references fields.
- **Removed-symbol reference check** — a repository-wide (not target-file-scoped) `rg`
  search for old symbol names, extending `workflow.md` Step 6's "no legacy symbol names
  remain" rule and Step 9's equivalent check beyond the target file or migration group
  to the whole repository.

Report each item as `Pass`, `Fail`, `Not run`, or `Blocked` per `validation.md` Conditional
Validation's reporting rule (never report a skip as passed).

---

## ADR Requirement (Step 10 addendum)

An ADR MUST be produced when the change is classified Path C. An ADR MAY be produced
for Path B when the change records an important trade-off — a judgment call made by
the AI executing this workflow when choosing to write one; no further gating criteria
are defined here.

ADR content follows the existing convention: `adr-template.md`'s section structure
(`docs/00_governance/governance_01_documentation-policy.md` "ADR Section Header
Standardization" holds the canonical header order) and the `Status` values of that document's
"ADR Status Definitions" (`Proposed`/`Accepted`/`Rejected`/`Deprecated`/`Superseded`). MUST
NOT invent a new storage convention, location, template, or top-level header; fold any extra
field into the nearest existing section.

Per `workflow.md` Allowed file operations, the ADR is presented inline as a draft with the
pre-implementation approval request (item 7 above) and its final state is reported inline in
Step 10. Creating `docs/10_adr/adr_02_{group}_{next-number}_{group-word}-{slug}.md` (group
number and word from `docs/10_adr/adr_00_document-guide.md`) and registering it in
`docs/10_adr/adr_01_index.md`'s "ADR List" table and dependency graph happen only on an
explicit documentation-update instruction.

Report the ADR's `Status` value and whether the file was actually created under
`docs/10_adr/` this cycle or remains a draft pending explicit documentation-update
instruction — see `report-template.md` "ADR Status".

---

## Path C Completion Requirements (Step 10 addendum)

Path C only; additive to `report-template.md` Completion Gate. MUST NOT report completion
while any row is unsatisfied.

| Requirement | Satisfied by |
|---|---|
| Behavior Lock completed | `workflow.md` Step 4 gate |
| Architecture Baseline completed | Architecture Baseline above |
| Approved scope unchanged | no silent group expansion (Architectural Refactoring Requirements) |
| Dependency direction verified | Comparison items "Before-and-after dependency" and "Architecture-boundary" |
| No new circular dependency | `validation.md` "Import boundary evidence" (Circular import risk) plus "Architecture-boundary" |
| Ownership changes verified | Comparison item "Ownership validation" |
| Migration completed | group membership, verified by "Migration validation" |
| Rollback strategy recorded or validated | checklist item 5, verified by "Rollback validation" |
| Removed references absent | Comparison item "Removed-symbol reference check" |
| Documentation impact classified | `discovery.md` Documentation Drift Detection plus checklist item 6 |
| Required ADR completed | ADR Requirement above |
| Path C validation passed | every Comparison item reports `Pass` |
| Findings separated from implemented changes | only an Approved Change is transformed (`discovery.md`) |
