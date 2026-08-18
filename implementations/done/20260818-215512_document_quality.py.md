## Goal

Standardize terminology and repair documentation quality defects by establishing a terminology glossary, correcting Markdown quality issues, managing links and metadata, stabilizing references, and implementing validation in CI.

## Scope

**In-Scope:**
- Create a terminology glossary; standardize terms across Agent, EventBus, Ingestion, Shared/DB metadata, Canonical-Source, and Known Issue/Needs Confirmation domains; use preferred English and Japanese forms.
- Correct typographical and encoding errors; standardize table-heading language; repair broken code fences; ensure dates follow ISO 8601.
- Deduplicate "Related Documents" lists; standardize "Part" link representations; remove or consolidate empty "Keywords" sections.
- Replace unstable line-number references with stable symbols, configuration keys, or test identifiers.
- Implement Markdown linting and link validation in CI; ensure all titles, filenames, source references, and dates are valid.

**Out-of-Scope:**
- Changes to existing MCP server implementations unless required by the unified policy.
- Changes to deployment infrastructure beyond what's needed for security enforcement.
- Changes to other systems' integration points (only internal security architecture).

## Assumptions

- The project already has some governance documents (e.g., `00_governance_03_evidence-labels.md`, `00_governance_07_needs-confirmation-inventory.md`, `00_governance_04_known-issues-template.md`) but they're inconsistently applied (verify current implementation against each claim).
- Evidence blocks need to be standardized across all documentation (check current evidence block usage).
- Uncertainty markers need to be extracted into a central inventory (check current uncertainty marker usage).
- Known issues need to follow a common template (check current known issues format).

## Design decisions

- Create a single terminology glossary — eliminates ambiguity and makes cross-area communication possible.
- Use stable identifiers (symbols, config keys, test refs) instead of line numbers — survives code changes.
- Implement CI validation for Markdown quality — catches regressions automatically.
- Standardize date format to ISO 8601 — enables consistent sorting and parsing.

## Alternatives considered

- Keep terminology per-area — rejected because it causes inconsistency and makes cross-area communication difficult.
- Leave line-number references in place — rejected because they become invalid when code changes.
- Leave Markdown quality unvalidated — rejected because drift between docs and standards is costly.

## Implementation

### Procedure

#### Part A: Create terminology glossary

1. Search for existing terminology definitions:
   ```bash
   rg -n "glossary\|用語.*定義\|term.*definition" docs/
   ```
2. Define a unified terminology glossary:
   ```markdown
    ## Terminology Glossary
    
    | Term | Preferred Form | Alternative Forms | Notes |
    |------|---------------|-------------------|-------|
    | Event Bus | EventBus | event bus, event-bus | CamelCase as proper noun; use "Event Bus" (with space) in Japanese text |
    | Message Queue | MQ | message queue, msg-queue | Abbreviation: MQ; not currently used in this project |
    | Schema Registry | Schema Registry | schema registry | Proper noun; used sparingly in this project |
    | Needs Confirmation | Needs Confirmation | Needs confirmation, 要確認, Need Confirmation, 未決事項 | Abbreviation: NC; always capitalize both words in English |
    | Known Issue | Known Issue | Known Issues, 既知の問題, 既知の不整合, 既知の不具合と不整合 | Plural form is acceptable when referring to multiple items |
    | At-Least-Once Delivery | At-Least-Once Delivery | at-least-once delivery, at least once delivery | Abbreviation: ALOD; hyphenate when used as adjective |
    ```

### Method

Part A — Add glossary to relevant documentation:

```markdown
<!-- BEFORE -->
The event bus delivers messages to consumers.

<!-- AFTER -->
The EventBus delivers messages to consumers. See [Terminology Glossary](./terminology_glossary.md) for details.
```

### Details

- Glossary follows project convention — clear and actionable.
- Both English and Japanese forms included — supports bilingual readers.
- Abbreviations defined — reduces verbosity while maintaining clarity.

