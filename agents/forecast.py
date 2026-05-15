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
    "You are the Forecast Agent for OlympusOS. "
    "Based on current crowd and traffic data from Milan, predict crisis scenarios 5-15 minutes ahead. "
    "Output JSON only: "
    "{\"prediction\": \"description\", \"time_horizon_minutes\": number, \"confidence\": 0.0-1.0, "
    "\"recommended_action\": \"what to do now\", \"severity\": 0.0-1.0}"
)

LOOP_INTERVAL = 5  # seconds
HIGH_SEVERITY_THRESHOLD = 0.7


class ForecastAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="forecast")
        self.model = "deepseek-ai/DeepSeek-V3.2"
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
        """Write the forecast to agent_reports; escalate to events if severity is high."""
        report = {"agent": self.name, "forecast": result, "source_command": command}
        self.redis.rpush("agent_reports", json.dumps(report))
        logger.info(
            "[%s] Forecast → confidence=%s severity=%s horizon=%smin",
            self.name,
            result.get("confidence"),
            result.get("severity"),
            result.get("time_horizon_minutes"),
        )

        severity = float(result.get("severity", 0.0))
        if severity > HIGH_SEVERITY_THRESHOLD:
            event = (
                f"forecast: {result.get('prediction', 'unknown')} "
                f"in {result.get('time_horizon_minutes', '?')}min, severity {severity:.2f}"
            )
            self.redis.rpush("events", event)
            logger.info("[%s] High-severity forecast escalated to orchestrator: %s", self.name, event)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("[%s] Forecast agent started (interval: %ds)", self.name, LOOP_INTERVAL)
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
                        self.write_status({"last_forecast_severity": result.get("severity"), "last_task": cmd.get("task")})

            except Exception as exc:
                logger.error("[%s] Unexpected error: %s", self.name, exc, exc_info=True)

            time.sleep(LOOP_INTERVAL)

        logger.info("[%s] Forecast agent stopped", self.name)
