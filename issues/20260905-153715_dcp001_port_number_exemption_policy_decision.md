# Finalize the port-number exemption boundary for docs/ content-policy cleanup

## Priority
Medium

## Summary
Decide how the `docs/*.md` no-port-numbers content policy (`skills/DESIGN.md`
Docs content policy — remove, "literal port number" category) applies to the
`<!-- AUTO-GENERATED -->` Server Port & Tool Reference table in
`docs/04_mcp_01_tool_ownership_matrix.md` (built by
`tools/generate_reference_table.py --type mcp`), and close the exemption
question that `issues/done/20260903-200135_docscope3_reconcile-port-drift-checks-with-new-policy.md`
left as "keep pending a documented, explicit exemption list." This decision
gates how the per-domain content-migration issues below may treat
auto-generated port tables versus hand-written port mentions.

## Background
`docscope1` (policy definition) and `docscope2` (detection tool) are already
done: `skills/DESIGN.md` Docs content policy — remove/retain is in place, and
`tools/check_docs_content_policy.py` is registered as `GV-021`
(report-only/Warning) in `docs/00_governance_04_documentation-checks.md`.
`docscope3` reviewed `check_port_drift()`/`check_port_range_claim()` in
`tools/check_docs_consistency.py` against the new policy and recorded the
decision "remain active pending a documented, explicit exemption list" —
i.e. the exemption list itself was never produced. This issue is the
follow-up that produces it, now that the content-migration work below is
about to start.