---

#### Part B: Correct typographical and encoding errors

1. Search for common errors:
   ```bash
   rg -n "エンコーディング\|encoding.*error\|typo\|misspell" docs/
   ```
2. For each error found, correct it:
   ```markdown
   <!-- BEFORE -->
   The system uses SQLite for persistance.

   <!-- AFTER -->
   The system uses SQLite for persistence.
   ```

### Method

Part B — Automated typo correction script:

```python
#!/usr/bin/env python3
"""Correct common typos in documentation."""

import re
from pathlib import Path

TYPO_MAP = {
    r"\bpersistance\b": "persistence",
    r"\brecieve\b": "receive",
    r"\boccured\b": "occurred",
    r"\bseperate\b": "separate",
    r"\bdefinately\b": "definitely",
}

def correct_typos(directory: str) -> int:
    """Correct typos in all Markdown files."""
    count = 0
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        for pattern, replacement in TYPO_MAP.items():
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                doc_path.write_text(new_content)
                count += 1
    return count

if __name__ == "__main__":
    corrected = correct_typos(".")
    print(f"Corrected {corrected} typos.")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part C: Standardize table headings

1. Search for inconsistent table headings:
   ```bash
   rg -n "^##.*Table\|^##.*表\|^##.*List\|^##.*リスト" docs/
   ```
2. For each heading found, standardize to English form:
   ```markdown
   <!-- BEFORE -->
   ## 関連ドキュメント一覧

   <!-- AFTER -->
   ## Related Documents List
   ```

### Method

Part C — Standardize table headings:

```markdown
<!-- BEFORE -->
## 既知の問題

<!-- AFTER -->
## Known Issues
```

### Details

- Heading update is minimal — just replaces Japanese with English equivalent.
- Follows project convention — concise, direct sentences.

---

#### Part D: Repair broken code fences

1. Search for broken code fences:
   ```bash
   rg -n "^\`\`\`[a-z]*$" docs/
   ```
2. For each broken fence found, add missing closing fence:
   ```markdown
   <!-- BEFORE -->
   ```python
   def foo():
       pass
   ```

   <!-- AFTER -->
   ```python
   def foo():
       pass
   ```
   ```

### Method

Part D — Repair broken code fences:

```python
#!/usr/bin/env python3
"""Repair broken code fences in documentation."""

import re
from pathlib import Path

def repair_code_fences(directory: str) -> int:
    """Repair broken code fences in all Markdown files."""
    count = 0
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        # Find unclosed code fences
        open_fences = len(re.findall(r"^```", content, re.MULTILINE))
        if open_fences % 2 != 0:
            # Add closing fence
            content += "\n```\n"
            doc_path.write_text(content)
            count += 1
    return count

if __name__ == "__main__":
    repaired = repair_code_fences(".")
    print(f"Repaired {repaired} broken code fences.")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part E: Ensure dates follow ISO 8601

1. Search for non-ISO dates:
   ```bash
   rg -n "[0-9]{2}/[0-9]{2}/[0-9]{4}\|[0-9]{2}-[0-9]{2}-[0-9]{4}" docs/
   ```
2. For each non-ISO date found, convert to ISO 8601:
   ```markdown
   <!-- BEFORE -->
   Updated on 08/18/2026.

   <!-- AFTER -->
   Updated on 2026-08-18.
   ```

### Method

Part E — Date conversion script:

