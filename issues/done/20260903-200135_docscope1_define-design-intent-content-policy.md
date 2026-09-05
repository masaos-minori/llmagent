# Define the docs/ design-intent content policy in skills/DESIGN.md

## Priority
Medium

## Summary
Add a precise, example-grounded content policy to `skills/DESIGN.md` Shared
Vocabulary: five categories of implementation-detail content that `docs/*.md`
documents should not contain (full file trees, per-file one-line descriptions,
class/function-name indices, "this behavior lives in this `.py`" location
mappings, literal port numbers), and five categories of design-intent content
they should contain instead (component responsibility, state each component
owns, allowed dependency direction, reason for process separation, reason for
per-process configuration separation, and design boundaries needing joint
review on change). This issue is policy text only — no tooling, no `docs/*.md`
content changes.

## Background
`skills/DESIGN.md` Shared Vocabulary already establishes related principles
that skills apply when *generating* new documentation: "Avoid
implementation-reference duplication", "No source-code line numbers", "No
concrete configuration values", and "No implementation counts". None of these
names the specific categories this policy targets precisely (a raw ASCII file
tree is not a "line number" or an "implementation count"), so a tool or writer
cannot reliably tell "does this violate policy?" from the current wording
alone.

## Problem
Repository-wide search confirms concrete, current examples of the
remove-categories this policy must name precisely:

- **Full file trees with per-file descriptions**: `docs/01_overview-files-01-build.md`
  through `docs/01_overview-files-06-misc.md` (6 files) consist primarily of
  literal ASCII tree diagrams (`├─`, `│`, `└─`) with a one-line description per
  entry, e.g. `docs/01_overview-files-02-rag.md`'s "## 3. File Structure"
  section.
- **Class/function/method index tables**: e.g.
  `docs/03_rag_02_08_ingestion_pipeline-shared.md`'s "Public Functions" table
  (`| Function | Signature | Description |`), and similar tables in
  `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`,
  `docs/03_rag_02_07_ingestion_pipeline-utils.md`,
  `docs/04_mcp_02_01_endpoints-and-transport.md`, and
  `docs/04_mcp_03_02_tool-registry.md`.
- **Literal port numbers**: e.g.
  `docs/04_mcp_04_02_file-write-file-delete-shell.md`'s section headings
  "## file-write-mcp (Port 8007)", "## file-delete-mcp (Port 8008)",
  "## shell-mcp (Port 8009)".
- **Implementation-location mappings**: e.g.
  `docs/01_overview-files-02-rag.md`'s file tree entries state inline which
  `.py` performs an action (`# Files ingested into DB (moved by
  ingester.py)`).

Without a precisely worded policy naming these categories, neither a future
detection tool (see Dependencies) nor a human writer can reliably distinguish
a violation from legitimate content.

## Reason for Change
Implementation-detail listings go stale the moment the underlying code
changes, and duplicate what `grep`/code/git already answer authoritatively.
`docs/03_rag_05_5-constraints-reference.md`'s own Evidence bullet already
records this failure mode once: a previous version cited
`` config/agent.toml:43 `` and specific hop/page-count values that had already
drifted from the actual `config/crawler.toml` values, requiring a correction
noting "Line number references are deprecated; use section-based references
instead." File trees, per-file descriptions, and location mappings are the
same failure mode at larger scale, and they crowd out the design-intent
content that is genuinely hard to recover from code alone (why components are
separated, what dependency direction is allowed, what design boundaries need
joint review).

## Implementation Intent
Extend `skills/DESIGN.md` Shared Vocabulary with two new named subsections
(or extend an existing one, at the implementer's discretion, provided the
five-and-five category split remains explicit) rather than creating a
disconnected parallel rule set. Each category gets a one-sentence definition
plus a short example drawn from Problem above. Cross-reference `rules/env.md`
Architecture for the canonical dependency-direction/layer content instead of
restating it — that document is already `AGENTS.md` Environment's designated
source for "schema, config reference, service ports."

## Target Files or Areas
- `skills/DESIGN.md` (Shared Vocabulary)

## Required Changes
1. Define the five remove-categories precisely, each with a concrete example:
   full file tree; per-file one-line description embedded in a tree or table;
   class/function/method signature-and-description index table; "this
   behavior is implemented in `{file}`" location-mapping statement; literal
   port number in a heading, table, or prose.
2. Define the five retain-categories precisely: component responsibility
   (Agent, MCP, RAG, EventBus, Shared/DB); state each component owns; allowed
   dependency direction; reason for process separation; reason for
   per-process configuration separation; design boundaries requiring joint
   consideration on change.
3. Add both lists to `skills/DESIGN.md` Shared Vocabulary, extending the
   existing "Avoid implementation-reference duplication" / "No source-code
   line numbers" / "No concrete configuration values" / "No implementation
   counts" principles rather than duplicating them.
4. Cross-reference `rules/env.md` Architecture for dependency-direction
   content instead of restating it.

## Constraints
- Must not touch `rules/env.md`'s content — it remains the canonical, allowed
  location for concrete operational values (schema, config reference, service
  ports) per `AGENTS.md` Environment.
- Do not edit any file under `docs/` in this issue — this issue is policy
  text in `skills/DESIGN.md` only (see Out of Scope).

## Acceptance Criteria
- `skills/DESIGN.md` Shared Vocabulary states both category lists explicitly,
  each with a one-sentence definition and a short example.
- The wording is precise enough that a follow-up detection tool (see
  Dependencies) can implement a pattern/heuristic for each remove-category
  without further clarification.
- The new text cross-references `rules/env.md` Architecture rather than
  restating dependency-direction content.

## Testing Expectations
Not required — this is a documentation/policy-text change with no code or
behavior impact.

## Documentation Impact
Yes — this issue's entire deliverable is the `skills/DESIGN.md` policy
addition described above.

## Out of Scope
- Building any detection tool for the new policy (tracked separately, see
  Dependencies).
- Rewriting any `docs/*.md` document to comply with the new policy.
- Deciding the fate of `tools/check_docs_consistency.py`'s
  `check_port_drift()`/`check_port_range_claim()` checks (tracked separately,
  see Dependencies).

## Dependencies
N/A: none — this issue can start immediately. A follow-up issue (detection
tool implementation) depends on this issue's policy text landing first.

## Unresolved Questions
N/A: none — the category definitions and their grounding evidence are
established in Problem above.

## AI Implementation Instruction
Edit only `skills/DESIGN.md`. Do not edit any file under `docs/`, and do not
implement any detection tool or check function — those are separate,
dependent issues. Keep each category definition to roughly one sentence plus
one example; do not write a long prose essay per category. Stop and ask if a
category's boundary is ambiguous against an existing `skills/DESIGN.md`
principle (e.g. whether a short illustrative port number in a worked example
should be exempted) rather than guessing.
