# Implementation Procedure: `tests/test_crawler_targets_file.py`

**Target file:** `tests/test_crawler_targets_file.py` (new file)

---

## Goal

Create a new test file covering all behaviors introduced by the `--targets-file` feature:

1. `parse_targets_file()` — valid inputs, invalid scheme, invalid lang, missing file
2. `main()` — `--url` / `--targets-file` mutual exclusion
3. `WebCrawler.crawl()` — `file://` dispatch to `crawl_file()`
4. CLI `--help` output — confirm `--force` is absent from crawler help

---

## Scope

**In-scope:**
- 8 test functions as specified in the plan
- Unit tests only (no real HTTP or filesystem access beyond temp files)
- `pytest` + `pytest-asyncio` (already used in the project)

**Out-of-scope:**
- Integration tests involving real crawl runs
- Tests for `parse_target_urls()` (existing function; unchanged)
- Tests for `chunk_splitter` or `ingester`

---

## Assumptions

1. `pytest-asyncio` is available (used by existing async tests in the project). Use `@pytest.mark.asyncio` for async test cases.
2. `tmp_path` fixture (built-in pytest) is available for creating temporary TOML files.
3. `unittest.mock.patch` or `pytest-mock` (`mocker` fixture) is available for mocking `crawl_file()`.
4. `parse_targets_file` is importable from `rag.ingestion.crawler_utils`.
5. `main()` exits via `SystemExit(2)` on `parser.error()` — test with `pytest.raises(SystemExit)`.
6. For the help test, use `argparse` directly (`parser.parse_args(["--help"])`) or capture subprocess stdout. Using `argparse` directly is preferred (no subprocess overhead).

---

## Implementation

### Target file

`tests/test_crawler_targets_file.py`

### Procedure

Create the file from scratch. The file structure is:

```
tests/test_crawler_targets_file.py
├── imports
├── test_parse_targets_file_http()
├── test_parse_targets_file_file_url()
├── test_parse_targets_file_invalid_scheme()
├── test_parse_targets_file_invalid_lang()
├── test_parse_targets_file_missing_file()
├── test_main_url_and_targets_file_conflict()
├── test_crawler_help_no_force()
└── test_crawl_dispatches_file_url_to_crawl_file()
```

### Test specifications

#### `test_parse_targets_file_http()`

**Purpose:** Verify that a valid TOML file with an `http://` URL is parsed correctly.

**Setup:**
- Write a temporary TOML file using `tmp_path`:
  ```toml
  target_urls = [["https://example.com/", "en"]]
  ```

**Assertion:**
- `parse_targets_file(path)` returns `[("https://example.com/", "en")]`

---

#### `test_parse_targets_file_file_url()`

**Purpose:** Verify that a `file://` URL is accepted and parsed.

**Setup:**
- Write a temporary TOML file:
  ```toml
  target_urls = [["file:///path/to/file.py", "en"]]
  ```

**Assertion:**
- `parse_targets_file(path)` returns `[("file:///path/to/file.py", "en")]`

---

#### `test_parse_targets_file_invalid_scheme()`

**Purpose:** Verify that an unsupported URL scheme raises `ValueError`.

**Setup:**
- Write a temporary TOML file:
  ```toml
  target_urls = [["ftp://example.com/file.txt", "en"]]
  ```

**Assertion:**
- `parse_targets_file(path)` raises `ValueError`
- Error message contains `"unsupported URL scheme"` (substring match)

---

#### `test_parse_targets_file_invalid_lang()`

**Purpose:** Verify that an unsupported lang value raises `ValueError`.

**Setup:**
- Write a temporary TOML file:
  ```toml
  target_urls = [["https://example.com/", "zh"]]
  ```

**Assertion:**
- `parse_targets_file(path)` raises `ValueError`
- Error message contains `"unsupported lang"` (substring match)

---

#### `test_parse_targets_file_missing_file()`

**Purpose:** Verify that a nonexistent path raises `FileNotFoundError`.

**Setup:**
- Use `tmp_path / "nonexistent.toml"` (do not create the file)

**Assertion:**
- `parse_targets_file(path)` raises `FileNotFoundError`

---

#### `test_main_url_and_targets_file_conflict()`

