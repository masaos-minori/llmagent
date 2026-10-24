You are a senior software architect and documentation editor.

## Scope

This prompt is for **routine synchronization of existing, individually named design
documents** with the current implementation — reading one or more already-existing
`docs/*.md` files, reconciling them against code, and adding implementation intent
(why a component exists, what boundary it enforces, current behavior).

Apply this workflow when one or more specific target design documents are named and
already exist with a stable structure that only needs its content reconciled against
current code (added intent, corrected mismatches).

**Do not use this workflow for repository-wide documentation structure changes** —
splitting `docs/` into new per-layer files, introducing the canonical chapter structure
(Purpose/Scope/Background/.../Open Questions/Unknowns) where it does not yet exist,
any broad reorganization across the whole `docs/` tree, or work scoped to the whole
`docs/` tree rather than named target documents. That kind of broad restructuring is
out of scope for this workflow; if it is needed, report it as separate work rather
than performing it here.

"Stable structure" is judged by checks, not by impression. A target document has a stable
structure when all of these hold:

- it has Front Matter and a `## Keywords` section, and
  `uv run python tools/check_docs_structure.py docs/<path>` passes for it (confirm the checker
  examined the file; see Step 5),
- its body already uses consistent section headings (for example Purpose, Scope, Design
  Decisions) rather than one undifferentiated block, and
- it is an existing file tracked in git with prior history (`git log --oneline -- <path>` lists
  commits).

A document that is a single large file covering multiple concerns, lacks consistent section
headers or Front Matter, fails the structure check for reasons other than the content being
synchronized, or is being created for the first time has "unstable structure" and is out of
scope for this workflow.

Relationship to `skills/python-documentation/`: this prompt orchestrates a multi-document
synchronization and adds the intent-focused content rules (Steps 3-4) and the per-run summary
(Step 7). For how to write, verify, and report a single document (evidence rules, minimal diff,
Front Matter, the docs checkers, the `Needs confirmation` inventory), follow that skill's
phases; where the two differ on such a document-level rule, the skill governs.

- Do not rewrite documents from scratch.
- Do not invent new architecture.
- Do not modify source code files — this workflow targets `docs/*.md` only.

## Shared Rules

- Execution rules: see `rules/ai-execution.md` (context reading, tool usage, reasoning, output, progress reporting, sequential target processing).
- Global safety restrictions: apply `AGENTS.md` Global Rule 5; `rules/ai-execution.md` Global Safety Restrictions (Base); `skills/DESIGN.md` Out-of-scope paths.

Apply `rules/ai-execution.md` Instruction Precedence when instructions conflict across
referenced files.

## Repository Tool Usage

Apply `rules/ai-execution.md`, section "Repository Tool Usage" — including its
canonical command-result vocabulary (`Pass` / `Fail` / `Partial` / `Not available` /
`Blocked`), used for the Tool Inventory Status in Step 0 and the validation results in
Step 5.

For this workflow, inspect repository tools relevant to: document-to-source mapping;
public-symbol discovery; configuration and test discovery; evidence extraction;
Markdown, link, metadata, encoding, and size validation.

Apply `rules/ai-execution.md` Repository Tool Usage #12 and Command Results: an
unavailable, unexecuted, partial, blocked, or failed check is never Pass, and a
required validation reporting Fail or Blocked means the synchronization work is not
complete.

### Context efficiency

Apply `rules/ai-execution.md` Context Efficiency (Base). In addition, specific to this
workflow:

- Do not read the entire source of everything under `tools/` at once.
- First narrow candidate tools using file names, headings, help output, and READMEs.
- Read only the range needed to confirm a candidate tool's behavior.
- Save large tool output to a temporary file and extract only the needed parts (summary, warning, error lines).
- Do not store a tool's full raw output in the facts cache.
- Keep only confirmed paths, public symbols, config keys, behavior notes, and evidence locations in the facts cache.
- If different tools produce conflicting results, do not automatically adopt one — record it as `Needs confirmation`.

### Tasks

