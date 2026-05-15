import json
import logging
import os
import time
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from agents.base_agent import BaseAgent

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are the Mobility Control Agent for OlympusOS managing Milan traffic during mass events. "
    "Output JSON only: "
    "{\"action\": \"reroute|signal_change|road_closure|bus_lane\", \"target_street\": \"street name\", "
    "\"alternative_route\": \"description\", \"estimated_improvement\": \"0-100%\", "
    "\"implementation_time_seconds\": number}"
)

LOOP_INTERVAL = 5  # seconds


class MobilityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="mobility")
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.client = OpenAI(
            api_key=os.getenv("FEATHERLESS_API_KEY"),
            base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_own_commands(self) -> list[dict[str, Any]]:
        """Drain the shared 'commands' list and return only entries addressed to this agent."""
        pipe = self.redis.pipeline()
        pipe.lrange("commands", 0, -1)
        pipe.delete("commands")
        results = pipe.execute()
        raw_list: list[str] = results[0]

        mine: list[dict[str, Any]] = []
        requeue: list[str] = []
        for raw in raw_list:
            try:
                cmd = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("[%s] Skipping malformed command: %s", self.name, raw)
                continue
            if cmd.get("agent") == self.name:
                mine.append(cmd)
            else:
                requeue.append(raw)

        if requeue:
            self.redis.rpush("commands", *requeue)

        return mine

    def _analyze(self, command: dict[str, Any]) -> dict[str, Any] | None:
        task = command.get("task", "")
        params = command.get("params", {})
        prompt = f"Task: {task}\nParams: {json.dumps(params)}\n\nAnalyze and respond with JSON only."

        try:
            with BaseAgent._API_LOCK:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=400,
                )
            content = response.choices[0].message.content
            logger.debug("[%s] RAW LLM response:\n%s", self.name, content)

            if not content:
                logger.warning("[%s] LLM returned empty content (finish_reason=%s)", self.name, response.choices[0].finish_reason)
                return None

            cleaned = content.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```")
                cleaned = parts[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

            result = json.loads(cleaned)
            logger.debug("[%s] Parsed result: %s", self.name, json.dumps(result))
            return result
        except json.JSONDecodeError as exc:
            logger.error("[%s] LLM returned non-JSON: %s", self.name, exc)
            return None
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", self.name, exc, exc_info=True)
            return None

    def _report(self, result: dict[str, Any], command: dict[str, Any]) -> None:
        """Write the mobility action to agent_reports."""
        report = {"agent": self.name, "mobility_action": result, "source_command": command}
        self.redis.rpush("agent_reports", json.dumps(report))
        logger.info(
            "[%s] Action → %s on %s (improvement: %s)",
            self.name,
            result.get("action"),
            result.get("target_street"),
            result.get("estimated_improvement"),
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("[%s] Mobility agent started (interval: %ds)", self.name, LOOP_INTERVAL)
        self.running = True

        while self.running:
            try:
                commands = self._read_own_commands()

                if not commands:
                    logger.debug("[%s] No commands — sleeping", self.name)
                    time.sleep(LOOP_INTERVAL)
                    continue

                logger.info("[%s] Processing %d command(s)", self.name, len(commands))
                for cmd in commands:
                    result = self._analyze(cmd)
                    if result:
                        self._report(result, cmd)
                        self.write_status({"last_action": result.get("action"), "last_street": result.get("target_street")})

            except Exception as exc:
                logger.error("[%s] Unexpected error: %s", self.name, exc, exc_info=True)

            time.sleep(LOOP_INTERVAL)

        logger.info("[%s] Mobility agent stopped", self.name)
