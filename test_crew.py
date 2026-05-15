import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-9s %(message)s",
    force=True,
)

from agents.crew import run_demo_scenario

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  OlympusOS CrewAI Demo — San Siro Mass Evacuation")
    print("=" * 60 + "\n")

    result = run_demo_scenario()

    print("\n" + "=" * 60)
    print("  FINAL ORCHESTRATOR DECISION")
    print("=" * 60)
    print(result)
    print()
