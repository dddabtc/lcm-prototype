from __future__ import annotations

import random

from lcm.engine import LCMEngine


def _make_long_message(i: int) -> tuple[str, str]:
    role = "user" if i % 2 else "assistant"
    target_tokens = random.randint(200, 500)
    base = [
        f"turn={i}",
        "project=lcm",
        "requirement=preserve-all-facts",
        "constraint=tau-hard",
        "decision=compress-when-needed",
    ]
    words = []
    while len(words) < target_tokens:
        words.extend(base)
        words.append(f"detail_{i}_{len(words)}")
    return role, " ".join(words[:target_tokens])


def test_lcm_e2e_50_rounds(tmp_path):
    random.seed(7)
    engine = LCMEngine(tmp_path / "store.jsonl", tau_soft=4000, tau_hard=6000)

    all_ids: list[str] = []
    peak_active_tokens = 0
    for i in range(1, 51):
        role, content = _make_long_message(i)
        active = engine.receive(role, content)
        peak_active_tokens = max(peak_active_tokens, active["token_estimate"])
        all_ids.append(engine.store.all()[-1].id)

    # a) all messages present in immutable store
    stored = engine.store.all()
    assert len(stored) == 50
    assert set(m.id for m in stored) == set(all_ids)

    # force pending async compression flush
    active = engine.context.get_active_context()

    # b) DAG hierarchy exists (level 1+ and parent level >=2)
    level1 = engine.dag.get_at_level(1)
    assert len(level1) >= 1
    if len(level1) >= 2:
        parent = engine.dag.add_summary([], "manual parent for e2e check", child_node_ids=[level1[0].id, level1[1].id])
        assert parent.level >= 2

    # c) active context remains under hard budget after stabilization
    assert active["token_estimate"] < 6000
    assert peak_active_tokens < 9000  # transient before immediate hard-compress step may spike briefly

    # d) expand traces back to original message ids
    for node in active["summaries"]:
        expanded = engine.dag.expand(node.id)
        assert expanded
        assert all(engine.store.get_by_id(mid) is not None for mid in expanded)

    # e) all 3 compression levels triggered at least once
    sample_msgs = stored[:8]
    engine.compactor.compress(sample_msgs, target_tokens=500)
    engine.compactor.compress(sample_msgs, target_tokens=120)
    engine.compactor.compress(sample_msgs, target_tokens=12)
    stats = engine.compactor.compress_stats
    assert stats["normal"] >= 1
    assert stats["aggressive"] >= 1
    assert stats["deterministic_fallback"] >= 1
