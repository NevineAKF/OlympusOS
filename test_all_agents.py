import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-9s %(message)s",
    force=True,
)

import json
import os
import threading
import time

import redis
from dotenv import load_dotenv

from agents.forecast import ForecastAgent
from agents.mobility import MobilityAgent
from agents.transit import TransitAgent
from agents.safety import SafetyAgent
from agents.communications import CommunicationsAgent

load_dotenv()

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RUN_DURATION = 15  # seconds

SEED_COMMANDS = [
    {
        "agent": "forecast",
        "task": "predict crowd crisis at San Siro in the next 15 minutes",
        "params": {"location": "San Siro", "current_density": 0.85},
    },
    {
        "agent": "mobility",
        "task": "reroute traffic away from Gate 4 due to crowd surge",
        "params": {"location": "Gate 4", "affected_streets": ["Via Piccolomini", "Via dei Giganti"]},
    },
    {
        "agent": "transit",
        "task": "deploy additional buses to absorb crowd overflow at Lotto metro",
        "params": {"location": "Lotto", "crowd_size": 3000},
    },
    {
        "agent": "safety",
        "task": "assess risk and open emergency corridor at Gate 4",
        "params": {"location": "Gate 4", "incident": "crowd crush risk", "severity": 0.83},
    },
    {
        "agent": "communications",
        "task": "broadcast crowd management instructions for Gate 4 area",
        "params": {"location": "Gate 4", "urgency": "high", "alternative_gate": "Gate 7"},
    },
]


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def seed_commands(r: redis.Redis) -> None:
    for cmd in SEED_COMMANDS:
        r.rpush("commands", json.dumps(cmd))
    logger.info("Seeded %d commands (one per agent)", len(SEED_COMMANDS))


def collect_reports(r: redis.Redis) -> list[dict]:
    pipe = r.pipeline()
    pipe.lrange("agent_reports", 0, -1)
    pipe.delete("agent_reports")
    results = pipe.execute()

    reports = []
    for raw in results[0]:
        try:
            reports.append(json.loads(raw))
        except json.JSONDecodeError:
            reports.append({"raw": raw})
    return reports


def start_agent(agent, threads: list[threading.Thread]) -> None:
    t = threading.Thread(target=agent.run, daemon=True, name=agent.name)
    t.start()
    threads.append(t)
    logger.info("Started agent: %s", agent.name)


def main() -> None:
    r = get_redis()
    r.delete("commands", "agent_reports", "events")

    seed_commands(r)

    agents = [
        ForecastAgent(),
        MobilityAgent(),
        TransitAgent(),
        SafetyAgent(),
        CommunicationsAgent(),
    ]

    threads: list[threading.Thread] = []
    for agent in agents:
        start_agent(agent, threads)
        time.sleep(2)

    logger.info("All 5 agents running for %d seconds…", RUN_DURATION)
    time.sleep(RUN_DURATION)

    for agent in agents:
        agent.stop()
    for t in threads:
        t.join(timeout=7)

    reports = collect_reports(r)

    print("\n" + "=" * 60)
    print(f"  Reports from all agents  ({len(reports)} total)")
    print("=" * 60)
    if reports:
        for i, report in enumerate(reports, 1):
            agent_name = report.get("agent", "unknown")
            print(f"\n[{i}] {agent_name.upper()}")
            print(json.dumps(report, indent=4))
    else:
        print("\n  (no reports generated)")
    print()


if __name__ == "__main__":
    main()
