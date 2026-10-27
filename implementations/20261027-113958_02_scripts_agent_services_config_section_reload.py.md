## Goal

Split the two section-reload primitives in `scripts/agent/services/config_section_reload.py` into prepare (build candidate + run validators, no live mutation) and apply (`setattr` only) halves, and re-implement `reload_validated_section` and `reload_direct_fields` as prepare-plus-apply compositions. This gives `config_reload.py` (row 01) the building blocks to validate every section before any `setattr`, while keeping the existing public functions stable for current callers and tests (REQ-002).

## Scope

- **In-Scope** (`scripts/agent/services/config_section_reload.py` only):
  - Add `prepare_validated_section` (new): build the `dataclasses.replace` candidate and run the existing registry validators for a validated section, returning the candidate and changed-field report; no `setattr`.
  - Add `apply_validated_section` (new): `setattr` the prepared candidate onto `ctx.cfg`.
  - Add `prepare_direct_section` (new): collect changed fields and build the `dataclasses.replace` candidate for a direct section with no validators, no `setattr`.
  - Add `apply_direct_section` (new): apply the prepared direct candidate.
  - Re-implement `reload_validated_section` (L15-57) and `reload_direct_fields` (L60-94) as the prepare-then-apply compositions.
- **Out-of-Scope**:
  - The orchestration reorder in `scripts/agent/services/config_reload.py` (row 01).
  - New validators or registry-semantics changes (REQ-006; reference `config_field_registry.py` / `config_validators.py`).
  - The regression tests (row 03) and the hot-reload doc (row 04).

## Assumptions

- `reload_validated_section` and `reload_direct_fields` are the sole production importers of this module (`config_reload.py`); grep confirms a single importer, so the prepare/apply split does not ripple.
- All six section dataclasses (`config_dataclasses.py`) accept `dataclasses.replace`; the validated sections already use it at L43.
- Registry `validator_fn` values take exactly one section candidate and never read live `ctx.cfg`, so the prepare phase needs no live-cfg extraction.
- Existing tests call `reload_validated_section` / `reload_direct_fields` (not the new prepare/apply halves), so preserving them as compositions keeps the public surface intact (REQ-002).

## Design decisions

- **Prepare returns the candidate; apply owns the mutation.** prepare_validated_section returns `(changed_fields, candidate)` and raises `ConfigReloadValidationError` during the validator loop (preserving the L42-54 wrapping and field-name specificity); apply_validated_section performs only the `setattr`. This is what lets row 01 validate the whole config before touching live state.
- **Direct path mirrors the validated path.** prepare_direct_section collects changed fields and builds the candidate via `dataclasses.replace` with no validators (rule set unchanged, REQ-006); apply_direct_section applies it. The composition `reload_direct_fields` keeps its original signature and return type.
- **Compositions preserve behavior.** `reload_validated_section` returns `[]` when nothing changed and `[section_path]` when applied; `reload_direct_fields` returns the changed-fields dict. The compositions reproduce these exactly by short-circuiting when the prepare phase reports no changes.

## Alternatives considered

- **Fusing prepare and apply in a single new pair.** Rejected: row 01 needs the prepare result WITHOUT application to stage the whole candidate set, so the halves must be independently callable.
- **Adding a single prepare_section dispatching on section type.** Rejected: the validated and direct paths differ (validators vs none), and the plan names four distinct functions; a dispatcher would hide that difference.

## Implementation

### Target file

`scripts/agent/services/config_section_reload.py` (existing; two functions split into four plus two compositions)

### Procedure

1. Open `scripts/agent/services/config_section_reload.py` and locate `reload_validated_section` (L15-57), whose body collects `changed_fields`, builds the `dataclasses.replace` candidate (L43), runs the validator loop (L42-54), and ends with the `setattr` at L56.
2. Extract the body up to (but excluding) the L56 `setattr` into a new prepare_validated_section that returns a two-tuple `(changed_fields, candidate)`. Keep the L42-54 validator loop and its `ValueError -> ConfigReloadValidationError` wrapping inside this prepare variant so validation errors surface here (REQ-003).
3. Add a new `apply_validated_section` (new) that takes the prepared candidate and performs the single `setattr(ctx.cfg, section_path, candidate)`.
4. Re-implement `reload_validated_section` as the composition: call prepare_validated_section; if the changed-field report is empty return `[]`; otherwise call apply_validated_section and return `[section_path]`.
5. Extract `reload_direct_fields` (L60-94) similarly: add a new prepare_direct_section that collects `changed_fields` and builds the `dataclasses.replace` candidate with no validators and no `setattr`, returning `(changed_fields, candidate)`; add a new apply_direct_section that applies the candidate.
6. Re-implement `reload_direct_fields` as the composition of the new direct prepare and apply halves, preserving its original signature, short-circuit, and returned dict.
7. Confirm no new validator or registry entry was added or changed (REQ-006) and that the sole production importer (`config_reload.py`) still resolves the two public functions.
8. Run the validation sequence (`routing.md`).

