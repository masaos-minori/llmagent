class CompressResult:
    def __init__(
        self,
        compressed_count,
        protected_count,
        summary_added,
        is_fallback=False,
        error=None,
    ):
        self.compressed_count = compressed_count
        self.protected_count = protected_count
        self.summary_added = summary_added
        self.is_fallback = is_fallback
        self.error = error

    def __repr__(self):
        return (
            f"CompressResult(..., is_fallback={self.is_fallback}, error={self.error})"
        )


class HistorySelectionPolicy:
    @staticmethod
    def classify_importance(m):
        return 0.5


class HistoryManager:
    def __init__(self, protect_turns=2):
        self._protect_turns = protect_turns
        self._char_limit = 1

    def count_chars(self, history):
        return sum(len(str(m.get("content", ""))) for m in history)

    def _is_over_char_limit(self, history):
        return self.count_chars(history) > self._char_limit

    def _build_protected_ids(self, history):
        protected_ids = {id(m) for m in history if m["role"] == "system"}
        turn_msgs = [m for m in history if m["role"] != "system"]
        n_protect = self._protect_turns * 2
        for m in turn_msgs[-n_protect:] if n_protect > 0 else []:
            protected_ids.add(id(m))
        return protected_ids

    def _fallback_truncate(self, history):
        protected_ids = self._build_protected_ids(history)
        candidates = sorted(
            (m for m in history if id(m) not in protected_ids),
            key=lambda x: HistorySelectionPolicy.classify_importance(x),
        )
        new_history = list(history)
        for msg in candidates:
            if not self._is_over_char_limit(new_history):
                break
            new_history = [m for m in new_history if m is not msg]
        return new_history


mgr = HistoryManager(protect_turns=2)
h = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
result = mgr._fallback_truncate(h)
print(f"Original: {h}")
print(f"Result: {result}")
assert result == h
