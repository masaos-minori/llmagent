# Implementation Procedure: Read ConfigLoader API for EventBus Migration Reference

## Goal

Read and understand `ConfigLoader`'s API (`restrict_to`, `load`, `load_all`) to inform the EventBus configuration loading migration in `scripts/eventbus/config.py`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/shared/config_loader.py`: understand `restrict_to()`, `load()`, `load_all()` methods
- No modifications to this file

## Assumptions

- `ConfigLoader.restrict_to()` is a classmethod that sets process-level file access restrictions — confirmed by `config_loader.py:40-49`
- `ConfigLoader.load()` accepts filenames and returns merged config data — confirmed by `config_loader.py:58-66`
- `ConfigLoader.load_all()` accepts multiple filenames and returns merged config data — confirmed by `config_loader.py:68-91`

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `scripts/eventbus/config.py` implementation procedure.

## Alternatives considered

### Alternative A: Modify ConfigLoader to support EventBus-specific validation

**Reason for rejection:** Would violate REQ-002 — EventBus's validation must be preserved exactly. Modifying `ConfigLoader` would require coordinating changes across multiple processes and introducing new dependencies.

## Implementation

### Target file

`scripts/shared/config_loader.py` (read-only)

### Procedure

#### Step 1: Read `restrict_to()` method

Focus on lines 40-49:
```python
@classmethod
def restrict_to(cls, process_name: str) -> None:
    """Set process-level file access restrictions."""
```

Verify:
- How the restriction is applied (file system level, environment variable, etc.)
- Whether it can be called multiple times safely
- What happens if called before `load()` vs after `load()`

#### Step 2: Read `load()` method

Focus on lines 58-66:
```python
def load(self, filename: str) -> dict[str, Any]:
    """Load a single configuration file."""
```

Verify:
- Return type (dict structure)
- Error handling (what exceptions are raised on failure)
- Whether it applies `restrict_to()` automatically

#### Step 3: Read `load_all()` method

Focus on lines 68-91:
```python
def load_all(self, filenames: list[str]) -> dict[str, Any]:
    """Load multiple configuration files and merge them."""
```

Verify:
- Merge order (later files override earlier ones)
- Error handling (what happens if one file fails)
- Whether it applies `restrict_to()` automatically

#### Step 4: Document findings for EventBus migration

Record any differences between `ConfigLoader`'s default behavior and EventBus's current validation requirements. This information will be used in the `scripts/eventbus/config.py` implementation procedure.

### Method

Manual code review — read the relevant sections of `config_loader.py` and document key findings.

### Details

#### Key questions to answer

1. Does `ConfigLoader.load()` return the same dict structure as `tomllib.load()`?
2. Can `ConfigLoader` be used without `restrict_to()` being called first?
3. Does `ConfigLoader` apply any default validation that differs from EventBus's current validation?
4. Is `ConfigLoader._REQUIRED_CONFIG_FILES` configurable, or hardcoded to `("agent.toml",)`?

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `scripts/eventbus/config.py` modification procedure

## Security considerations

- No security impact — this is a read-only step
- Understanding `restrict_to()` is critical for ensuring EventBus gets the same process-isolation guarantee as other processes

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of `ConfigLoader`'s API matches the documented behavior
2. Verify that `ConfigLoader.load()` returns the same dict structure as `tomllib.load()`
3. Verify that `ConfigLoader` does not apply default validation that differs from EventBus's current validation

## Completion criteria

- [x] `restrict_to()` behavior understood — takes filenames, not process names
- [x] `load()` behavior understood (return type, error handling)
- [x] `load_all()` behavior understood (merge order, error handling)
- [x] Differences between `ConfigLoader` defaults and EventBus requirements documented

## Out of scope

- Modifying `ConfigLoader` itself
- Adding new `ConfigLoader` features
- Changing `ConfigLoader`'s validation logic

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read restrict_to() method | Completed | 20260915-221000 | 20260915-221000 | Takes filenames (not process_name); sets _allowed_files class variable |
| 2 | Read load() method | Completed | 20260915-221000 | 20260915-221000 | Takes filenames (not paths); resolves against _config_dir; returns dict[str, Any] |
| 3 | Read load_all() method | Completed | 20260915-221000 | 20260915-221000 | Loads base config files in dependency order; strict mode raises on missing required files |
| 4 | Document findings for EventBus migration | Completed | 20260915-221000 | 20260915-221000 | _REQUIRED_CONFIG_FILES hardcoded to ("agent.toml"); ConfigLoader.load() cannot replace tomllib directly due to filename vs path distinction

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003 (confirm restrict_to() initialization appropriately for EventBus process)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064620
- **Related target files**: scripts/shared/config_loader.py
