from dataclasses import dataclass

from scripts.agent.history_selection_policy import HistorySelectionPolicy


@dataclass
class LLMMessage:
    role: str
    content: str


policy = HistorySelectionPolicy(compress_turns=1, protect_turns=1)
# n_protect = 2, n_compress = 2. Need > 4.
history = [
    {"role": "user", "content": "1"},
    {"role": "assistant", "content": "2"},
    {"role": "user", "content": "3"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "5"},
]
result = policy.select_turns_to_compress(history)
print(f"Result: {result}")
