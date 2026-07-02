# Implementation Procedure: Update `docs/03_rag_02_ingestion_pipeline.md`

**Target file:** `docs/03_rag_02_ingestion_pipeline.md`

---

## Goal

Update `docs/03_rag_02_ingestion_pipeline.md` to reflect the new `--targets-file` argument:

1. Add a `--targets-file` usage example in §1 Step 1 (Crawl section).
2. Add a `--targets-file PATH` row to the §2.3 CLI arguments table.

---

## Scope

**In-scope:**
- §1 "Step 1: Crawl" — add one usage example after the multiple-URL block
- §2.3 "CLI arguments" table — add one row for `--targets-file PATH`

**Out-of-scope:**
- Removing any existing content from §2.3 (plan confirmed: no crawler `--force` row exists in this table; UNK-04 resolved)
- Changes to §2.1 class overview, §2.2 behavior details, or other sections
- Changes to §5 Crawler Utils section

---

## Assumptions

1. No crawler `--force` row exists in §2.3 (confirmed by reading the file; the table has only `--url` and `--lang`).
2. The `--targets-file` TOML format uses `target_urls = [[url, lang], ...]` as a flat inline syntax. The example should show a standalone TOML file, not the `[[target_urls]]` section-array syntax.
3. The example file path `/path/to/targets.toml` is a placeholder — keep it generic.

---

## Implementation

### Target file

`docs/03_rag_02_ingestion_pipeline.md`

### Procedure

#### Change 1: Add `--targets-file` usage example in §1 Step 1

**Location:** After the block ending with `--lang auto` example (line 34), before the `**Note:**` line (line 36).

**Current text (lines 33–36):**
```
# Per-page CJK-ratio language detection
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/page" --lang auto
```

**Add after this block:**
```markdown
# Load targets (http:// and file://) from a TOML file
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

The targets TOML file format:
```toml
target_urls = [
    ["https://ziglang.org/documentation/master/", "en"],
    ["file:///opt/llm/scripts/rag/ingestion/crawler.py", "en"],
]
```

#### Change 2: Add `--targets-file PATH` row to §2.3 CLI arguments table

**Location:** `docs/03_rag_02_ingestion_pipeline.md` lines 203–207 (§2.3 CLI arguments).

**Current table:**
```markdown
| Argument | Description | Default |
|---|---|---|
| `--url URL [URL ...]` | Target URLs (multiple allowed; omit to use `target_urls` from config) | — |
| `--lang {en,ja,auto}` | Hint language for per-page CJK-ratio detection | `en` |
```

**New table (add one row):**
```markdown
| Argument | Description | Default |
|---|---|---|
| `--url URL [URL ...]` | Target URLs (multiple allowed; omit to use `target_urls` from config) | — |
| `--lang {en,ja,auto}` | Hint language for per-page CJK-ratio detection | `en` |
| `--targets-file PATH` | Path to a TOML file with `target_urls = [[url, lang], ...]`; supports `http://`, `https://`, and `file://`; mutually exclusive with `--url` | — |
```

---

## Validation plan

| Check | Method | Expected |
|---|---|---|
| §1 example renders | Read §1 in context | `--targets-file` example present with TOML block |
| §2.3 table has 3 rows | Read §2.3 table | `--url`, `--lang`, `--targets-file` rows present |
| No crawler `--force` introduced | Search for `--force` in §2 | Not present |
