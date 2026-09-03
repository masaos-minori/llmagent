# Replace implementation-detail listings in docs/ with design-intent documentation

## Priority
Medium

## Summary
Establish and enforce a content policy for `docs/*.md`: remove implementation-detail
listings (full file trees, per-file one-line descriptions, class/function-name
indices, "this behavior lives in this `.py`" location mappings, and literal port
number lists) and ensure design-intent content is documented instead (component
responsibilities, state each component owns, allowed dependency directions, reasons
for process separation, reasons for per-process configuration separation, and design
boundaries that need joint review on change). Includes a decision on whether a
detection tool is needed, and its design if so.

## Background
`skills/DESIGN.md` Shared Vocabulary already establishes related principles that
skills apply when *generating* new documentation: "Avoid implementation-reference
duplication", "No source-code line numbers", "No concrete configuration values", and
"No implementation counts". These principles do not fully name the five categories
this request targets (a raw ASCII file tree is not a "line number" or an
"implementation count"), and — more importantly — there is no audit/enforcement
mechanism applying them to the *existing* corpus. Several existing documents predate
these principles and were never revisited against them.

## Problem
Repository-wide search confirms concrete, current violations of the requested
policy:

- **Full file trees with per-file descriptions**: `docs/01_overview-files-01-build.md`
  through `docs/01_overview-files-06-misc.md` (6 files) consist primarily of literal
  ASCII tree diagrams (`├─`, `│`, `└─`) with a one-line description per entry, e.g.
  `docs/01_overview-files-02-rag.md`'s "## 3. File Structure" section.
- **Class/function/method index tables**: e.g. `docs/03_rag_02_08_ingestion_pipeline-shared.md`'s
  "Public Functions" table (`| Function | Signature | Description |`), and similar
  tables in `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`,
  `docs/03_rag_02_07_ingestion_pipeline-utils.md`, `docs/04_mcp_02_01_endpoints-and-transport.md`,
  and `docs/04_mcp_03_02_tool-registry.md`.
- **Literal port numbers**: e.g. `docs/04_mcp_04_02_file-write-file-delete-shell.md`'s
  section headings "## file-write-mcp (Port 8007)", "## file-delete-mcp (Port 8008)",
  "## shell-mcp (Port 8009)", and similar port mentions in
  `docs/04_mcp_04_01_web-search-file-read-github.md`, `docs/04_mcp_04_03_rag-pipeline-and-cicd.md`,
  `docs/04_mcp_04_04_mdq.md`, `docs/04_mcp_04_05_git.md`, `docs/01_overview-arch-02-pipelines.md`,
  `docs/01_overview-files-05-config.md`, and `docs/03_rag_05_1-configuration-reference.md`.
- **Implementation-location mappings**: e.g. `docs/01_overview-files-02-rag.md`'s file
  tree entries themselves state which `.py` performs an action inline (`# Files
  ingested into DB (moved by ingester.py)`).

None of this content states the design information the policy wants retained
(component responsibility, owned state, allowed dependency direction, reason for
process/config separation, cross-cutting design boundaries) — that information is
largely absent or scattered across the corpus today.

Separately, `tools/check_docs_consistency.py` already contains `check_port_drift()`
and `check_port_range_claim()` — automated checks that assume port numbers *are*
documented and verify they match the actual config. A "remove port numbers" policy
directly conflicts with these checks' current premise; this issue must decide their
fate, not leave them silently checking content the new policy says should not exist.

## Reason for Change
Implementation-detail listings go stale the moment the underlying code changes, and
duplicate what `grep`/code/git already answer authoritatively. This is not
theoretical: `docs/03_rag_05_5-constraints-reference.md`'s own Evidence bullet already
records a prior instance of exactly this failure mode — a previous version cited
`` config/agent.toml:43 `` and specific hop/page-count values that had already drifted
from the actual `config/crawler.toml` values, requiring a correction that also noted
"Line number references are deprecated; use section-based references instead." File
trees, per-file descriptions, and location mappings are the same failure mode at
larger scale: they change on every file move, rename, or refactor, and crowd out the
design-intent content (why components are separated, what dependency direction is
allowed, what design boundaries need joint review) that is the harder-to-recover, more
durable information a reader actually needs.

