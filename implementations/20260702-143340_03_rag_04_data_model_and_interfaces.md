# Implementation Procedure: Fix Duplicate Section Number in `03_rag_04_data_model_and_interfaces.md`

## Goal

Repair the duplicate `## 3.` section number in `docs/03_rag_04_data_model_and_interfaces.md`.
Currently the document has two top-level sections both numbered `3.`:
- Line 158: `## 3. Hit Type Hierarchy`
- Line 346: `## 3. Data Transfer Objects`

The second `## 3.` must be renumbered so that section numbers are unique and sequential throughout the document.

## Scope

**In scope:**
- Renumber the duplicate `## 3. Data Transfer Objects` heading and all its subsections (`### 3.1`, `### 3.2`, `### 3.3`) to the next available number in the document sequence.
- Update any internal cross-references within the same file that cite the affected section numbers.

**Out of scope:**
- Changes to any Python source files.
- Changes to other `docs/` files (cross-file links use filename anchors, not section numbers).
- Changes to CI workflow files.
- Changes to `scripts/checks/check_docs_consistency.py` (covered in a separate implementation document).

## Assumptions

1. The current document heading sequence before the duplicate is: `## 1.`, `## 2.`, `## 3.` (Hit Type Hierarchy), `## 4.`, `## 5.`.
2. The section `## 3. Data Transfer Objects` at line 346 is followed by subsections `### 3.1`, `### 3.2`, `### 3.3` that must also be renumbered.
3. External links from other docs reference sections by filename anchor (e.g. `03_rag_04_data_model_and_interfaces.md`) and not by section number label, so renumbering does not break external links.
4. After renumbering, the document must pass `python scripts/checks/check_docs_consistency.py docs/03_rag_04_data_model_and_interfaces.md` with exit 0.

## Implementation

### Target file

`docs/03_rag_04_data_model_and_interfaces.md`

### Procedure

**Step 1: Confirm the current heading sequence**

Read the full file and list all `##` and `###` headings with their line numbers to determine the correct next section number. The expected existing top-level sequence is:

```
## 1. File Format Specifications        (line 9)
## 2. SQLite Schema (`rag.sqlite`)      (line 87)
## 3. Hit Type Hierarchy                (line 158)   ← first ## 3.
## 4. Public Interfaces (summary)       (line 183)
## 5. Supporting Types                  (line 197)
## 3. Data Transfer Objects             (line 346)   ← duplicate ## 3. — must become ## 6.
```

The next available number is `6`.

**Step 2: Renumber the duplicate section and its subsections**

Apply the following substitutions in the file (exact strings, single occurrence each):

| Old text | New text | Approximate line |
|---|---|---|
| `## 3. Data Transfer Objects` | `## 6. Data Transfer Objects` | 346 |
| `### 3.1 models_data.py` | `### 6.1 models_data.py` | 348 |
| `### 3.2 models_result.py` | `### 6.2 models_result.py` | 417 |
| `### 3.3 types.py` | `### 6.3 types.py` | 490 |

**Step 3: Check for internal cross-references**

Search the file for any links or text that reference the old `§3.1`, `§3.2`, `§3.3` or `section 3` labels within this file. Update any found references to the new numbering.

Command:
```bash
grep -n "3\." docs/03_rag_04_data_model_and_interfaces.md | grep -v "^[0-9]*:.*\`\`\`"
```

### Method

Use the `Edit` tool with exact string matching. Each substitution must be made separately to ensure uniqueness. Do not use `replace_all` unless the old string is guaranteed to appear only once.

### Details

- The heading `## 3. Hit Type Hierarchy` at line 158 is the canonical `## 3.` — it must not be changed.
- The heading `## 3. Data Transfer Objects` at line 346 is the erroneous duplicate — it becomes `## 6.`.
- Subsections `### 3.1`, `### 3.2`, `### 3.3` under line 346 belong to the "Data Transfer Objects" section and must also be updated to `### 6.1`, `### 6.2`, `### 6.3`.
- Note: section `## 5. Supporting Types` also has subsections named `### 5.1`, `### 5.2`, ... `### 5.7`. These are unaffected.
- The file currently has no table of contents or anchor links to section numbers, so no TOC update is needed.

## Validation Plan

| Check | Command | Expected outcome |
|---|---|---|
| Checker passes on this file | `python scripts/checks/check_docs_consistency.py docs/03_rag_04_data_model_and_interfaces.md` | Exit 0, 0 issues |
| Full RAG docs regression | `python scripts/checks/check_docs_consistency.py` | Exit 0, 0 issues across all RAG docs |
| No remaining duplicate `## 3.` | `grep -n "^## 3\." docs/03_rag_04_data_model_and_interfaces.md` | Exactly one match (line 158) |
| New `## 6.` heading exists | `grep -n "^## 6\." docs/03_rag_04_data_model_and_interfaces.md` | Exactly one match (the renamed section) |
