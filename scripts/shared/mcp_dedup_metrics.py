"""scripts/shared/mcp_dedup_metrics.py — Read-only capacity metrics for the dedup store.

Report-only path (REQ-004, AC-8): every value here comes from the read-only metrics view bound
to the ledger (defined in shared/mcp_dedup_rows.py, row 07), on the store's own connection and its
configured busy_timeout, so this module adds no writer and no second lock, and it issues no write,
no migration, and no new service. A computed status is reported only and never gates store or dispatcher behaviour (owner
decision D-6). Threshold values are operator-supplied (U-1): nothing here names a threshold, only
the reporting fractions.

Module family: shared leaf, never imports mcp_servers. The health `details` block is the only
consumer; the public names are re-exported by the shared.mcp_dedup facade.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from shared.mcp_dedup_config import DedupStoreConfig

if TYPE_CHECKING:
    from shared.mcp_dedup_ledger import DedupLedger

METRICS_SCHEMA_VERSION = 1

# Reporting fractions, not thresholds (U-1): the configured `[dedup]` value is the fail boundary,
# so a value at or above it reads as `fail` and one at or above WARNING_FRACTION of it reads as
# `warning` (owner decision, 20261123). These numbers never gate store or dispatcher behaviour.
WARNING_FRACTION = 0.8

STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_FAIL = "fail"

# `growth_rows_per_hour` counts rows created inside this window; the window defines the metric
# name, it is not a threshold value.
GROWTH_WINDOW_SECONDS = 3600

BYTES_PER_MB = 1024 * 1024


def _metric_status(value: float | None, threshold: int | None) -> str | None:
    """Report-only status for one metric (D-6).

    None when the threshold is unset or the read was not available inside the view's lock
    deadline; `fail` at or above the configured value, `warning` at or above the reporting
    fraction of it, otherwise `ok`. A status never changes store or dispatcher behaviour.
    """
    if threshold is None or value is None:
        return None
    if value >= threshold:
        return STATUS_FAIL
    if value >= threshold * WARNING_FRACTION:
        return STATUS_WARNING
    return STATUS_OK


def collect_dedup_metrics(
    store: DedupLedger,
    config: DedupStoreConfig,
    *,
    now_epoch: float | None = None,
) -> dict[str, object]:
    """Assemble the read-only metrics payload for the health `details.dedup` block (REQ-004).

    One read pass per call through `get_dedup_metrics_view()`, so no value is computed here: the
    view issues the SELECT and the `-wal` file stat. A per-metric block appears only when its
    `[dedup]` threshold key is configured; a read that cannot acquire the store lock inside the
    view's deadline reports null values and never raises, so `/health` still answers. The payload
    is JSON-safe: counts, the store path, and the configured held states — no `snapshot_json`,
    `result_json`, key values, or owner ids. `lock_wait_ms` is read last because it accumulates
    the elapsed wait of the pass.
    """
    now = time.time() if now_epoch is None else now_epoch
    view = store.get_dedup_metrics_view()

    row_states = view.row_states()
    pending_overdue = view.pending_overdue(now)
    growth = view.created_since(now - GROWTH_WINDOW_SECONDS)
    wal_size_bytes = view.wal_size_bytes()
    held_past_retention = view.held_past_retention(now, config.retention_days)

    payload: dict[str, object] = {
        "schema_version": METRICS_SCHEMA_VERSION,
        "db_path": view.db_path,
        "generated_epoch": now,
        "row_states": row_states,
        "pending_overdue": pending_overdue,
        "growth_rows_per_hour": growth,
        "wal_size_bytes": wal_size_bytes,
        "legal_hold_states": list(config.legal_hold_states),
        "held_past_retention": held_past_retention,
    }

    total_rows = sum(row_states.values()) if row_states is not None else None
    wal_mb = wal_size_bytes / BYTES_PER_MB if wal_size_bytes is not None else None
    for block, value, threshold in (
        ("rows", total_rows, config.max_dedup_rows),
        ("growth", growth, config.max_dedup_growth_per_hour),
        ("wal", wal_mb, config.max_dedup_wal_mb),
    ):
        if threshold is None:
            continue
        payload[block] = {
            "value": value,
            "threshold": threshold,
            "status": _metric_status(value, threshold),
        }

    payload["lock_wait_ms"] = view.lock_wait_ms()
    return payload
