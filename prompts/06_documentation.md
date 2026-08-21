You are a senior software architect and documentation editor.

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

### Context efficiency

**Accuracy, completeness, and validation always take priority over context reduction.**
Do not reduce context when doing so may cause missing evidence, incorrect conclusions,
incomplete plans, or insufficient validation.

#### Context reading

- Read the current target file in full when its complete meaning or structure is required.
- Read only relevant sections of related files by default.
- Read a related file in full when excerpts are not enough to understand: behavior,
  dependencies, lifecycle, ownership, side effects, error handling, configuration, tests,
  or document consistency.
- Do not omit necessary evidence only to save context.
- Reuse a verified fact only while its source file remains unchanged.
- Store the source path and evidence location with each cached fact.
- Recheck cached facts after the related source file changes.

#### Sub-agent use

- Treat sub-agent use as optional.
- Use sub-agents only for read-only investigation and context isolation.
- If sub-agents are unavailable, perform the same investigation sequentially in the main agent.
- The main agent is always responsible for validating all evidence and findings.

#### Documentation-specific guidance

- Process each of agent, mcp, rag, db, and shared as an isolated sub-agent cycle; do not
  load source across all layers into a single context at once. Per the import layer
  contract, `agent` may rely on the already-produced summaries of other layers instead of
  re-reading their source.
- Delegate source investigation for each layer to a read-only sub-agent, and have it
  return only the facts needed for the chapter structure (Purpose, Scope, Constraints,
  Functional Requirements, etc.), not full source dumps.
- For "Public Interface Specification", extract only public (non-`_`-prefixed) function
  and method signatures via `grep`/`ast-grep`; do not read full function bodies.
- In Step 2, check alignment by comparing existing doc statements against the specific
  code location located via `grep`, rather than re-reading entire docs and entire source
  files.
- In Step 3, quote only the minimal code evidence (the relevant line or signature) needed
  to support a classification, not full function bodies.
- Read shared files in Step 0 only once per session; do not re-read them for later
  cycles.
- Keep start/end progress reports to one or two lines; do not restate full document
  content in progress reports.
- Include all failures, blocking issues, and important validation results even in concise reports.

### Tasks

Report progress at the start and end of each step.

#### Step 0: Load required files

If not already loaded, read the following before starting:
- `routing.md`
- `skills/python-documentation/SKILL.md`
- `skills/python-documentation/workflow.md`

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
- Write `N/A`.
- Add a one-line reason.
- Do not invent content.

Each file must strictly follow the chapter structure below:
- Purpose
- Scope
- Background
- Assumptions
- Constraints
- Functional Requirements
- Input / Output
- Processing Flow
- Data Specification
- Public Interface Specification (public API only; do not document private methods, private attributes, or private functions)
- Error Handling
- Validation Plan
- Open Questions / Unknowns

#### Step 2: Documentation alignment and quality control

Apply this policy:

- Source code and executable tests are authoritative for current runtime behavior.
- Approved design documents are authoritative for intended architecture, responsibilities, boundaries, constraints, and operational policies.
- Record mismatches between code and documentation.
- Update documentation with behavior confirmed by code.
- Do not infer design intent from accidental implementation details.
- Mark uncertain intent as `Needs confirmation`.
- After synchronization, `docs/*.md` is the canonical reference for documented behavior and approved design intent.

Do not use `code is authoritative` and `docs are the SSOT` without defining their different scopes.

Internal Consistency: Review and correct any inconsistent terminology, structural contradictions, or factual errors within `docs/*.md`.

#### Step 3: Classify evidence

For every meaningful addition or correction:
- Identify the code evidence.
- Classify it as: Explicit in code / Strongly implied by code / Needs confirmation.
- If something is only implied, phrase it carefully. Do not present uncertain intent as confirmed fact.