```python
#!/usr/bin/env python3
"""Convert dates to ISO 8601 format."""

import re
from datetime import datetime
from pathlib import Path

NON_ISO_PATTERNS = [
    (r"(\d{2})/(\d{2})/(\d{4})", "%m/%d/%Y"),
    (r"(\d{2})-(\d{2})-(\d{4})", "%m-%d-%Y"),
]

def convert_dates(directory: str) -> int:
    """Convert dates to ISO 8601 format."""
    count = 0
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        for pattern, fmt in NON_ISO_PATTERNS:
            def replacer(m):
                try:
                    dt = datetime.strptime(m.group(0), fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    return m.group(0)
            new_content = re.sub(pattern, replacer, content)
            if new_content != content:
                doc_path.write_text(new_content)
                count += 1
    return count

if __name__ == "__main__":
    converted = convert_dates(".")
    print(f"Converted {converted} dates to ISO 8601.")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part F: Deduplicate "Related Documents" lists

1. Search for duplicate entries:
   ```bash
   rg -n "Related Documents\|関連ドキュメント" docs/
   ```
2. For each list found, remove duplicates:
   ```markdown
   <!-- BEFORE -->
   ## Related Documents
   - [docs/architecture.md](./architecture.md)
   - [docs/architecture.md](./architecture.md)
   - [docs/deployment.md](./deployment.md)

   <!-- AFTER -->
   ## Related Documents
   - [docs/architecture.md](./architecture.md)
   - [docs/deployment.md](./deployment.md)
   ```

### Method

Part F — Deduplicate related documents:

```python
#!/usr/bin/env python3
"""Deduplicate 'Related Documents' lists."""

import re
from pathlib import Path

def deduplicate_related_docs(directory: str) -> int:
    """Deduplicate 'Related Documents' lists."""
    count = 0
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        # Find Related Documents section
        match = re.search(r"(## Related Documents\n)([\s\S]*?)(?=##|\Z)", content)
        if match:
            header = match.group(1)
            body = match.group(2)
            # Extract links
            links = re.findall(r"\[([^\]]+)\]\(([^\)]+)\)", body)
            seen = set()
            unique_links = []
            for title, url in links:
                key = (title, url)
                if key not in seen:
                    seen.add(key)
                    unique_links.append(f"- [{title}]({url})")
            # Rebuild section
            new_body = "\n".join(unique_links) + "\n"
            new_content = content[:match.start()] + header + new_body + content[match.end():]
            if new_content != content:
                doc_path.write_text(new_content)
                count += 1
    return count

if __name__ == "__main__":
    deduped = deduplicate_related_docs(".")
    print(f"Deduplicated {deduped} 'Related Documents' lists.")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part G: Standardize "Part" link representations

1. Search for inconsistent "Part" references:
   ```bash
   rg -n "Part\s*[0-9]+\|パート\s*[0-9]+" docs/
   ```
2. For each reference found, standardize to consistent format:
   ```markdown
   <!-- BEFORE -->
   See Part 1 of the plan.

   <!-- AFTER -->
   See [Part 1](#part-1) of the plan.
   ```

### Method

Part G — Standardize Part references:

```markdown
<!-- BEFORE -->
See Part 2 for details.

<!-- AFTER -->
See [Part 2](#part-2) for details.
```

### Details

- Link update is minimal — just adds anchor reference.
- Follows project convention — concise, direct sentences.

---

#### Part H: Remove or consolidate empty "Keywords" sections

1. Search for empty Keywords sections:
   ```bash
   rg -n "Keywords:\s*$\|キーワード:\s*$" docs/
   ```
2. For each empty section found, remove it:
   ```markdown
   <!-- BEFORE -->
   ## Keywords
   
   <!-- AFTER -->
   (removed)
   ```

### Method

Part H — Remove empty Keywords sections:

```python
#!/usr/bin/env python3
"""Remove empty Keywords sections from documentation."""

import re
from pathlib import Path

def remove_empty_keywords(directory: str) -> int:
    """Remove empty Keywords sections."""
    count = 0
    for doc_path in Path(directory).rglob("*.md"):
        content = doc_path.read_text()
        # Find empty Keywords sections
        pattern = r"(## Keywords\n)(\s*\n)"
        new_content = re.sub(pattern, "", content)
        if new_content != content:
            doc_path.write_text(new_content)
            count += 1
    return count

if __name__ == "__main__":
    removed = remove_empty_keywords(".")
    print(f"Removed {removed} empty Keywords sections.")
```