**Purpose:** Verify that passing both `--url` and `--targets-file` causes `parser.error()` → `SystemExit(2)`.

**Setup:**
- Create a dummy targets file using `tmp_path` (content does not matter since the conflict is checked first)
- Patch `sys.argv` to simulate: `["crawler.py", "--url", "https://example.com/", "--targets-file", str(targets_path)]`

**Assertion:**
- Calling `main()` (from `rag.ingestion.crawler`) raises `SystemExit` with code `2`

**Implementation note:**
- Use `with pytest.raises(SystemExit) as exc_info:` and assert `exc_info.value.code == 2`
- Use `monkeypatch.setattr(sys, "argv", [...])` to set CLI args

---

#### `test_crawler_help_no_force()`

**Purpose:** Verify that `--force` does not appear in the crawler's help output.

**Setup:**
- Patch `sys.argv` to `["crawler.py", "--help"]`

**Implementation:**
- Capture `argparse` output. Since `--help` calls `sys.exit(0)`, wrap in `pytest.raises(SystemExit)`.
- Use `capsys` fixture to capture stdout.

**Assertion:**
- `"--force"` is not in the captured stdout

**Alternative approach (if capsys does not capture argparse output):**
- Import the `argparse.ArgumentParser` from `crawler.py`'s `main()` by extracting it into a helper, or use `subprocess.run` with `--help` and check stdout.
- Simpler fallback: `import argparse; from rag.ingestion.crawler import main; ...` and rely on `capsys`.

---

#### `test_crawl_dispatches_file_url_to_crawl_file()`

**Purpose:** Verify that `WebCrawler.crawl()` dispatches a `file://` target to `crawl_file()` and does NOT call `crawl_site()`.

**Setup:**
- Instantiate `WebCrawler` with a minimal mock config dict:
  ```python
  config = {
      "rag_src_dir": str(tmp_path),
      "crawl_delay": 0,
      "max_depth": 1,
      "min_chunk": 40,
      "fetch_retry": 1,
      "fetch_timeout": 5,
      "crawl_concurrency": 1,
      "max_pages": 10,
      "target_urls": [],
      "skip_nofollow": False,
      "skip_external": True,
  }
  crawler = WebCrawler(config=config)
  ```
- Mock `crawler.crawl_file` using `unittest.mock.patch.object` or `mocker.patch.object`

**Test:**
```python
targets = [("file:///tmp/some_file.py", "en")]
import asyncio
asyncio.run(crawler.crawl(targets))
```

**Assertion:**
- `crawler.crawl_file` was called exactly once
- Called with `Path("/tmp/some_file.py")` and `"en"` as arguments

**Note:** `crawl_site` must NOT be called. Verify via `mock_crawl_site.assert_not_called()` if mocked, or by asserting `crawl_file.call_count == 1` and no HTTP calls occurred.

---

## File structure template

```python
"""Tests for --targets-file feature: parse_targets_file(), crawl() file:// dispatch, and CLI argument handling."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from rag.ingestion.crawler import WebCrawler, main
from rag.ingestion.crawler_utils import parse_targets_file


# --- parse_targets_file tests ---

def test_parse_targets_file_http(tmp_path: Path) -> None: ...

def test_parse_targets_file_file_url(tmp_path: Path) -> None: ...

def test_parse_targets_file_invalid_scheme(tmp_path: Path) -> None: ...

def test_parse_targets_file_invalid_lang(tmp_path: Path) -> None: ...

def test_parse_targets_file_missing_file(tmp_path: Path) -> None: ...


# --- main() conflict tests ---

def test_main_url_and_targets_file_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None: ...


# --- CLI help tests ---

def test_crawler_help_no_force(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None: ...


# --- crawl() dispatch tests ---

def test_crawl_dispatches_file_url_to_crawl_file(tmp_path: Path) -> None: ...
```

---

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 8 tests pass | `uv run pytest tests/test_crawler_targets_file.py -v` | 8 passed, 0 failed |
| No import errors | `uv run python -c "import tests.test_crawler_targets_file"` | No errors |
| mypy on test file | `mypy tests/test_crawler_targets_file.py` | No new errors |
| Full suite unaffected | `uv run pytest tests/ -x -q` | All pass |
