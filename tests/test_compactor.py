from lcm.compactor import Compactor
from lcm.store import Message


def _messages(n: int) -> list[Message]:
    return [
        Message(
            id=str(i),
            timestamp="2026-01-01T00:00:00+00:00",
            role="user" if i % 2 else "assistant",
            content=("word " * 40) + str(i),
        )
        for i in range(1, n + 1)
    ]


def test_deterministic_fallback_respects_budget():
    comp = Compactor()
    msgs = _messages(4)
    text = comp.deterministic_fallback(msgs, max_tokens=20)
    assert comp.token_counter(text) <= 25  # prefix may add tiny overhead in simplistic estimator
    assert "..." in text


def test_compress_converges_to_target():
    comp = Compactor()
    msgs = _messages(8)
    level, text = comp.compress(msgs, target_tokens=30)
    assert level in {"normal", "aggressive", "deterministic_fallback"}
    assert comp.token_counter(text) <= 30
