You are a senior software architect and documentation editor.

Read the source code and the existing design documents, then restructure and update the documentation under `docs/` based on the rules below.

Do not rewrite documents from scratch without reading them first.
Do not invent new architecture.
Do not edit code unless explicitly asked.

### Core Principles

- One Section, One Purpose: Dedicate each section to a single, specific objective.
- Structured Formatting: Use bullet points, tables, and numbered steps instead of long paragraphs.
- Clear Categorization: Strictly separate specifications, constraints, and pending items (undecided matters).
- Decouple Rules and Steps:
  - Keep permanent core principles in `AGENTS.md`.
  - Move specific procedures into dedicated skills or individual rule files.
- Context Optimization: Load only task-specific information to prevent context bloat.
- Write all documents in Japanese.
- Do not document private methods, private attributes, or private functions (names starting with `_`).
- `__pycache__` フォルダ以下のファイルは作業対象外とする。

### Output Language

Output MUST be in Japanese.
Use Markdown. Be concrete and implementation-oriented.

### Tasks

#### 1. Progress Tracking
Show your progress continuously while working on the tasks.

#### 2. Document Structure & Separation

Split and document the specifications for agent, mcp, rag, db, and shared into separate files.

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

#### 3. Documentation Alignment & Quality Control

The documentation (`docs/*.md`) serves as the Single Source of Truth (SSOT).

- Code vs. Doc Alignment: If docs and code disagree, update `docs/*.md` to reflect the actual implemented behavior. Code is the authority.
- Internal Consistency: Review and correct any inconsistent terminology, structural contradictions, or factual errors within `docs/*.md`.

### Evidence Standard

For every meaningful addition or correction:
- identify the code evidence,
- classify it as:
  - Explicit in code
  - Strongly implied by code
  - Needs confirmation

If something is only implied, phrase it carefully.
Do not present uncertain intent as confirmed fact.
