import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    def __init__(self, name: str) -> None:
        self.name = name
        self.running = False
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: redis.Redis = redis.Redis.from_url(redis_url, decode_responses=True)
        logger.info("Agent '%s' initialised (Redis: %s)", self.name, redis_url)

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    def read_events(self) -> list[str]:
        """Atomically drain all entries from the 'events' list."""
        pipe = self.redis.pipeline()
        pipe.lrange("events", 0, -1)
        pipe.delete("events")
        results = pipe.execute()
        return results[0]

    def read_agent_reports(self) -> list[str]:
        """Atomically drain all entries from the 'agent_reports' list."""
        pipe = self.redis.pipeline()
        pipe.lrange("agent_reports", 0, -1)
        pipe.delete("agent_reports")
        results = pipe.execute()
        return results[0]

    def write_command(self, command: dict[str, Any]) -> None:
        """Append a command (serialised as JSON) to the 'commands' list."""
        self.redis.rpush("commands", json.dumps(command))

    def write_status(self, status: dict[str, Any]) -> None:
        """Persist this agent's current status to Redis."""
        self.redis.set(f"status:{self.name}", json.dumps(status))

    def log_decision(self, decision: dict[str, Any]) -> None:
        """Log a decision to the console. Wire up PostgreSQL here when ready."""
        logger.info("[%s] Decision: %s", self.name, json.dumps(decision))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Signal the run loop to exit after the current iteration."""
        self.running = False
        logger.info("[%s] Stop signal received", self.name)

    @abstractmethod
    def run(self) -> None:
        """Main agent loop — subclasses must implement this."""
