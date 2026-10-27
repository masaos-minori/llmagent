## Goal

Reorder `apply_config_dict` in `scripts/agent/services/config_reload.py` into two phases so the live context is mutated only after the entire candidate configuration validates. Today the method applies each section as it succeeds through the chained helpers at L106-108, so an invalid later section leaves earlier sections already applied to `ctx.cfg` while services are never re-synced. This Plan confines the change to the orchestration ordering inside `apply_config_dict`; the field registry, validators, and service-sync implementation are unchanged.

## Scope

- **In-Scope** (`scripts/agent/services/config_reload.py` only):
  - Restructure `apply_config_dict` (L89-122) into a candidate phase (build and validate every section, direct field, and the MCP classification; no live mutation) followed by a commit phase (apply candidate sections, set the `ctx.conv` field, run removed-server lifecycle cleanup, then `_sync_services`).
  - Fold `allowed_tools` and `masked_fields` into the `tool` candidate so they become atomic with it. Verification note: `allowed_tools` is already a `tool`-section registry entry (`config_field_registry.py` L80), so the prepare variant picks it up automatically; only `masked_fields` (not a registry entry) needs explicit folding via the prepare variant's `extra_changed_fields` parameter.
  - Hold `system_prompt_tool` in a pending-apply list executed only in the commit phase.
  - Move MCP removed-server `cleanup_server_resources` to the commit phase (REQ-004).
- **Out-of-Scope**:
  - The prepare/apply split of the section-reload primitives (`scripts/agent/services/config_section_reload.py`; row 02).
  - The regression tests (row 03).
  - The hot-reload doc (row 04).
  - `cmd_config.py` error rendering (reference only; REQ-003; MUST NOT be modified).

## Assumptions

- `apply_config_dict` is the sole production entry point the command handler calls; `apply_config` delegates to it, so `cmd_config.py` needs no change (Reference File).
- Registry validators take only the candidate section and never read live `ctx.cfg` (confirmed by `config_validators.py` signature review), so candidate-phase validation needs no live-cfg extraction.
- `classify_mcp_server_changes` is read-only classification; only the removed-server branch carries the `cleanup_server_resources` side effect. Verification facts: it returns `list[str]` (no `.needs_restart` object), and it calls `_build_mcp_servers(new_cfg)` which raises `ValueError` when `new_cfg` has no non-empty `mcp_servers` key — the existing `if "mcp_servers" not in new_cfg` guard in `_handle_mcp_changes` (L252-253) must be kept in the candidate phase.
- `dataclasses.replace` candidate construction applies to the three validated sections (`llm`/`rag`/`tool`) only. Direct sections are staged as changed-field dicts and applied with per-field `setattr` (row 02 Design decisions; test fixtures model `ctx.cfg.approval` / `ctx.cfg.mcp` as `MagicMock`).
- `new_cfg` payloads are flat: reloadable field names appear at the top level of the dict (e.g. `{"llm_temperature": 0.5}`), matching `_req_to_dict` flattening (L125-140) and existing tests.

## Design decisions

- **Candidate phase first.** Build a candidate for every touched validated section via `dataclasses.replace` on the current section (the pattern already used in `reload_validated_section`) and run the existing validators for all of them before touching live state. Collect direct-section changed-field dicts, fold `masked_fields` into the `tool` candidate via `extra_changed_fields` (`allowed_tools` arrives through the registry), hold `system_prompt_tool` aside for the conv update, and classify MCP changes — all without any `setattr` or lifecycle call.
- **Commit phase last.** Only after the whole candidate set is valid: `setattr` the candidates onto `ctx.cfg`, execute the pending `system_prompt_tool` update, run removed-server cleanup, then `_sync_services`. Because the candidate phase is the only place validation can raise, no validation-error path exists in the commit phase, making whole-config atomicity a structural property (no rollback or compensation code).
- **Pending-apply for the conv field.** `system_prompt_tool` targets `ctx.conv`, not `ctx.cfg`, so it is staged in a small pending-apply list executed only in the commit phase.

## Alternatives considered

- **Compensating rollback in the commit phase.** Rejected: the failure model confines validation to the candidate phase, so there is nothing to compensate once committing; a compensation routine adds complexity for a path that cannot fail.
- **Validating sections inline as today.** Rejected: that is exactly the partial-apply defect this Plan removes (an invalid `tool` leaves `llm` and `rag` already applied).

## Implementation

### Target file

`scripts/agent/services/config_reload.py` (existing; `apply_config_dict` reordered)

