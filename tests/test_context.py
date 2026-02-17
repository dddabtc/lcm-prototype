from lcm.compactor import Compactor
from lcm.context import ContextManager
from lcm.dag import SummaryDAG
from lcm.store import Message


def _msg(i: int) -> Message:
    return Message(id=str(i), timestamp="2026-01-01T00:00:00+00:00", role="user", content="token " * 30)


def test_context_soft_and_hard_compression():
    comp = Compactor()
    dag = SummaryDAG()
    ctx = ContextManager(compactor=comp, dag=dag, tau_soft=60, tau_hard=120, recent_window=2)

    for i in range(6):
        ctx.add_message(_msg(i))

    active = ctx.get_active_context()
    assert active["token_estimate"] <= 120
    assert len(active["summaries"]) >= 1
    assert len(active["recent_messages"]) <= 6
