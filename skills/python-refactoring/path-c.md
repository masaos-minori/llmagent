# Python Refactoring — Path C (Architectural Refactoring)

Load this file only after `workflow.md` Step 2 classifies the current change as Path C
(see `SKILL.md` Routing for the full classification criteria). Path C requires at least
Path B's Step 3/4 tool depth (see `path-b.md`) in addition to everything below.

If a change satisfies any Path C criterion, classify it as Path C even if it also
satisfies a Path B criterion (e.g. an import-boundary change that is a byproduct of a
relocation, merge, split, ownership transfer, or boundary change is Path C, not Path B);
a narrower import-direction fix that is not part of such a structural change remains
Path B.

---

## Architectural Refactoring Requirements (pre-Step 3)

A Path C change requires all of the following before implementation begins:

1. Explicit approval
2. Affected-file scope
3. Current and proposed boundaries
4. Migration strategy
5. Rollback strategy
6. Documentation impact
7. ADR requirement — an ADR MUST exist or be referenced before implementation; this
   requirement does not define the ADR template or process itself (see ADR Requirement
   below)

An unapproved Path C idea is a Proposal only, per the Proposal state defined in
`discovery.md` Discovery Vocabulary (added per
`implementations/20260826-155803_01_prompts_04_refactor.md.md` `REQ-001`); it MUST NOT
be transformed in `workflow.md` Step 6 until it becomes an Approved Change per that same
section's rule that only an Approved Change may be transformed in Step 6, with all seven
items above satisfied and explicit approval given.

**Atomic migration group**: the explicit, enumerated set of files whose changes MUST be
applied and validated together, because no proper subset of them can independently pass
Step 7 validation while the remaining members are unchanged (e.g. relocating a module and
updating every one of its callers). Group membership MUST be declared and included in the
approval above (item 2, affected-file scope) before `workflow.md` Step 3 begins for any
member of the group.

The one-file-at-a-time rule (`workflow.md` Step 1) remains the default for Path A and
Path B, and for ordering independent Path C target files that do not belong to the same
atomic migration group. For an approved atomic migration group, the rule applies to the
group as a single logical unit rather than to each member file individually — one Path
classification, one Step 3-7 preparation/validation/gating pass, and one Completion gate
(`report-template.md`) cover the whole group — while member files are still read and
transformed one at a time in a fixed, declared order; they MUST NOT be transformed in
parallel (`workflow.md` Step 6 Transformation and the Global Safety Restriction against parallel target-file
processing still apply within the group).

Silent expansion of an approved atomic migration group is prohibited. If executing the
group reveals that an additional file must change for the group to remain valid, stop; the
additional file is a new Proposal requiring a new approval cycle for the amended group
before any further transformation. The originally approved group's membership is frozen at
approval time.

---

## Architecture Baseline (Step 4 addendum)

Applies only when the change is classified Path C. Path A and Path B proceed through
`workflow.md` Step 4 exactly as `path-a.md`/`path-b.md` describe, unaffected.

Before any Path C transformation begins (`workflow.md` Step 6), capture all eight of the
following fields:

- **Module ownership**: no established repository command exists for this field
  (verified: no `CODEOWNERS` file, no ownership-registry document, no documented
  ownership-check command anywhere in `rules/`, `routing.md`, or `skills/`). Capture
  manually by direct code inspection, using `rules/env.md` Architecture's six-layer
  diagram (`scripts/{agent,db,eventbus,mcp_servers,rag,shared}/`) as the default
  ownership unit (the owning layer/module directory).
- **Dependency direction**: run `pydeps` (import graph) and `import-linter`/
  `lint-imports` against `.importlinter`'s contracts — the same tools `path-b.md`
  already runs at Path B/C depth — cross-checked against `rules/env.md` Architecture's
  layer diagram.
- **Entry points**: no single established repository command covers all entry-point
  types. Capture manually via `rg "if __name__ == .__main__.":` plus direct inspection
  of `config/agent.toml` service definitions and the relevant MCP server class's
  `http_port` class variable (`scripts/mcp_servers/server.py`-derived modules).
- **Lifecycle ownership**: no established repository command exists for this field
  beyond module-naming convention. Capture manually via `rg` for class names containing
  `Lifecycle` and for `start`/`stop`/`shutdown` method definitions in the affected
  module.
- **State ownership**: reuse `validation.md` Side-Effect Inventory's "Global mutable
  state" item as the baseline record for this field; do not define a second, separate
  capture method.
- **Configuration dependencies**: `rg` against `config/*.toml` and
  `shared/config_loader.py` usages, consistent with `rules/env.md`'s statement that
  `config/agent.toml` is the configuration SSOT.
- **Routing or registration**: `rg "ToolRouteResolver\|tool_names" scripts/shared/` —
  the exact command already named in `workflow.md` Special Cases.
- **Deployment references**: reuse `workflow.md` Step 3's existing "referenced in
  `deploy.sh`" check verbatim; do not define a second deploy-reference check.

