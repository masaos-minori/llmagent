"""Shared column name constants across eventbus layers.

Column names derived from events table DDL in schema.sql. These are safe from SQL
injection because they originate from the schema definition, not user input.
"""

# Shared column constants — used by all layers
_COL_EVENT_ID = "event_id"
_COL_SEQ = "seq"
_COL_ACKED_AT = "acked_at"
_COL_DLQ_AT = "dlq_at"

# Shared column constants — used by all layers
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"

__all__ = [
    "_COL_EVENT_ID",
    "_COL_SEQ",
    "_COL_ACKED_AT",
    "_COL_DLQ_AT",
    "_COL_DELIVERY_FAILURE_COUNT",
    "_COL_CYCLE_FAILURE_COUNT",
    "_COL_DLQ_REQUEUE_COUNT",
    "_COL_REDISTRIBUTED_FROM",
    "_COL_CONSUMER_DELIVERY_FAILURE_COUNT",
    "_COL_CONSUMER_ID",
    "_COL_OFFSET",
]
