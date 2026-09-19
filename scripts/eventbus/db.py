# WARNING: Do not add new functions here. Add them to the appropriate layer module
# and re-export from this stub. See scripts/eventbus/README.md for layer boundaries.

from eventbus.db_conn import check_db, get_db_lock, open_db
from eventbus.delivery_repo import (
    NackResult,
    ack_event,
    ack_event_for_consumer,
    get_consumer_offset,
    nack_event,
)
from eventbus.dlq_repo import redeliver_event, requeue_event
from eventbus.event_repo import (
    count_dlq,
    fetch_dlq,
    fetch_events_since,
    get_seq,
    insert_event,
)
from eventbus.offset_migrator import migrate_legacy_offsets

__all__ = [
    # Connection layer
    "open_db",
    "check_db",
    "get_db_lock",
    # Event repository
    "insert_event",
    "get_seq",
    "fetch_events_since",
    "fetch_dlq",
    "count_dlq",
    # Delivery repository
    "ack_event",
    "nack_event",
    "ack_event_for_consumer",
    "get_consumer_offset",
    "NackResult",
    # DLQ repository
    "requeue_event",
    "redeliver_event",
    # Offset migrator
    "migrate_legacy_offsets",
]