## Implementation Intent
Two parts, kept separate so the (potentially large) content migration does not block
the (small, self-contained) policy definition and tooling:

1. **Define the policy** in `skills/DESIGN.md` Shared Vocabulary, extending the
   existing related principles rather than creating a disconnected parallel rule set.
   State the five remove-categories and the five retain-categories explicitly, each
   with a short example. Cross-reference `rules/env.md` Architecture for the canonical
   dependency-direction/layer content instead of restating it — that document is
   already `AGENTS.md` Environment's designated source for "schema, config reference,
   service ports."
2. **Build a detection tool** (see Required Changes) that scans `docs/*.md` for the
   five remove-categories and reports findings as a report-only (Warning, non-CI-
   blocking) check, following the same rollout pattern `GV-020` already established for
   a comparably corpus-wide finding: land as `Partial`/report-only first, promote to
   default-on once the corpus is compliant. Run the tool once against the current
   corpus and treat its output as the concrete violation inventory that scopes
   whatever follow-up issue(s) perform the actual content rewrites — do not attempt
   the corpus-wide rewrite inside this issue (see Out of Scope).

**On whether a tool is needed**: yes. The violation categories recur across at least
6 dedicated file-tree documents and 5+ more files with index tables or port numbers,
matching this repository's own stated threshold for tooling (`AGENTS.md` Global Rule
7: extract a repeated operation into a script under `tools/` once it recurs three or
more times). A manual one-time sweep would also leave no regression guard — a future
document could reintroduce a file tree or a port number with nothing to catch it,
the same gap `GV-020` was created to close for reintroduced removed-names.

## Target Files or Areas
- `skills/DESIGN.md` (Shared Vocabulary — extend existing principles)
- `docs/00_governance_04_documentation-checks.md` (new Automated Check entry;
  Governance Verification Matrix — new row, next available ID after `GV-020`)
- `tools/check_docs_quality.py` (candidate location for the new check, following its
  existing `@register_core_check` pattern) or a new dedicated script — see Unresolved
  Questions
- `tools/check_docs_consistency.py` (`check_port_drift`, `check_port_range_claim` —
  fate to be decided, see Required Changes)
- `docs/01_overview-files-01-build.md` through `docs/01_overview-files-06-misc.md`,
  and the other files named in Problem — violation sites; **not** edited by this
  issue (see Out of Scope), listed here only as the evidence base for Required
  Change 7's inventory run
- `rules/env.md` — referenced, not modified (see Constraints)

## Required Changes
1. Define the five remove-categories precisely, each with a concrete example drawn
   from Problem above: full file tree; per-file one-line description embedded in a
   tree or table; class/function/method signature-and-description index table;
   "this behavior is implemented in `{file}`" location-mapping statement; literal
   port number in a heading, table, or prose.
2. Define the five retain-categories precisely, matching the request: component
   responsibility (Agent, MCP, RAG, EventBus, Shared/DB); state each component owns;
   allowed dependency direction; reason for process separation; reason for
   per-process configuration separation; design boundaries requiring joint
   consideration on change.
3. Add both category lists to `skills/DESIGN.md` Shared Vocabulary, extending the
   existing "Avoid implementation-reference duplication" / "No source-code line
   numbers" / "No concrete configuration values" / "No implementation counts"
   principles rather than duplicating them.
4. Decide `check_port_drift()`/`check_port_range_claim()`'s fate under the new
   policy (deprecate, narrow to files the policy exempts, or leave pending a
   documented exemption list) and state the decision explicitly — do not leave them
   silently inconsistent with the new policy.
5. Build a detection tool (new registered check function or new script) scanning
   `docs/*.md` for the five remove-categories, reporting file + heading/line-level
   findings.
6. Register the new check in `docs/00_governance_04_documentation-checks.md`'s
   Automated Checks list and Governance Verification Matrix, as report-only
   (Warning), matching the `GV-020` rollout pattern.
7. Run the new tool once against the current `docs/` corpus and record the resulting
   violation inventory (file + category) — this becomes the scoping input for
   follow-up content-migration issue(s), not something this issue resolves itself.

## Constraints
- Must not touch `rules/env.md` — it remains the canonical, allowed location for
  concrete operational values (schema, config reference, service ports) per
  `AGENTS.md` Environment.
