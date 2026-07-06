# Implementation: agent/repl_health.py — Replace except Exception: pass with explicit handlers in audit_security_defaults()

## Goal

Replace 4 broad `except Exception: pass` blocks in `audit_security_defaults()` with explicit handlers that raise `RuntimeError` in production mode and log warnings in local mode.

## Scope

**In**: Update exception handlers at shell (line ~634), git (line ~654), github (line ~674), cicd (line ~703) config load sites.

**Out**: Changes to `check_routing_drift()`, watchdog, other functions.

## Assumptions

1. Shell block (line 634): current `except Exception` catches `FileNotFoundError`, `ImportError`, and non-RuntimeError exceptions and swallows them after re-raising `RuntimeError`.
2. Git block (line 654): bare `except Exception: pass` — swallows all including config load failures.
3. GitHub allowed_repos block (line 674): bare `except Exception: pass`.
4. CI/CD block (line 703): bare `except Exception: pass`.
5. GitHub write settings block (line 721): bare `except Exception: pass` — keep non-fatal for this one (it's a soft warning).
6. `security_lockdown_enabled=True` suppresses deny-all warnings but NOT config load failures or production enforcement.
7. `ImportError` for optional dependencies (github-mcp, cicd-mcp) must remain silent in all modes.

## Implementation

### Target file
`scripts/agent/repl_health.py`

### Procedure
1. Replace shell audit exception handler (lines ~634-640).
2. Replace git audit exception handler (lines ~654).
3. Replace GitHub allowed_repos exception handler (lines ~674).
4. Replace CI/CD exception handler (lines ~703).
5. Keep GitHub write settings as warning-only exception handler.

### Method

**Standard replacement pattern:**
```python
except RuntimeError:
    raise
except ImportError:
    pass  # optional dependency not installed; skip gracefully
except (FileNotFoundError, OSError, ValueError, TypeError, AttributeError) as exc:
    msg = f"Security audit: failed to load <name> config: {exc}"
    if production_mode:
        logger.error(msg)
        raise RuntimeError(msg) from exc
    logger.warning(msg)
    warnings.append(msg)
```

**Shell block replacement (replaces lines ~634-640):**
```python
except RuntimeError:
    raise
except ImportError:
    pass
except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
    msg = f"Security audit: failed to load shell config: {exc}"
    if production_mode:
        logger.error(msg)
        raise RuntimeError(msg) from exc
    logger.warning(msg)
    warnings.append(msg)
```

**Git block replacement (replaces `except Exception: pass` at ~654):**
```python
except (ImportError, ModuleNotFoundError):
    pass
except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
    msg = f"Security audit: failed to load git config: {exc}"
    if production_mode:
        logger.error(msg)
        raise RuntimeError(msg) from exc
    logger.warning(msg)
    warnings.append(msg)
```

**GitHub allowed_repos block replacement (at ~674):**
```python
except (ImportError, ModuleNotFoundError):
    pass  # github-mcp optional
except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
    msg = f"Security audit: failed to load GitHub config: {exc}"
    if production_mode:
        logger.error(msg)
        raise RuntimeError(msg) from exc
    logger.warning(msg)
    warnings.append(msg)
```

**CI/CD block replacement (at ~703):**
```python
except (ImportError, ModuleNotFoundError):
    pass  # cicd-mcp optional
except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
    msg = f"Security audit: failed to load CI/CD config: {exc}"
    if production_mode:
        logger.error(msg)
        raise RuntimeError(msg) from exc
    logger.warning(msg)
    warnings.append(msg)
```

**GitHub write settings block (at ~721) — keep non-fatal:**
```python
except (ImportError, ModuleNotFoundError):
    pass
except Exception as exc:  # noqa: BLE001 — GitHub write config is non-critical
    logger.debug("Security audit: skipped GitHub write settings check: %s", exc)
```

### Details

- `lockdown=True` check at line ~591 is already correct — it only suppresses deny-all warnings, not the new config load failure handlers.
- Production mode path always raises immediately (no partial warning list).
- Local mode collects warning and continues.

## Validation plan

- `uv run pytest tests/ -v -k "audit_security or security_failure"` — all pass.
- Verify: production + `OSError` from git config → `RuntimeError`.
- Verify: local + `OSError` from git config → warning in return list.
- Verify: `security_lockdown_enabled=True` + config load failure in production → still raises.
- `mypy scripts/agent/repl_health.py` — no new errors.
- `ruff check scripts/agent/repl_health.py` — 0 errors.