## Problem
Running `uv run python tools/check_docs_content_policy.py` against the
current corpus reports 62 "literal port number" findings (per
`docs/00_governance_04_documentation-checks.md`'s own GV-021 note). Most are
hand-written port mentions in prose, table cells, or section headings (e.g.
`04_mcp_01_tool_ownership_matrix.md`'s "Tool-to-MCP Server Mapping" table
rows such as `file-read-mcp (port 8005)`, and its "### file-read-mcp (port
8005)" Responsibility Boundaries headings) — unambiguously in scope for
removal. But `04_mcp_01_tool_ownership_matrix.md` also ends with a
"## Server Port & Tool Reference (auto-generated)" section, generated and
kept current by `tools/generate_reference_table.py --type mcp` between
`<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments.
`skills/DESIGN.md`'s only stated exemption is "a short, explicitly-labeled
illustrative example" — a machine-generated table of the actual current
ports is not illustrative, so the exemption as currently worded does not
obviously cover it, yet deleting it would make
`tools/generate_reference_table.py --type mcp` (and the `routing.md` guidance
that recommends running it) produce output with no `docs/*.md` destination.

## Reason for Change
Without an explicit decision, the per-domain cleanup issues below would each
have to improvise an answer for the same recurring case (auto-generated
tables vs. hand-written mentions), risking inconsistent treatment across
files. `check_port_drift()`/`check_port_range_claim()` also remain in an
admittedly-provisional state pending exactly this decision — resolving it
here removes a known inconsistency in the repository's own governance
tooling rather than letting each downstream issue re-litigate it.

## Implementation Intent
Choose one of the three options `docscope3` already framed, applied
specifically to the auto-generated table case:
(a) relocate the auto-generated port/tool reference output to a location
outside `docs/*.md` entirely (e.g. keep it as a `--dry-run`-inspectable
generator output only, not committed into a `docs/*.md` file);
(b) exempt the auto-generated, guard-commented block specifically (its
content is mechanically regenerated and self-correcting, unlike hand-written
prose) while still removing every hand-written port mention elsewhere;
(c) leave the current arrangement in place and defer this specific case to
a later decision.
Record the choice and its rationale directly in
`docs/00_governance_04_documentation-checks.md`'s existing Domain
Consistency Check / GV-021 description, matching where `docscope3`'s prior
decision is already recorded.

## Target Files or Areas
- `docs/00_governance_04_documentation-checks.md` (Domain Consistency Check
  description, GV-021 row)
- `docs/04_mcp_01_tool_ownership_matrix.md` (the auto-generated section
  itself, if option (a) or (b) requires a structural change)
- `tools/check_docs_content_policy.py` (add an auto-generated-block exemption
  if option (b) is chosen)
- `tools/check_docs_consistency.py` (`check_port_drift()`,
  `check_port_range_claim()` — final disposition, if this decision resolves
  it)

## Required Changes
1. Decide which of options (a)/(b)/(c) applies to the auto-generated port
   table case, with a one-paragraph rationale.
2. Record the decision in `docs/00_governance_04_documentation-checks.md`
   alongside the existing GV-021 / port-drift-check description.
3. If option (b): add an auto-generated-guard-comment exemption to
   `check_docs_content_policy.py`'s literal-port-number check, with a unit
   test confirming content between `<!-- AUTO-GENERATED -->` /
   `<!-- END AUTO-GENERATED -->` is not flagged while hand-written port
   mentions elsewhere in the same file still are.
4. If option (a): remove the auto-generated section from
   `04_mcp_01_tool_ownership_matrix.md` and confirm
   `tools/generate_reference_table.py --type mcp --dry-run` still functions
   as a standalone inspection command.
5. State explicitly whether this decision also resolves
   `check_port_drift()`/`check_port_range_claim()`'s "pending exemption
   list" status, or whether that remains open for a separate reason.

## Constraints
- Do not modify `rules/env.md` — it remains the canonical location for
  concrete operational values per `AGENTS.md` Environment.
- Do not change `GV-021`'s report-only (Warning) status as part of this
  decision — promotion to default-on is explicitly gated on corpus
  compliance, tracked separately.
- Do not perform the actual hand-written-port-number removal in
  `04_mcp_01_tool_ownership_matrix.md` or any other file here — that is
  `dcp003` below.

## Acceptance Criteria
- `docs/00_governance_04_documentation-checks.md` states an explicit,
  reasoned decision for the auto-generated port table case (not a repeat of
  "pending exemption list").
- If option (b) is chosen, `check_docs_content_policy.py` has a passing unit
  test proving the auto-generated block is exempt and hand-written port
  mentions are still flagged.
- The per-domain content-migration issues below (`dcp003` in particular) can
  proceed without needing to re-decide this question themselves.

## Testing Expectations
If `check_docs_content_policy.py` gains new exemption logic (option b): unit
tests per Required Change 3. If no code changes result (option a or c
without tool changes): `Not required` beyond re-running
`uv run python tools/check_docs_content_policy.py` to confirm no regression.

## Documentation Impact
Yes — this issue's deliverable is the governance-doc decision described
above.

## Out of Scope
- Removing hand-written port numbers from `04_mcp_01_tool_ownership_matrix.md`
  or any other individual file (tracked in `dcp003`).
- Any change to `04_mcp_01_tool_ownership_matrix.md`'s non-port content.
- Re-opening `docscope1`/`docscope2`'s already-settled policy text or tool
  implementation.

## Dependencies
Depends on `docscope1`/`docscope2`/`docscope3` (all in `issues/done/`,
already implemented). `dcp002` through `dcp006` below depend on this issue
only for the parts of their scope that touch auto-generated port-reference
content (concretely: `dcp003`'s treatment of
`04_mcp_01_tool_ownership_matrix.md`'s auto-generated section) — their
hand-written-content cleanup work does not need to wait for this decision.

## Unresolved Questions
N/A: none — the three candidate options and their trade-offs are stated
above; this issue's job is to pick one, not to discover new ones.

## AI Implementation Instruction
Make the decision explicit in writing before touching any code or other
doc. If option (b) is chosen, keep the exemption narrowly scoped to the
guard-commented auto-generated block — do not broaden it into a general
"tables are exempt" rule. Do not edit
`04_mcp_01_tool_ownership_matrix.md`'s hand-written content as part of this
issue. Stop and ask if evidence suggests a fourth option not listed here is
warranted, rather than forcing the decision into one of the three.
