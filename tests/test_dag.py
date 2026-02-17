from lcm.dag import SummaryDAG
from lcm.store import Message


def _msg(i: int) -> Message:
    return Message(id=f"m{i}", timestamp="2026-01-01T00:00:00+00:00", role="user", content=f"content {i}")


def test_add_summary_and_expand():
    dag = SummaryDAG()
    messages = [_msg(1), _msg(2)]
    node = dag.add_summary(messages, "summary l1")

    assert node.level == 1
    assert dag.expand(node.id) == ["m1", "m2"]


def test_hierarchical_level_from_children():
    dag = SummaryDAG()
    n1 = dag.add_summary([_msg(1)], "s1")
    n2 = dag.add_summary([_msg(2)], "s2")
    n3 = dag.add_summary([], "parent", child_node_ids=[n1.id, n2.id])

    assert n3.level == 2
    assert dag.expand(n3.id) == ["m1", "m2"]


def test_get_at_level():
    dag = SummaryDAG()
    n1 = dag.add_summary([_msg(1)], "s1")
    n2 = dag.add_summary([_msg(2)], "s2")
    dag.add_summary([], "parent", child_node_ids=[n1.id, n2.id])

    lvl1 = dag.get_at_level(1)
    lvl2 = dag.get_at_level(2)
    assert len(lvl1) == 2
    assert len(lvl2) == 1