### Details

- Script scans all Markdown files in the repository.
- Output format matches project convention — machine-readable and human-readable.
- No behavioral changes — purely observability.

---

#### Part I: Replace unstable line-number references with stable identifiers

1. Search for line-number references:
   ```bash
   rg -n "line\s*[0-9]+\|L\d+\|行目" docs/
   ```
2. For each reference found, replace with stable identifier:
   ```markdown
   <!-- BEFORE -->
   See line 42 of the config file.

   <!-- AFTER -->
   See `config/system.toml::max_connections`.
   ```

### Method

Part I — Replace line-number references:

```markdown
<!-- BEFORE -->
The value at line 15 should be updated.

<!-- AFTER -->
The value at `config/approval.toml::timeout_hours` should be updated.
```

### Details

- Reference update is minimal — just replaces line number with config key.
- Follows project convention — concise, direct sentences.

---

#### Part J: Implement Markdown linting and link validation in CI

1. Create CI step for Markdown linting:
   ```yaml
   - name: Lint Markdown
     run: |
       pip install markdownlint-cli
       markdownlint --config .markdownlint.json docs/
   ```

2. Create CI step for link validation:
   ```yaml
   - name: Validate Links
     run: |
       pip install linkchecker
       linkchecker --config .linkcheckerrc docs/
   ```

3. Create `.markdownlint.json`:
   ```json
   {
     "MD013": false,
     "MD024": false,
     "MD033": false
   }
   ```

4. Create `.linkcheckerrc`:
   ```ini
   [linkchecker]
   ignore=.*\.pdf$
   ignore=.*\.png$
   ignore=.*\.jpg$
   ignore=.*\.jpeg$
   ```

### Method

Part J — Add CI steps:

```yaml
# .github/workflows/docs.yml
name: Docs Validation

on:
  push:
    paths:
      - docs/**/*.md

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install markdownlint-cli linkchecker
      - name: Lint Markdown
        run: markdownlint --config .markdownlint.json docs/
      - name: Validate Links
        run: linkchecker --config .linkcheckerrc docs/
```

### Details

- CI steps follow project convention — clear and actionable.
- Configuration files added — enables consistent validation.
- Exclusions defined — prevents false positives.

## Compatibility considerations

- Adding terminology glossary does not affect runtime behavior.
- Correcting typos does not change code — purely documentation.
- Repairing broken code fences does not affect code — purely documentation.
- Converting dates does not affect code — purely documentation.
- Deduplicating related documents does not affect code — purely documentation.
- Standardizing Part references does not affect code — purely documentation.
- Removing empty Keywords sections does not affect code — purely documentation.
- Replacing line-number references does not affect code — purely documentation.
- CI validation does not affect runtime behavior — purely CI.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert terminology glossary: remove glossary document.
- Revert typo corrections: restore original text.
- Revert code fence repairs: restore original fences.
- Revert date conversions: restore original dates.
- Revert deduplication: restore original lists.
- Revert Part standardization: restore original references.
- Revert empty Keywords removal: restore original sections.
- Revert line-number replacements: restore original references.
- Revert CI validation: delete CI steps and configuration files.
- No schema changes — rollback is purely documentation-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All modified docs | Manual review: verify no broken cross-references | Visual inspection of each changed document | No broken links, no misleading content |
| All modified docs | Automated: verify no duplicate sections remain | `rg -n "Deprecated Items\|Canonical Source Rule" docs/` — check for remaining raw text vs. links | Only links to canonical docs remain |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |
| Generated inventory | Manual verification against active configuration | Visual inspection | Inventory matches config |
| CI pipeline | Stale output detection | Trigger CI build | Warning displayed for stale output |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260818_12_issue.md
- Source requirement: requires/20260818-172400_require.md
- Source plan: plans/20260818-190237_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-215512
- Related target files: docs/**/*.md, routing.md, AGENTS.md
