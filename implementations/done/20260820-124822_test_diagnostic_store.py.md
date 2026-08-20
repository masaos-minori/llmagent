# Implementation Procedure: Add fetch decrypt round-trip test to TestEncryption

## Goal
Add a unit test to `tests/agent/test_diagnostic_store.py` (in `TestEncryption`, alongside the existing `save(encrypt=True)` tests) that calls `store.save(session_id, kind, content, encrypt=True)` with a configured `encryption_key`, then calls `store.fetch(session_id)`, and asserts the returned `content` equals the original plaintext — exercising the decrypt branch inside `DiagnosticStore.fetch()` itself, not a manual `Fernet(...).decrypt(...)` call in the test.

## Scope
- Target file: `tests/agent/test_diagnostic_store.py`
- Add one test method to `TestEncryption` class

## Assumptions
- The test should follow the existing `test_save_encrypt_true_with_configured_key` pattern
- Use same `fake_db` + `_FakeConfigLoader` setup
- Instead of manually decrypting with `Fernet(...).decrypt(...)`, call `store.fetch()` and assert on returned content
- Insert test after `test_save_encrypt_true_with_configured_key` (line 332) and before `test_save_encrypt_true_without_configured_key_is_noop` (line 334)

## Design decisions
- Follow existing test pattern for encryption tests
- Assert on `store.fetch()` output directly, not manual decryption
- This tests the actual decrypt branch in `DiagnosticStore.fetch()`

## Implementation
### Target file
`tests/agent/test_diagnostic_store.py`

### Procedure
1. Add new test method `test_fetch_decrypts_content_saved_with_encrypt_true` to `TestEncryption`

### Method
Direct code addition using exact line matching

### Details
**Location:** After line 332 (after `test_save_encrypt_true_with_configured_key`)

**New test method:**
```python
    def test_fetch_decrypts_content_saved_with_encrypt_true(
        self, fake_db: _FakeSQLiteHelper
    ) -> None:
        """fetch() should decrypt ciphertext saved via save(encrypt=True)."""
        key = Fernet.generate_key().decode("utf-8")
        plaintext = '{"turn": 1}'
        fake_cfg_loader = _FakeConfigLoader(
            {"diagnostics": {"encryption_key": key, "retention_days": 30}}
        )
        store = DiagnosticStore()
        with (
            patch("db.helper.SQLiteHelper", side_effect=lambda _: fake_db),
            patch("shared.config_loader.ConfigLoader", return_value=fake_cfg_loader),
        ):
            store.save(1, kind="k", content=plaintext, encrypt=True)
            entries = store.fetch(1)
        assert len(entries) == 1
        assert entries[0]["kind"] == "k"
        # This assertion exercises the decrypt branch inside fetch() itself
        assert entries[0]["content"] == plaintext
```

## Compatibility considerations
- Test-only change, no production code impact
- Uses existing `_FakeConfigLoader` and `fake_db` fixtures

## Security considerations
- None - test only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Run `uv run pytest tests/agent/test_diagnostic_store.py -v` - all pass including new test
- Run full test suite `uv run pytest` - no new failures

## Out of scope
- No changes to production code

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-213537_require.md
- Source plan: plans/20260819-162837_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-124822
- Related target files: tests/agent/test_diagnostic_store.py