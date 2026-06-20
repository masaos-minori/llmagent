# Implementation: docs/04_mcp-mdq.md (update — add Agent Routing Policy section)

## Goal

Add an "Agent Routing Policy" section to `docs/04_mcp-mdq.md` describing the classifier,
config override, and fallback behavior for MDQ/RAG tool selection.

## Scope

**In:**
- Add `## Agent Routing Policy` section after `## Agent Access Patterns` (line 55)
  and before `## Boundary Enforcement` (if already added) or `## Known Issues`

**Out:**
- Changes to existing sections
- Changes to other documentation files

## Assumptions

- `## Agent Access Patterns` is at line 55 of `docs/04_mcp-mdq.md`
- `## Boundary Enforcement` may have been inserted between Agent Access Patterns and
  Known Issues in a previous step; the new section goes between them or before Known Issues
- `mdq_rag_classifier.py` is described at a module-reference level (no code blocks needed)

## Implementation

### Target file

`docs/04_mcp-mdq.md`

### Procedure

1. Locate the blank line after the `## Agent Access Patterns` section content
2. Insert the following new section before the next `##` heading:

```markdown
## Agent Routing Policy

The agent uses a lightweight classifier (`agent/mdq_rag_classifier.py`) to guide
tool selection between MDQ and RAG based on the user's query.

### Classifier heuristics

Queries containing Markdown-structural terms (e.g., "heading", "outline", "hierarchy",
"section", ".md", "table of contents") are classified as MDQ; all others default to RAG.

### Config override (`mdq_rag_mode`)

Set `mdq_rag_mode` in `config/agent.toml` under `[mcp_servers]`:

| Value | Behavior |
|---|---|
| `"auto"` (default) | Use classifier heuristics |
| `"mdq"` | Force MDQ for all retrieval queries |
| `"rag"` | Force RAG for all retrieval queries |

### Fallback behavior

| Condition | Behavior |
|---|---|
| MDQ selected, mdq-mcp unavailable | Log WARNING; fall back to RAG hint |
| RAG selected, rag-pipeline-mcp unavailable | Return error; no fallback |
| Override mode, forced server unavailable | Return error |

The classifier injects a one-line system prompt hint (~20-40 tokens) before each
LLM turn. The LLM may still deviate; use override mode for deterministic routing.
```

### Details

- Insert the section immediately after `## Agent Access Patterns` content ends,
  before the next `##` heading
- Table format matches existing tables in the file
- No code block needed — the module name is sufficient for operators

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Section present | `grep -n "Agent Routing Policy" docs/04_mcp-mdq.md` | 1 match |
| Config table present | `grep -n "mdq_rag_mode" docs/04_mcp-mdq.md` | >= 1 match |
| Fallback table present | `grep -n "mdq-mcp unavailable" docs/04_mcp-mdq.md` | 1 match |
| Markdown lint | `markdownlint docs/04_mcp-mdq.md` | 0 errors |
| Consistency | All three modes ("auto", "mdq", "rag") documented | Present in table |
