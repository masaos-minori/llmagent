# Goal

Replace all three `except Exception` clauses in `ingester.py` with specific
exception types that cover the actual failure modes.

# Scope

- `scripts/rag/ingestion/ingester.py`

# Assumptions

1. Line 59 (`__del__`): `self._client.close()` is an httpx client close operation.
   Failure is `OSError` only.

2. Line 280 (future.result() in `_ingest_chunk_files`): Propagated from
   `_embed_and_store()` which can raise:
   - `httpx.HTTPStatusError` (from `resp.raise_for_status()`)
   - `httpx.RequestError` (from HTTP connection failures)
   - `OSError` (from DB helper or file I/O)
   - `ValueError` (from embedding schema validation)
   - `TypeError` (from embedding type mismatch)
   `httpx` is already imported.

3. Line 312 (`_process_url_groups`): `ingest_url_group()` calls DB operations and
   file I/O, so can raise:
   - `OSError` (file moves, DB writes)
   - `RuntimeError` (unexpected DB state)
   - `ValueError` (data validation)
   - `sqlite3.OperationalError` (DB lock, constraint)
   `sqlite3` is not currently imported — add it.

# Implementation

## Target file

`scripts/rag/ingestion/ingester.py`

## Procedure

1. Add `import sqlite3` to the imports section (after existing stdlib imports).

2. Line 59 — `__del__` except:
   ```python
   # Before
   except Exception:
       pass

   # After
   except OSError:
       pass
   ```

3. Line 280 — future.result() except:
   ```python
   # Before
   except Exception as e:
       logger.error(f"Failed to ingest {path}: {e}")

   # After
   except (httpx.HTTPStatusError, httpx.RequestError, OSError, ValueError, TypeError) as e:
       logger.error(f"Failed to ingest {path}: {e}")
   ```

4. Line 312 — `_process_url_groups` except:
   ```python
   # Before
   except Exception:
       logger.exception(f"ingest_url_group failed: {url}")

   # After
   except (OSError, RuntimeError, ValueError, sqlite3.OperationalError):
       logger.exception(f"ingest_url_group failed: {url}")
   ```

5. Run ruff + mypy.

## Method

Three targeted exception narrowings + one import addition.

# Validation plan

- `grep -n "except Exception" scripts/rag/ingestion/ingester.py` → 0 hits
- `uv run ruff check scripts/rag/ingestion/ingester.py`
- `uv run mypy scripts/rag/ingestion/ingester.py`
- `uv run pytest tests/ -k "ingestion or ingester" --ignore=tests/test_create_schema.py -v`
