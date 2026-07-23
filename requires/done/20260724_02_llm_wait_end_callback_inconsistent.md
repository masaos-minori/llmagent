# LLMTurnRunner.run() からの LLMTransportError 時、_on_llm_wait_end コールバックが両パスで呼ばれない

## Priority

Critical

## Summary

`LLMTurnRunner.run()` から `LLMTransportError` が返される場合、コールバック `_on_llm_wait_end` の呼び出しがパスによって分岐している。`result.exception is not None` パスでは呼ばれず、`raise` パスでは呼ばれる。

## Problem

`orchestrator.py:424-435` (result.exception is not None):

```python
if result.exception is not None:
    handle_llm_transport_error(result.exception, ctx, self._diagnostic_store)
    if self._on_error:
        self._on_error(result.exception)
else:
    if self._on_turn_end:
        self._on_turn_end()
return result
```

`result.exception is not None` の場合、`_on_llm_wait_end` も `_on_turn_end` も呼ばれない。

一方 `orchestrator.py:437-450` (raise パス):

```python
except LLMTransportError as e:
    handle_llm_transport_error(e, ctx, self._diagnostic_store)
    if self._on_llm_wait_end:
        self._on_llm_wait_end()
    if self._on_error:
        self._on_error(e)
    return TurnResult(...)
```

`raise` パスでは `_on_llm_wait_end` が呼ばれる。

## Root Cause

`LLMTurnRunner.run()` が例外を返す場合と raise する場合の2つのパスがあり、それぞれでコールバックの呼び出しが異なる。

## Fix Direction

`result.exception is not None` パスでも `_on_llm_wait_end` を呼ぶように統一する。

## Acceptance Criteria

- [ ] `LLMTurnRunner.run()` が exception を返す場合、_on_llm_wait_end が呼ばれる
- [ ] `LLMTurnRunner.run()` が raise する場合、_on_llm_wait_end が呼ばれる
- [ ] 両パスで同じコールバック呼び出し順序になる
