# メモリ注入のトークン爆発

## 深刻度: 低

## 概要

`StartupOrchestrator._inject_session_memories()` で `on_session_start()` が大量のメモリを返すと、
システムプロンプトが膨大になりLLMのトークン制限を超える。上限チェックがない。

## 該当コード

`scripts/agent/startup.py:331-348`

```python
async def _inject_session_memories(self) -> None:
    ctx = self._ctx
    if ctx.services is None or ctx.services.memory is None:
        return
    memory_snippets = ctx.services.memory.on_session_start(
        session_id=ctx.session.session_id,
        user_id=str(ctx.user.id),
    )
    if memory_snippets:
        memory_block = "\n\n[Relevant memories]\n" + "\n".join(
            f"- {snippet.text}" for snippet in memory_snippets
        )
        initial_prompt = initial_prompt + memory_block
```

## 問題の詳細

1. `on_session_start()` はセッションに関連するメモリを返す
2. セッションが長い場合、多数のメモリが返る可能性がある
3. システムプロンプトにそのまま連結される
4. LLMのトークン制限（例: 4096トークン）を超えると、LLMがエラーを返すか、
   コンテキストが切り捨てられる
5. 上限チェックが実装されていない

## 影響

- 長時間のセッションでメモリが累積し、トークン制限超過
- エージェントが正常に動作しなくなる
- ユーザーにはわかりにくいエラーが表示される

## 修正案

```python
async def _inject_session_memories(self) -> None:
    ctx = self._ctx
    if ctx.services is None or ctx.services.memory is None:
        return
    memory_snippets = ctx.services.memory.on_session_start(
        session_id=ctx.session.session_id,
        user_id=str(ctx.user.id),
    )
    if memory_snippets:
        # Limit to prevent token explosion
        max_snippets = 10
        limited_snippets = memory_snippets[:max_snippets]
        memory_block = "\n\n[Relevant memories]\n" + "\n".join(
            f"- {snippet.text}" for snippet in limited_snippets
        )
        initial_prompt = initial_prompt + memory_block
```
