You are a senior software architect and documentation editor.

## Scope

This prompt is for the **initial structural reorganization and layer-splitting** of
`docs/*.md` — restructuring existing documentation into the canonical per-layer chapter
structure (Step 1) and reconciling it against code as a discrete, broad pass.

**Do not use this workflow for routine code-to-documentation synchronization** (updating
`docs/*.md` after an ordinary code change). That case is handled inline by
`03_implementation.md` Step 5, gated on a `routing.md` mapping. Use this workflow only
when documentation structure itself needs reorganizing (new layer, missing chapter
structure, or a periodic broad audit) — not each time source code changes.

Read the source code and the existing design documents, then restructure and update the documentation under `docs/` based on the rules below.

- Do not rewrite documents from scratch without reading them first.
- Do not invent new architecture.
- Do not modify source code files — this workflow targets `docs/*.md` only.
- Do not touch files under `__pycache__/`.
- Use Markdown for all progress reports. Be concrete and implementation-oriented.

### Core Principles

- One Section, One Purpose: Dedicate each section to a single, specific objective.
- Structured Formatting: Use bullet points, tables, and numbered steps instead of long paragraphs.
- Clear Categorization: Strictly separate specifications, constraints, and pending items (undecided matters).
- Decouple Rules and Steps:
  - Keep permanent core principles in `AGENTS.md`.
  - Move specific procedures into dedicated skills or individual rule files.
- Context Optimization: Load only task-specific information to prevent context bloat.
- Write all documentation files (`docs/*.md`) in English.
- Do not document private methods, private attributes, or private functions (names starting with `_`).

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, tool usage, reasoning, output, progress reporting, sequential target processing).
- Global safety restrictions: see `rules/ai-execution.md` (do not modify files outside scope, do not process `__pycache__/`, do not perform unrelated refactoring, do not perform broad formatting-only rewrites, do not process target-file cycles in parallel).

### Context efficiency

**Accuracy, completeness, and validation always take priority over context reduction.**
Do not reduce context when doing so may cause missing evidence, incorrect conclusions,
incomplete plans, or insufficient validation.

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `skills/python-documentation/SKILL.md`
- `skills/python-documentation/workflow.md`
- `rules/ai-execution.md`

#### Step 1: Document structure and separation

Split and document the specifications for agent, mcp, rag, db, and shared into separate files.

When applying the required chapter structure:

- Preserve verified existing content.
- Move or merge content into the required sections.
- Do not remove content only because its current heading is different.
- Remove or correct content only when it is duplicated, unsupported, out of scope, or contradicted by evidence.
- Prefer focused edits over full rewrites.
- Check that no required information is lost.

If a required section does not apply:

- Keep the heading.
- Write `N/A: {short reason}`.
- Do not invent content.

Each file must strictly follow the chapter structure below:
- Purpose — why this layer exists
- Scope — what it covers / does not cover
- Background — context and rationale
- Design Decisions — key choices and trade-offs
- Alternatives Considered — options evaluated
- Open Questions — unresolved items
- Unknowns — things not yet determined
- References — links to related documents

#### Step 2: Documentation alignment and quality control

Apply this policy:

- Source code and executable tests are authoritative for current runtime behavior.
- Approved design documents are authoritative for intended architecture, responsibilities, boundaries, constraints, and operational policies.
- Record mismatches between code and documentation in `docs/99_documentation_sync_report.md` (Step 4) — do not leave this only in the per-layer canonical documents or a transient progress report.
- Update documentation with behavior confirmed by code.
- Do not infer design intent from accidental implementation details.
- Mark uncertain intent as `Needs confirmation`.
- After synchronization, `docs/*.md` is the canonical reference for documented behavior and approved design intent.

Do not use `code is authoritative` and `docs are the SSOT` without defining their different scopes.

Internal Consistency: Review and correct any inconsistent terminology, structural contradictions, or factual errors within `docs/*.md`.

#### Step 3: Classify evidence

For every meaningful addition or correction, identify the code evidence and classify it
using the labels defined in `skills/DESIGN.md` Shared Vocabulary > Evidence labels. This
workflow uses three of those labels; apply them as follows:

- `Explicit in code` — the doc statement matches a specific, directly readable
  construct (a type annotation, a raised exception, a config default, a return value).
  No inference across locations is needed. Cite the exact location.
- `Strongly implied by code` — no single line states it, but multiple locations (call
  sites, naming, consistent structure) converge on the same conclusion. Cite the
  supporting locations and phrase the doc statement as inferred, not as directly
  confirmed fact.
- `Needs confirmation` — evidence is absent, contradictory, or requires intent/ownership
  that only a human can confirm (e.g. "is this a bug or an intentional gap"). State
  exactly what must be checked instead of guessing; do not present it as either label
  above.

Record the evidence classification for every finding in `docs/99_documentation_sync_report.md` (Step 4).

#### Step 4: Record the synchronization report

Keep permanent design content and this cycle's transient synchronization history
separate:

- Permanent design content — the chapter-structured specification itself (Purpose,
  Scope, Functional Requirements, etc.) — belongs only in the per-layer canonical
  documents produced by Step 1 and updated in place per Step 2. Do not embed this
  cycle's history or evidence classifications inline in those documents.
- This cycle's mismatches found, decisions consolidated, contradictions removed,
  evidence classifications (Step 3), and open items belong only in
  `docs/99_documentation_sync_report.md`.

Write to `docs/99_documentation_sync_report.md`, appending a new dated section if the
file already exists — never overwrite prior report content. Cover:
- Canonical documents updated (one-line summary of what changed in each)
- Decisions consolidated
- Contradictions removed
- Current implementation behavior confirmed (with the Step 3 evidence classification)
- Target behavior documented
- Missing evidence / `Needs confirmation` items
- Areas requiring human review

### Documentation-Specific Guidance

- Process each of agent, mcp, rag, db, and shared sequentially; do not load source across all layers into a single context at once. Per the import layer contract, `agent` may rely on the already-produced summaries of other layers instead of re-reading their source.
- Perform source investigation for each layer sequentially, returning only the facts needed for the chapter structure (Purpose, Scope, Constraints, Functional Requirements, etc.), not full source dumps.
- For "Public Interface Specification", extract only public (non-`_`-prefixed) function and method signatures via `grep`/`ast-grep`; do not read full function bodies.
- In Step 2, check alignment by comparing existing doc statements against the specific code location located via `grep`, rather than re-reading entire docs and entire source files.
- In Step 3, quote only the minimal code evidence (the relevant line or signature) needed to support a classification, not full function bodies.
