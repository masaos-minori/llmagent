# Implementation: docs/06_eventbus_90_inconsistencies_and_known_issues.md — resolved items update (req #33)

## Goal

Add two resolved items to the known-issues document recording the old `retry_count` behavior and the 60-second DLQ delay as resolved, with references to the implementing requirements. Add a delivery lifecycle model entry to the "Adopted execution model" section.

## Scope

- Add 2 rows to the "Resolved items" table (or create the table if it only has schema vs impl differences)
- Add a "Delivery lifecycle model" subsection under an "Adopted execution model" section
- Unconfirmed items table: move `/health HTTP status` to resolved (req #19 resolved it as 200 always)

## Assumptions

- req #24–#30 are implemented before publishing this update
- The current document has no "Resolved items" table — only "Schema vs implementation differences" and "Unconfirmed items"
- A "Resolved items" section needs to be added

## Implementation

### Target file

`docs/06_eventbus_90_inconsistencies_and_known_issues.md`

### Procedure

1. Add `## Resolved items` section after "Schema vs implementation differences"
2. Add resolved items table with 2 rows for the old `retry_count` and 60s DLQ delay
3. Add `## Adopted execution model` section at the end with delivery lifecycle model
4. Move `/health HTTP status` from Unconfirmed to Resolved (status is 200 always, per req #19)

### Method

Append sections to existing file.

### Details

**New "Resolved items" section:**

```markdown
## Resolved items

| Issue | Resolution | References |
|---|---|---|
| `retry_count` incremented only on DLQ requeue (not on delivery failure) | Fixed in req #24–#28. New fields: `delivery_failure_count` (incremented on nack), `dlq_requeue_count` (incremented on requeue). `retry_count` is deprecated. | req #24, #28, `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| DLQ promotion delayed up to 60 s (background loop only) | Fixed in req #26. DLQ promotion now happens inline when `delivery_failure_count >= max_retry`. Background loop retained as orphan sweep only (req #30). | req #26, #30, `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| `/health` HTTP status on degraded state (200 vs 503) | By design: always 200. Status conveyed in `status` field (`"ok"` or `"degraded"`). | req #19 |
```

**New "Adopted execution model" section:**

```markdown
## Adopted execution model

### Delivery lifecycle model (req #24–#30)

- Consumer outcome: `POST /events/{id}/ack` and `POST /events/{id}/nack`
- Delivery failure count: `delivery_failure_count` (per event; never resets)
- DLQ promotion: inline on nack when `delivery_failure_count >= max_retry`; background loop as safety-net sweep only
- Offset advancement: on explicit ack via `?consumer_id=X` (not on delivery)
- State transitions: LIVE → ACKED (ack), LIVE/RETRY → DLQ (threshold), DLQ → LIVE (requeue)
```

**Remove from Unconfirmed items table:**
Remove the `/health HTTP status on degraded state` row (moved to Resolved).

**Update Schema vs implementation differences table:**
- `acked_at`: change "Reserved/unused" to "Set by `POST /events/{id}/ack`"
- `retry_count`: add "deprecated" note

## Validation plan

| Check | Command | Target |
|---|---|---|
| Resolved table present | `grep "## Resolved items" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 1 result |
| retry_count entry | `grep "retry_count.*incremented only" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 1 result |
| 60s DLQ entry | `grep "60" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | match in Resolved |
| Execution model section | `grep "Delivery lifecycle model" docs/06_eventbus_90_inconsistencies_and_known_issues.md` | 1 result |
