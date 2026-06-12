# Goal

Replace `except Exception` in `get_repo_info()` with specific exception types
`(ImportError, ValueError, OSError)` to eliminate broad exception catching.

# Scope

- `scripts/shared/git_helper.py` only

# Assumptions

1. `git.Repo()` can raise `git.InvalidGitRepositoryError` (subclass of `ValueError`),
   `git.NoSuchPathError` (subclass of `OSError`), and `ImportError` when gitpython
   is not installed. These three cover all expected failure modes.
2. Any other exception (e.g. `PermissionError`) is an unexpected system error and
   should propagate to the caller rather than being silently swallowed.

# Implementation

## Target file

`scripts/shared/git_helper.py`

## Procedure

1. Change `except Exception as e:` → `except (ImportError, ValueError, OSError) as e:`
2. Run ruff + mypy.

## Method

One-line change. No logic change.

## Details

```python
# Before
    except Exception as e:
        logger.debug("get_repo_info: %s", e)
        return None

# After
    except (ImportError, ValueError, OSError) as e:
        logger.debug("get_repo_info: %s", e)
        return None
```

# Validation plan

- `grep -n "except Exception" scripts/shared/git_helper.py` → 0 hits
- `uv run ruff check scripts/shared/git_helper.py`
- `uv run mypy scripts/shared/git_helper.py`