### Procedure

1. Open `scripts/agent/services/config_reload.py` and locate `apply_config_dict` (L89-122), whose body currently chains `_apply_validated_sections` (L210-221), `_apply_direct_reloads` (L223-234), `_apply_direct_fields` (L236-243), `_handle_mcp_changes` (L245-264), and `_sync_services` (L144-161) in a single mutating sequence.
2. Replace the body with a two-phase structure: a candidate phase that builds and validates every section, direct field, and the MCP classification without mutating live state, then a commit phase that applies the validated results.
3. In the candidate phase, iterate `llm`, `rag`, and `tool` and build each section candidate via `prepare_validated_section` (row 02), collecting only non-empty `(section_path, candidate)` pairs into a new `prepared` collection. For `tool`, pass `extra_changed_fields={"masked_fields": list(new_cfg["masked_fields"])}` when `masked_fields` is present in `new_cfg` AND differs from `ctx.cfg.tool.masked_fields` (mirrors the registry's equal-value skip); `allowed_tools` is already a `tool`-section registry entry and is picked up by the prepare variant itself.
4. In the candidate phase, collect the `approval`, `memory`, and `mcp` direct-section changed fields via `prepare_direct_section` from row 02 (no validators, no candidate; REQ-006), and — only when `mcp_servers` is present in `new_cfg` (guard preserved from `_handle_mcp_changes` L252-253) — classify MCP server changes with `classify_mcp_server_changes` read-only. It returns `list[str]`; do NOT run `cleanup_server_resources` here.
5. In the candidate phase, if `system_prompt_tool` is present in `new_cfg`, append a zero-arg closure to a new `pending_conv_updates` (new) list instead of setting `ctx.conv.system_prompt_content` now.
6. In the commit phase, `setattr` each prepared validated candidate onto `ctx.cfg` in order and append each such `section_path` to `outcome.applied`; apply each direct-section changed-field dict with `apply_direct_section` (per-field `setattr` on the live section) and append the non-empty section names to `outcome.applied`; invoke each closure in pending_conv_updates to set `ctx.conv.system_prompt_content`; run removed-server `cleanup_server_resources` for the MCP items classified as removed and append the remaining items to `outcome.needs_restart`; finally call `_sync_services`.
7. Confirm the outcome report shape (`applied`, `needs_restart`, `skipped`, `startup_only`, `always_live`) is unchanged (REQ-007) and that `cmd_config.py` still surfaces `ConfigReloadValidationError` unchanged (reference only).
8. Run the validation sequence (`routing.md`).

### Method

The current `apply_config_dict` body (L89-122) opens at L103 with `ctx = self._ctx` and `outcome = ConfigReloadOutcome()`, then mutates live state through the five chained helpers. The edit keeps that opening and replaces the chained mutation with a candidate phase followed by a commit phase:

```
def apply_config_dict(self, new_cfg):
    ctx = self._ctx
    outcome = ConfigReloadOutcome()

    # Candidate phase: build + validate everything; no live mutation
    prepared = []                       # (section_path, candidate) pairs, changes only
    for section_path in ("llm", "rag", "tool"):
        extra = None
        if (
            section_path == "tool"
            and "masked_fields" in new_cfg
            and list(new_cfg["masked_fields"]) != ctx.cfg.tool.masked_fields
        ):
            extra = {"masked_fields": list(new_cfg["masked_fields"])}
        changed, candidate = prepare_validated_section(
            ctx, section_path, new_cfg, extra_changed_fields=extra
        )
        if candidate is not None:
            prepared.append((section_path, candidate))
    # approval / memory / mcp direct changed fields (seq 02); no validators
    direct_changed = {}
    for section_path in ("approval", "memory", "mcp"):
        changed_fields = prepare_direct_section(ctx, new_cfg, section_path)
        if changed_fields:
            direct_changed[section_path] = changed_fields
    mcp_items = (
        classify_mcp_server_changes(ctx, new_cfg) if "mcp_servers" in new_cfg else []
    )  # read-only list[str], no cleanup
    pending_conv_updates = []     # closures run only in the commit phase
    if "system_prompt_tool" in new_cfg:
        value = new_cfg["system_prompt_tool"]
        pending_conv_updates.append(
            lambda v=value: setattr(ctx.conv, "system_prompt_content", v)
        )

    # Commit phase: safe, no validation error path exists
    for section_path, candidate in prepared:
        setattr(ctx.cfg, section_path, candidate)
        outcome.applied.append(section_path)
    for section_path, changed_fields in direct_changed.items():
        apply_direct_section(ctx, section_path, changed_fields)
        outcome.applied.append(section_path)
    for update in pending_conv_updates:
        update()
    for item in mcp_items:
        if item.endswith(" (removed server)"):
            lifecycle = ctx.services_required.lifecycle
            if lifecycle is not None:
                lifecycle.cleanup_server_resources(<server key>)
        else:
            outcome.needs_restart.append(item)
    service_result = self._sync_services(
        new_cfg,
        ctx.services_required.llm,
        ctx.services_required.hist_mgr,
        ctx.services_required.runtime_tools,
    )
    outcome.applied.extend(service_result.applied)
    outcome.skipped.extend(service_result.skipped)
    startup_only, always_live = self._classify_outcomes(new_cfg)
    outcome.startup_only = startup_only
    outcome.always_live = always_live
    return outcome
```

The illustrative block shows the shape; the exact direct-section staging uses `prepare_direct_section` from row 02 (changed-field dicts, no candidates); the key structural change is that every `setattr` and the `cleanup_server_resources` call move after the whole candidate set is known valid.

### Details

- **`REQ-001` / `AC-001`:** the candidate phase validates llm, rag, tool, approval, memory, mcp, direct fields, and MCP classification before any `setattr`; a `ConfigReloadValidationError` from any validator aborts before the commit phase, leaving `ctx.cfg` and `ctx.conv.system_prompt_content` unchanged.
- **`REQ-003` / `AC-003`:** the same validators wrap their `ValueError` into `ConfigReloadValidationError` during candidate preparation, preserving field-name specificity; the raised type is unchanged.
- **`REQ-004` / `AC-004`:** `cleanup_server_resources` runs only in the commit-phase loop, so a failed validation never reaches it.
- **`REQ-005` / `AC-001`:** `_sync_services` (L144-161) is called last, only after the commit phase begins, so services are not re-synced on failure.
- **`REQ-007` / `AC-002`:** a fully valid payload still applies every section, direct field, the `system_prompt_tool` conv update, the MCP classification categories, and services; the outcome report shape is unchanged.

## Compatibility considerations

- Purely an internal reordering of `apply_config_dict`: the method signature, the `ConfigReloadOutcome` shape, and the delegated helpers are unchanged. Public entries `apply_config` and `apply_config_dict` stay stable (REQ-002).

## Security considerations

- No new input surface or secret handling; the reorder changes only ordering, not which fields are accepted.

## Rollback considerations

- Revert the file edit (`git checkout`). Single logical commit; revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Reorder correctness; partial-apply gone | `uv run pytest tests/agent/services/test_config_reload.py` | AC-001..AC-004 pass |
| Existing behavior | Regression | `uv run pytest tests/agent/services/test_config_reload_classification.py tests/agent/commands/test_agent_cmd_config.py` | Pass unchanged |
| Static | mypy / ruff | `uv run mypy scripts/`, `uv run ruff check scripts/` | Clean |

## Completion criteria

- `apply_config_dict` validates the fully assembled candidate config before mutating `ctx.cfg` and `ctx.conv`, applies only after success, defers MCP cleanup and `_sync_services` to the commit phase, and the outcome report shape is unchanged.
- `mypy` and `ruff` pass; the regression gate passes.

## Out of Scope

- The prepare/apply split (`scripts/agent/services/config_section_reload.py`, row 02).
- The regression tests (row 03).
- The hot-reload doc (row 04).
- `cmd_config.py` (reference only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Prepare/apply split in `config_section_reload.py` (row 02) | Completed | 20261027-194948 | 20261027-194948 | Dependency |
| 2 | Two-phase reorder of `apply_config_dict` (this row) | Completed | 20261027-194948 | 20261027-194948 | REQ-001, REQ-004, REQ-005, REQ-007 |
| 3 | Regression tests (row 03) | Completed | 20261027-194948 | 20261027-194948 | Dependency |
| 4 | Hot-reload doc (row 04) | Completed | 20261027-194948 | 20261027-194948 | REQ-001, REQ-003 |
| 5 | Run validation sequence | Completed | 20261027-194948 | 20261027-194948 | pytest/mypy/ruff |

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
- **Requirement ID**: `REQ-001`, `REQ-004`, `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261026-224903_config001_make-config-reload-atomic.md`
- **Source plan**: `plans/20261027-073638_config001_make-config-reload-atomic.md`
- **Generated at**: 20261027-113958
- **Related target files**: `scripts/agent/services/config_reload.py`