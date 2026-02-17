from datetime import datetime, timedelta, timezone

from lcm.store import ImmutableStore


def test_append_and_get_by_id(tmp_path):
    store = ImmutableStore(tmp_path / "store.jsonl")
    msg = store.append("user", "hello")

    loaded = store.get_by_id(msg.id)
    assert loaded is not None
    assert loaded.content == "hello"
    assert loaded.role == "user"


def test_query_time_range(tmp_path):
    store = ImmutableStore(tmp_path / "store.jsonl")
    m1 = store.append("user", "first")
    m2 = store.append("assistant", "second")

    t1 = datetime.fromisoformat(m1.timestamp)
    t2 = datetime.fromisoformat(m2.timestamp)

    out = store.query_time_range(t1 - timedelta(seconds=1), t2 + timedelta(seconds=1))
    assert [m.id for m in out] == [m1.id, m2.id]


def test_get_by_ids_preserves_order(tmp_path):
    store = ImmutableStore(tmp_path / "store.jsonl")
    m1 = store.append("user", "a")
    m2 = store.append("assistant", "b")
    m3 = store.append("user", "c")

    out = store.get_by_ids([m3.id, m1.id])
    assert [m.id for m in out] == [m3.id, m1.id]