Module ownership, entry points, and lifecycle ownership are manual-capture fields with
no established repository tooling — record them explicitly as such rather than
applying an inconsistent ad hoc method across runs.

Do not start a Path C transformation (`workflow.md` Step 6) if any required Architecture
Baseline field is missing or its capture is incomplete.

---

## Architecture Comparison Validation (Step 7 addendum)

Applies only when the change is classified Path C. These eight items MUST be checked
for Path C — they are not optional the way `validation.md` Conditional Validation is;
only their evidence availability, not their requiredness, MAY be `Not run`/`Blocked`.

For each item, re-run the same capture method recorded in Architecture Baseline above
after `workflow.md` Step 6 Transformation, and compare the result against the baseline
recorded before transformation:

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

Report each item as one of `Pass`, `Fail`, `Not run`, or `Blocked`, reusing
`validation.md` Conditional Validation's reporting rule verbatim in spirit: report why
an item was not run, use a repository-defined alternative when available, do not
report a skipped item as passed, report `Blocked` only if the missing check is
required to prove behavior preservation, and otherwise record it as `Not run`.

---

## ADR Requirement (Step 10 addendum)

An ADR MUST be produced when the change is classified Path C. An ADR MAY be produced
for Path B when the change records an important trade-off — a judgment call made by
the AI executing this workflow when choosing to write one; no further gating criteria
are defined here.

ADR content produced by this Requirement follows the repository's existing convention —
`adr-template.md`'s section structure, standardized by
`docs/00_governance_01_documentation-policy.md` "ADR Section Header Standardization"
(canonical header order: Context [Problem, Constraints], Assumptions, Decision,
Rationale, Alternatives Considered, Consequences [Positive/Negative], Invariants,
Verification, Migration, Implementation Notes, Known Deviations, Review Triggers,
Approval, Related Documents, Change History, Completion Checklist), plus the `Status`
field governed by that same document's "ADR Status Definitions"
(`Proposed`/`Accepted`/`Rejected`/`Deprecated`/`Superseded`) — not a separate,
purpose-built field list. This MUST NOT invent a new storage convention, location, or
template; any suggested field with no direct equivalent in the existing convention is
folded into its nearest existing section rather than added as a new top-level header.

`workflow.md`'s existing Allowed file operations rule ("Do not edit documentation
unless explicitly instructed") governs where this ADR content is written: Step 10
MUST produce the ADR content, in the reconciled shape above, inline in the report as
a draft. Creating the file under `docs/adr/ADR-{next-number}-{slug}.md` and registering
it in `docs/adr-index.md`'s existing "ADR List" table and dependency graph happens only
when the user explicitly instructs a documentation update — this Requirement does not
relax or reinterpret that existing rule, it states how the new ADR obligation operates
within it.

Report the ADR's `Status` value and whether the file was actually created under
`docs/adr/` this cycle or remains a draft pending explicit documentation-update
instruction — see `report-template.md` "ADR Status".

---

## Path C Completion Requirements (Step 10 addendum)

The following items apply only when the change is classified Path C; Path A/B
completion (`report-template.md` Completion Gate) is unaffected, and these items are
additive to, not a replacement for, that gate:

- Behavior Lock completed — `workflow.md` Step 4's gate sentence ("Do not proceed to
  Step 6 ... if important behavior is uncovered ..."), unchanged by this Requirement.
- Architecture Baseline completed — Architecture Baseline above.
- Approved scope unchanged — Architectural Refactoring Requirements above's prohibition
  on silent expansion of an approved atomic migration group.
- Dependency direction verified — Architecture Comparison Validation's
  "Before-and-after dependency comparison" and "Architecture-boundary comparison"
  items.
- No new circular dependency — `validation.md` Required Validation's "Import boundary
  evidence" item ("Circular import risk"), cross-checked by Architecture Comparison
  Validation's "Architecture-boundary comparison" item.
- Ownership changes verified — Architecture Comparison Validation's "Ownership
  validation" item.
- Migration completed — Architectural Refactoring Requirements' atomic migration group
  membership, verified by Architecture Comparison Validation's "Migration validation"
  item.
- Rollback strategy recorded or validated — Architectural Refactoring Requirements'
  rollback-strategy pre-implementation checklist item, verified by Architecture
  Comparison Validation's "Rollback validation" item.
- Removed references absent — Architecture Comparison Validation's "Removed-symbol
  reference check" item.
- Documentation impact classified — `discovery.md` Documentation Drift Detection,
  together with Architectural Refactoring Requirements' "Documentation impact"
  pre-implementation checklist item.
- Required ADR completed — ADR Requirement above.
- Path C validation passed — every Architecture Comparison Validation item reports
  `Pass`.
- Findings separated from implemented changes — `discovery.md` Discovery Vocabulary's
  Finding/Candidate/Proposal states do not authorize implementation; only an Approved
  Change may be transformed.

If any item is not satisfied, do not report the task as complete.
