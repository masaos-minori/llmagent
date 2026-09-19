"""Shared column name constants across eventbus layers.

Column names derived from events table DDL in schema.sql. These are safe from SQL
injection because they originate from the schema definition, not user input.
"""

# Core event columns — used by all layers
_COL_EVENT_ID = "event_id"
_COL_SEQ = "seq"
_COL_ACKED_AT = "acked_at"
_COL_DLQ_AT = "dlq_at"

__all__ = [
    "_COL_EVENT_ID",
    "_COL_SEQ",
    "_COL_ACKED_AT",
    "_COL_DLQ_AT",
]
