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
    "You are the Public Safety Agent for OlympusOS coordinating emergency response in Milan. "
    "Output JSON only: "
    "{\"risk_level\": \"low|medium|high|critical\", "
    "\"action\": \"open_corridor|dispatch_ambulance|evacuate|secure_perimeter\", "
    "\"location\": \"where\", \"corridor_route\": \"description\", "
    "\"response_time_seconds\": number, \"units_needed\": number}"
)

LOOP_INTERVAL = 5  # seconds
ESCALATION_RISK_LEVELS = {"high", "critical"}


class SafetyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="safety")
        self.model = "MiniMaxAI/MiniMax-M2.5"
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
                    max_tokens=600,
                )
            content = response.choices[0].message.content
            logger.debug("[%s] RAW LLM response:\n%s", self.name, content)

            if not content:
                logger.warning("[%s] LLM returned empty content (finish_reason=%s)", self.name, response.choices[0].finish_reason)
                return None

            import re
            cleaned = content.strip()
            if cleaned.startswith("```"):
                parts = cleaned.split("```")
                cleaned = parts[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)

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
        """Write the safety response to agent_reports; escalate if risk is high or critical."""
        report = {"agent": self.name, "safety_response": result, "source_command": command}
        self.redis.rpush("agent_reports", json.dumps(report))
        logger.info(
            "[%s] Response → risk=%s action=%s location=%s units=%s",
            self.name,
            result.get("risk_level"),
            result.get("action"),
            result.get("location"),
            result.get("units_needed"),
        )

        risk_level = result.get("risk_level", "low")
        if risk_level in ESCALATION_RISK_LEVELS:
            event = (
                f"safety: {risk_level} risk at {result.get('location', 'unknown')}, "
                f"action={result.get('action')}"
            )
            self.redis.rpush("events", event)
            logger.info("[%s] %s risk escalated to orchestrator: %s", self.name, risk_level.upper(), event)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("[%s] Safety agent started (interval: %ds)", self.name, LOOP_INTERVAL)
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
                        self.write_status({"last_risk_level": result.get("risk_level"), "last_action": result.get("action")})

            except Exception as exc:
                logger.error("[%s] Unexpected error: %s", self.name, exc, exc_info=True)

            time.sleep(LOOP_INTERVAL)

        logger.info("[%s] Safety agent stopped", self.name)