### Method

The current module defines two functions. `reload_validated_section` (L15-57) reads the current section, collects changed fields, builds the candidate, validates, and finally `setattr`s; `reload_direct_fields` (L60-94) collects changed fields and `setattr`s each field. The edit moves the "build + validate" half and the "apply" half apart:

```
def prepare_validated_section(ctx, section_path, new_cfg):
    cfg = getattr(ctx.cfg, section_path)
    changed_fields = {}
    for field_entry in registry_for(section_path):
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value
    if not changed_fields:
        return {}, None
    replaced = dataclasses.replace(cfg, **changed_fields)
    for field_entry in registry_for(section_path):
        if field_entry.name in changed_fields:
            validator = field_entry.validator_fn
            if validator is not None:
                try:
                    validator(replaced)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e
    return changed_fields, replaced


def apply_validated_section(ctx, section_path, candidate):
    setattr(ctx.cfg, section_path, candidate)


def reload_validated_section(ctx, section_path, new_cfg):
    changed_fields, candidate = prepare_validated_section(ctx, section_path, new_cfg)
    if not changed_fields:
        return []
    apply_validated_section(ctx, section_path, candidate)
    return [section_path]


def prepare_direct_section(ctx, section_path, new_cfg, field_filter=None):
    cfg = getattr(ctx.cfg, section_path)
    changed_fields = {}
    for field_entry in registry_for(section_path):
        if field_filter is not None and field_entry.name not in field_filter:
            continue
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value
    if not changed_fields:
        return {}, None
    return changed_fields, dataclasses.replace(cfg, **changed_fields)


def apply_direct_section(ctx, section_path, candidate):
    for field_name, value in <candidate changed fields>.items():
        setattr(getattr(ctx.cfg, section_path), field_name, value)


def reload_direct_fields(ctx, new_cfg, section_path, field_filter=None):
    changed_fields, candidate = prepare_direct_section(
        ctx, new_cfg, section_path, field_filter
    )
    if not changed_fields:
        return {}
    apply_direct_section(ctx, section_path, candidate)
    return changed_fields
```

The illustrative block shows the shape; the exact apply_direct_section application iterates the candidate's changed fields. The decisive change is that every `setattr` now lives in a dedicated apply half that row 01 calls only after the whole candidate set is valid.

### Details

- **`REQ-002` / `AC-005`:** `reload_validated_section` and `reload_direct_fields` remain as prepare-plus-apply compositions with unchanged signatures and return types, so existing callers and tests keep working; four new functions are added.
- **`REQ-003` / `AC-003`:** the validator `ValueError -> ConfigReloadValidationError` wrapping (L42-54) stays inside prepare_validated_section, so failure messages still name the failing field; the raised type is preserved.
- **`REQ-006`:** no validator or registry entry is added, removed, or weakened; the direct path gains no validators it did not already have.

## Compatibility considerations

- Additive: four new module-level functions plus two reimposed compositions. No existing signature changes; the sole importer (`config_reload.py`) resolves the two retained public functions unchanged.

## Security considerations

- No new input surface or secret handling; the split reorders where validation and mutation happen, not which fields are accepted.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/services/config_section_reload.py` | Compositions reproduce original behavior; prepare raises, apply mutates | `uv run pytest tests/agent/services/test_config_reload.py` | AC-005 pass; compositions unchanged |
| Existing behavior | Regression | `uv run pytest tests/agent/services/test_config_reload_classification.py tests/agent/commands/test_agent_cmd_config.py` | Pass unchanged |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- prepare_validated_section / apply_validated_section and prepare_direct_section / apply_direct_section exist as separate prepare and apply halves; reload_validated_section and reload_direct_fields are their compositions with unchanged signatures; no validator or registry entry changed.
- `mypy` and `ruff` pass; the regression gate passes.

## Out of Scope

- The orchestration reorder (`scripts/agent/services/config_reload.py`, row 01).
- New validators or registry changes (reference only).
- The regression tests (row 03).
- The hot-reload doc (row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Prepare/apply split in `config_section_reload.py` (this row) | In Progress | — | — | REQ-002, REQ-003, REQ-006 |
| 2 | Two-phase reorder of `apply_config_dict` (row 01) | Pending | — | — | Depends on this row |
| 3 | Regression tests (row 03) | Pending | — | — | Dependency |
| 4 | Hot-reload doc (row 04) | Pending | — | — | REQ-001, REQ-003 |
| 5 | Run validation sequence | Pending | — | — | pytest/mypy/ruff |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-006`
- **Source issue**: `issues/20261026-224903_config001_make-config-reload-atomic.md`
- **Source plan**: `plans/20261027-073638_config001_make-config-reload-atomic.md`
- **Generated at**: 20261027-113958
- **Related target files**: `scripts/agent/services/config_section_reload.py`