- The new detection tool must land as a non-blocking Warning, not a hard CI failure,
  given the current corpus has known, extensive violations (the entire
  `01_overview-files-*` series) — a day-one hard gate would block unrelated PRs.
- Any `Related Documents` / `Document References by Task` cross-reference pointing
  at a file a future content-migration issue guts must be updated in that same
  future change — flagged here as a constraint on that follow-up work, not
  something this issue performs.

## Acceptance Criteria
- `skills/DESIGN.md` Shared Vocabulary states both category lists explicitly, each
  with a short example, and cross-references `rules/env.md` Architecture for
  dependency-direction content instead of restating it.
- A new automated check exists that scans `docs/*.md` and reports every instance of
  the five remove-categories (file tree, per-file description list/table, index
  table, location-mapping statement, literal port number).
- The new check is registered in `docs/00_governance_04_documentation-checks.md`'s
  Automated Checks section and Governance Verification Matrix as report-only.
- Running the new check against the current `docs/` corpus produces a concrete
  violation inventory (file + category) attached to this issue or a named follow-up
  issue.
- `check_port_drift()`/`check_port_range_claim()`'s continued applicability is
  explicitly decided and documented, not left silently inconsistent with the new
  policy.

## Testing Expectations
Unit tests for the new detection check — one test per remove-category, each using a
small fixture document containing that category's pattern, confirming it is
detected, and a fixture containing only retain-category content, confirming it is
not falsely flagged. `check_docs_quality.py`/`check_docs_structure.py` continue to
pass against the (unmodified by this issue) existing corpus, since the new check is
report-only and this issue does not rewrite any `docs/*.md` content.

## Documentation Impact
Yes. This issue's own deliverable is documentation-governance work: extend
`skills/DESIGN.md` Shared Vocabulary with the new policy, and register the new check
in `docs/00_governance_04_documentation-checks.md`. It does not rewrite the
documents the new check will flag — that is explicitly deferred (see Out of Scope).

## Out of Scope
- Rewriting `docs/01_overview-files-*.md`, or any other individual document
  identified by the new tool, to actually apply the retain/remove policy — a large,
  multi-file content-migration effort to be scoped into its own follow-up issue(s)
  once this issue's tool produces the concrete violation inventory.
- Any change to `rules/env.md`'s content.
- Redesigning `rules/env.md` Architecture's dependency-direction diagram — the
  policy only asks other `docs/*.md` documents to reference it, not that it change.

## Dependencies
N/A: none. This issue's own Required Change 7 (running the new tool) produces the
scoping input likely follow-up issues will depend on, but this issue does not depend
on other in-flight work.

## Unresolved Questions
- Whether the new detection check should extend `tools/check_docs_quality.py`
  (following its existing `@register_core_check` pattern) or live in a new dedicated
  script — `check_docs_quality.py` is already close to `skills/DESIGN.md` File Split
  Rule's 400-line trigger threshold; the implementer should decide based on the
  final check's size and how many new check functions this issue ends up adding.
- Whether `check_port_drift()`/`check_port_range_claim()` should be deprecated,
  narrowed to `rules/env.md`-adjacent files only, or kept pending a documented
  per-file exemption list — needs the Required Change 7 violation inventory before
  deciding.
- Whether a short, explicitly-labeled illustrative example (e.g. a worked example
  showing a port number for pedagogical purposes, per `skills/DESIGN.md` "No
  concrete configuration values"'s own carve-out) should be distinguished from a
  policy violation by the new tool, or whether the tool should flag it too and let a
  human confirm the exemption during review.

## AI Implementation Instruction
Implement only `skills/DESIGN.md`'s policy additions, the new detection tool, and its
registration in `docs/00_governance_04_documentation-checks.md`. Do not edit any file
under `docs/` to remove or rewrite content as part of this issue — that is explicit
Out of Scope. Land the new check as report-only (Warning), never a blocking CI
failure, on first landing. After implementing, run the new tool against the current
`docs/*.md` corpus once and report its findings (file + category) as this issue's
completion evidence — do not attempt to fix any of the findings yourself. If the
five category definitions cannot be told apart reliably from legitimate content while
implementing the detection logic, stop and ask rather than guessing a heuristic that
could produce excessive false positives or false negatives.
