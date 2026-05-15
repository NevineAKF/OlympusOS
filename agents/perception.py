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
    "You are the Perception Agent for OlympusOS, monitoring crowd dynamics in Milan during mass events. "
    "Your job is to analyze sensor data and video feeds, detect anomalies, and report them. "
    "You watch for: crowd density anomalies, congestion patterns, security risks, infrastructure failures. "
    "Output observations as valid JSON only with format: "
    "{\"observation\": \"description\", \"severity\": 0.0-1.0, \"location\": \"where\", "
    "\"type\": \"crowd_anomaly|congestion|security|infrastructure\"}"
)

LOOP_INTERVAL = 5  # seconds
HIGH_SEVERITY_THRESHOLD = 0.7


class PerceptionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="perception")
        self.model = "mistralai/Mistral-Nemo-Instruct-2407"
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

        # Put commands for other agents back
        if requeue:
            self.redis.rpush("commands", *requeue)

        return mine

    def _analyze(self, command: dict[str, Any]) -> dict[str, Any] | None:
        task = command.get("task", "")
        params = command.get("params", {})
        prompt = f"Task: {task}\nParams: {json.dumps(params)}\n\nAnalyze and respond with JSON only."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=300,
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
            logger.debug("[%s] Parsed observation: %s", self.name, json.dumps(result))
            return result
        except json.JSONDecodeError as exc:
            logger.error("[%s] LLM returned non-JSON: %s", self.name, exc)
            return None
        except Exception as exc:
            logger.error("[%s] LLM call failed: %s", self.name, exc, exc_info=True)
            return None

    def _report(self, observation: dict[str, Any], command: dict[str, Any]) -> None:
        """Write the observation to agent_reports; escalate to events if severity is high."""
        report = {"agent": self.name, "observation": observation, "source_command": command}
        self.redis.rpush("agent_reports", json.dumps(report))
        logger.info(
            "[%s] Report → type=%s severity=%s location=%s",
            self.name,
            observation.get("type"),
            observation.get("severity"),
            observation.get("location"),
        )

        severity = float(observation.get("severity", 0.0))
        if severity > HIGH_SEVERITY_THRESHOLD:
            event = (
                f"{observation.get('type', 'anomaly')} at {observation.get('location', 'unknown')}, "
                f"severity {severity:.2f}"
            )
            self.redis.rpush("events", event)
            logger.info("[%s] High-severity event escalated to orchestrator: %s", self.name, event)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("[%s] Perception agent started (interval: %ds)", self.name, LOOP_INTERVAL)
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
                    observation = self._analyze(cmd)
                    if observation:
                        self._report(observation, cmd)

            except Exception as exc:
                logger.error("[%s] Unexpected error: %s", self.name, exc, exc_info=True)

            time.sleep(LOOP_INTERVAL)

        logger.info("[%s] Perception agent stopped", self.name)