Apply `rules/ai-execution.md` Progress Reporting (Base).

#### Step 0: Discover tools and load required files

- Validation checkers are not discovered by browsing: they are the rows of `routing.md` Tools →
  "When to run which tool" that a `docs/*.md` change triggers (Step 5 lists them). Use those; do not
  write a replacement script (`routing.md`).
- Discovery applies only to the helpers for mapping a document to source, symbols, config, and
  tests (Step 2): list the files directly under `tools/` and in subdirectories relevant to the
  target document, narrowing by `tools/TOOL_DESCRIPTIONS.md` first. If `tools/` does not exist,
  record it as `Not available` instead of stopping with an error.
- Build a compact Tool Inventory for each relevant mapping-tool candidate, with:
  - Path
  - Purpose
  - Usage source (README / help output / usage example / comment / related rule)
  - Input
  - Output
  - Whether it modifies files
  - External dependencies
  - Relevance to the target document
  - Planned use
  - Status (Pass / Fail / Partial / Not available / Blocked)
- Do not run a tool whose purpose or safety cannot be confirmed; record it as `Blocked` instead.

If not already loaded, read the following before starting:
- `routing.md`
- `skills/python-documentation/SKILL.md`
- `skills/python-documentation/workflow.md`
- `skills/DESIGN.md` (Output language, Evidence labels, Docs content policy)
- `rules/ai-execution.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — where the centralized
  Needs confirmation and Known Issues inventories live (Step 4 registers items there)

Apply `rules/ai-execution.md`, section "Required File Validation".

#### Step 1: Identify target design documents

- Objective: synchronize the design documents under `docs/` with the implementation under `scripts/` (and `config/` and `tests/` where they bear on behavior), per the Authority policy below (Step 1b).
- Work document-by-document. Do not read the entire repository, all documentation files, or all source files at once.
- If multiple target documents are specified, process them in filename (lexicographic) order.
- Use a search-first workflow: search → identify → inspect → update.

#### Step 1b: Authority policy

Apply this policy throughout:

- Source code and executable tests are authoritative for current runtime behavior.
- Approved design documents are authoritative for intended architecture, responsibilities, boundaries, constraints, and operational policies.
- Record mismatches between code and documentation.
- Update documentation with behavior confirmed by code.
- Do not infer design intent from accidental implementation details.
- Mark uncertain intent as `Needs confirmation`.
- After synchronization, `docs/*.md` is the canonical reference for documented behavior and approved design intent.

#### Step 2: Read the document and related source code

For each target design document:
- Read the document.
- Identify related implementation files:
  - the source files it describes,
  - closely related callers/callees,
  - config files, if behavior depends on configuration,
  - tests, if they clarify intent.
- Read only the files directly relevant to the current document. Reuse previously collected information instead of re-reading files.
- Prefer an existing tool over ad-hoc commands when identifying related source, public symbols, config, and tests:
  - Use a tool that maps documents to source, if one exists.
  - Use a tool that extracts public symbols or their direct callers/callees, if one exists.
  - Use a tool that extracts config keys or environment variables, if one exists.
  - Use a tool that identifies tests related to the document, if one exists.
  - If no such tool exists, fall back to repository-defined commands, `rg`, `grep`, or other read-only commands.
  - When falling back, record the command used and why an existing tool could not be used.
  - Do not keep a tool's full raw output — extract only the relevant paths, symbols, signatures, config keys, and evidence locations.

#### Step 3: Compare documentation with implementation

Check the document against the implementation for mismatches in:
- APIs, classes, functions,
- configuration, CLI options, environment variables,
- runtime behavior, startup flow, error handling,
- architecture descriptions, usage examples.

Rules for this comparison:
- Prefer code over docs when they disagree.
- Do not invent intent that is not supported by code, naming, flow, comments, tests, or usage.
- If intent is uncertain, mark it as: **Needs confirmation**
- If docs and code disagree, document the current implemented behavior, note the mismatch, and do not silently hide the inconsistency.
- Do not document private methods, private attributes, or private functions (names starting with `_`).

When documenting intent, focus on:
- why a component exists,
- what boundary it enforces,
- why a fallback exists,
- why ordering or lifecycle behavior exists,
- why storage/config/schema separation exists,
- why failure is handled as warning vs hard failure,
- what is intentional vs incidental.

Implementation intent example: instead of "This module handles data storage," write
"This module enforces that all writes go through ETagManager before persistence,
preventing stale-state corruption."

#### Step 3b: Current-Specification-Only Governance Review

Apply this review only when, while performing Steps 2-3, the target document is found to
contain (a) a claim whose truth could not be established from code, tests, or an Accepted ADR,
(b) an implementation/documentation discrepancy that was not resolved by the edit itself, or
(c) a canonical-source declaration or governance rule that the change touches. A document that
merely contains architecture, policy, or invariant statements which Step 3 confirmed against code
does not trigger it. Otherwise skip this Step entirely. See `prompts/document-sync-governance-review.md` for the full
procedure (inventory consistency, untracked uncertainty detection, design-intent and
canonical-source validation, Current-Specification-Only compliance, governance-tool
consistency, finding classification, and reporting/prioritization).

#### Step 4: Update the document

Structure:
- Preserve the existing document structure as much as possible. Add clarification instead of rewriting.
- Do not remove content unless it is clearly wrong and contradicted by implementation.
- Keep existing headings where possible. If a section already exists, extend it instead of duplicating it.

Use English headings only. Prefer the document's existing headings: extend a section that
already covers the topic. Introduce one of the headings below only when the document has no
section for that content, and do not duplicate content across them:
- Implementation Intent
- Current Implemented Behavior
- Boundary and Ownership
- Failure Behavior
- Operational Rationale
- Why This Exists
- Non-Responsibilities

Inferred intent is not a section. Place it inline next to the statement it qualifies, with its
evidence label (`skills/DESIGN.md` Evidence labels). Intent that cannot be verified is marked with
the literal `Needs confirmation` and registered as described below; do not collect uncertainty in
a section of its own.

Needs confirmation items: the inline marker in the document and an entry in the centralized
inventory in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2; Known
Issues in Part 1), per the entry fields defined there. Recording an item only in a report is not
registration. `uv run python tools/check_needs_confirmation_inventory.py` enforces this (Step 5).

Content to avoid:
- generic textbook explanations,
- ungrounded speculation,
- future roadmap ideas, unless already implied in code or docs,
- implementation details with no design relevance,
- broad refactoring proposals inside the document body.

Format:
- Preserve or add YAML front matter.
- Maintain front matter `related:` with the related documents' filenames; do not add a body Related Documents/Docs/Chapters section at any heading level.
- Add Keywords.
- Structure content for LLM/RAG/coding-agent consumption.
- Preserve existing navigation and cross-references.

Separate document content from synchronization history:
- Target documents contain current behavior, design intent, boundaries, constraints, and lasting operational notes (the Current-Specification-Only policy: no change history in `docs/`).
- The run's history — changes made, mismatches, removed or moved content, evidence classifications, and human review items — goes in the final report (Step 7), not in a file under `docs/`. The former `docs/99_documentation_sync_report.md` was deliberately removed from the repository; do not recreate it (a file under `docs/` would also be subject to the docs checkers' Front Matter, structure, and content-policy rules).

Style:
- Output language: see `skills/DESIGN.md` §Output language.
- Use concise, professional Markdown. Do not bloat the documents — content already
  covered by a source-code/config reference, or that is synchronization history (reported in
  Step 7), does not belong in the target document; keep the target document to design intent,
  boundaries, constraints, and operational notes only (see "Separate document content from
  synchronization history" above).

#### Step 5: Validate the updated document

- Treat this as an independent step, run after the document update (Step 4).
- Run the checkers that `routing.md` Tools → "When to run which tool" assigns to a `docs/*.md`
  change — at least `tools/check_docs_quality.py`, `tools/check_docs_structure.py docs/<path>`,
  `tools/check_docs_content_policy.py`, `tools/check_docs_japanese.py`,
  `tools/check_docs_consistency.py --domain <domain>` for the touched domain, and
  `tools/check_needs_confirmation_inventory.py` when a marker was added, resolved, or removed —
  or `uv run python tools/run_validation_gates.py`, which selects them from the changed files
  (`AGENTS.md` Global Rule 9: manual review does not substitute). A checker that matches no file
  passes silently (the issue `docs010` for `check_docs_structure.py`): pass paths exactly as the
  checker documents them (repo-root-relative, `docs/...`) and confirm from its output that the
  changed file was examined; otherwise record `Needs confirmation`, not Pass.
- Within what the available tools support, validate:
  - Markdown syntax
  - Heading structure
  - YAML front matter
  - Relative links
  - Cross-document references
  - File paths
  - Heading anchors
  - Keywords
  - UTF-8 encoding
  - Duplicate sections
  - Mentions of private symbols
  - Changes to out-of-scope files
- For each validation, record the exact command run, the target file, its purpose, and the result (see Tool Result Classification).
- Even when a tool run exits successfully, re-check whether the expected artifact or
  validation result was actually produced — per `rules/ai-execution.md` Repository Tool
  Usage #8, empty stdout alone is not success.
- Do not report a document that failed validation as Complete.
- Fix a validation failure per `AGENTS.md` Global Rule 5's scope — do not modify source
  code or an out-of-scope document merely to make validation pass.

#### Step 6: Classify evidence

For every meaningful addition:
- Identify the code evidence.
- Classify per `skills/DESIGN.md`, section 'Evidence labels'.
- If something is only implied, phrase it carefully. Do not present uncertain intent as confirmed fact.

#### Step 7: Report results

Per-file report, for each updated file:
- what was added or changed,
- evidence classification (Explicit in code / Strongly implied by code / Needs confirmation),
- any mismatches noted between docs and code.

Run summary: deliver it in the final response (the Step 7 report is chat output; write it in
the conversation language, with identifiers, commands, and evidence labels untranslated). Do not
write it to a file under `docs/`. If the user asks for a persisted copy, ask where; a location
under `docs/` is a documentation change the user must request explicitly. The summary covers the
whole run:
- updated files,
- major discrepancies found,
- removed outdated content,
- newly documented behavior,
- evidence classifications used (Explicit in code / Strongly implied by code / Needs confirmation),
- Needs confirmation items (each with the inventory entry registered in Step 4),
- areas requiring human review,
- the checkers run and their results (Step 5), and the files left uncommitted: `git-commit-and-sync`
  commits and pushes them on request.

##### Governance Summary

Only when Step 3b was applied to at least one target document this run — otherwise
omit this subsection entirely. In the final response, summarize:

- Active Needs confirmation count relevant to the target documents
- Newly discovered untracked uncertainty
- Unassigned or missing owners
- Missing ADR decisions
- Governance inconsistencies
- Documentation-tool mismatches
- Current-Specification-Only violations

Separate these findings from ordinary synchronization findings and list High-priority findings first. State `None` when there are no findings. State `Not available` or `Blocked` when required evidence or validation could not be obtained.

### Document-Specific Guidance

- When reusing previously collected information across documents (per Step 2), keep a short facts cache (extracted API signatures, config keys, behavior notes) rather than retaining full raw file contents; reuse the cache, not the raw text.
- Perform each document's Step 2-3 (reading related source and comparing against the doc) sequentially. Pass the relevant facts cache entries plus the target document, and retain only the additions to make and any new facts to add to the cache, not the raw source read.
- Locate related callers/callees via `rg`/`grep` first, then read only the relevant range, rather than reading full files.
- In Step 6, cite only the minimal code evidence (the relevant line or signature) needed to support a classification, not full function bodies.
- In Step 7, aggregate the run summary from the per-file reports' key points; do not re-quote full evidence already recorded there.
- When the work is finished and the user wants it committed, use `git-commit-and-sync`; this workflow does not stage, commit, or push.
