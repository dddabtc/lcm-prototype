from pathlib import Path

from lcm.engine import LCMEngine


def main() -> None:
    engine = LCMEngine(store_path=Path("./data/messages.jsonl"), tau_soft=80, tau_hard=150)

    for role, content in [
        ("user", "Hello, can you track my long context?"),
        ("assistant", "Sure. I will maintain summaries and recent details."),
        ("user", "Here is a long update: " + "details " * 60),
    ]:
        active = engine.receive(role, content)
        print("--- ACTIVE CONTEXT ---")
        print("recent:", len(active["recent_messages"]))
        print("summaries:", len(active["summaries"]))
        print("tokens:", active["token_estimate"])


if __name__ == "__main__":
    main()
