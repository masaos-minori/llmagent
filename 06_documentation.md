# Core Principles

- One Section, One Purpose: Dedicate each section to a single, specific objective.
- Structured Formatting: Use bullet points, tables, and numbered steps instead of long paragraphs.
- Clear Categorization: Strictly separate specifications, constraints, and pending items (undecided matters).
- Decouple Rules and Steps:
  - Keep permanent core principles in `~/llmagent/AGENTS.md`.
  - Move specific procedures into dedicated "Skills" or individual rule files.
- Context Optimization: Load only task-specific information to prevent context bloat.
- Write all documents in Japanese.

[tasks]
Restructure all files under `~/llmagent/docs/*.md` based on the following rules:

1. Progress Tracking
- Real-Time Updates: Show your progress continuously while working on the tasks.

2. Document Structure & Separation

- Split and document the specifications for agent, mcp, rag, db, and shared into separate files.
- Each file must strictly follow the chapter structure below:
  - Purpose
  - Scope
  - Background
  - Assumptions
  - Constraints
  - Functional Requirements
  - Input / Output
  - Processing Flow
  - Data Specification
  - Public Interface Specification
  - Error Handling
  - Validation Plan
  - Open Questions / Unknowns

3. Documentation Alignment & Quality Control

- The documentation (`~/llmagent/docs/*.md`) serves as the Single Source of Truth (SSOT).*
  - Code vs. Doc Alignment: If there are any discrepancies between the actual program implementation and the descriptions in `~/llmagent/docs/*.md`, update `~/llmagent/docs/*.md` to reflect the correct, intended behavior.
  - Internal Consistency: Review and correct any inconsistent terminology, structural contradictions, or factual errors within `~/llmagent/docs/*.md`.

4. Update `~/llmagent/routing.md` to align with the restructured documents.

5. Create a Git commit.

6. End the task.
