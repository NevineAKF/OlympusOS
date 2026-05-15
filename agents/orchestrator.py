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
    "You are the Orchestrator Agent for OlympusOS, an autonomous urban operations system. "
    "Your job is to coordinate exactly 6 specialist agents during mass-scale events in Milan. "
    "The agents are: 'perception', 'forecast', 'mobility', 'transit', 'safety', 'communications'. "
    "You MUST use these exact lowercase names. "
    "You read events, decide priority, delegate tasks, and resolve conflicts. "
    "Output decisions as valid JSON only with this exact format: "
    "{\"priority\": \"high|medium|low\", \"commands\": [{\"agent\": \"one of the 6 names\", \"task\": \"description\", \"params\": {}}]}"
)

_RESPONSE_FORMAT_HINT = (
    'Respond with a JSON object in this exact format:\n'
    '{"priority": "<high|medium|low>", "commands": [{"agent": "<name>", "task": "<task>", "params": {}}]}'
)

LOOP_INTERVAL = 3  # seconds


class OrchestratorAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(name="orchestrator")
        self.model = "deepseek-ai/DeepSeek-V3.1"
        self.client = OpenAI(
            api_key=os.getenv("FEATHERLESS_API_KEY"),
            base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_context(self, events: list[str], reports: list[str]) -> str:
        return json.dumps({"events": events, "agent_reports": reports})

    def _call_llm(self, context: str) -> dict[str, Any]:
        with BaseAgent._API_LOCK:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Current state:\n{context}\n\n{_RESPONSE_FORMAT_HINT}"},
                ],
                temperature=0.2,
                max_tokens=500,
            )

        content = response.choices[0].message.content
        logger.debug("[%s] RAW LLM response:\n%s", self.name, content)

        if not content:
            logger.warning("[%s] LLM returned empty content (finish_reason=%s)", self.name, response.choices[0].finish_reason)
            return {"priority": "low", "commands": []}

        cleaned = content.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            logger.debug("[%s] Cleaned response (after stripping markdown):\n%s", self.name, cleaned)

        result = json.loads(cleaned)
        logger.debug("[%s] Parsed result: %s", self.name, json.dumps(result))
        return result

    def _dispatch(self, decision: dict[str, Any]) -> None:
        """Write every command from a decision to Redis and log the decision."""
        self.log_decision(decision)
        commands: list[dict[str, Any]] = decision.get("commands", [])
        for cmd in commands:
            self.write_command(cmd)
            logger.info("[%s] Dispatched → agent=%s task=%s", self.name, cmd.get("agent"), cmd.get("task"))
        self.write_status({"priority": decision.get("priority"), "last_commands": len(commands)})

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        logger.info("[%s] Orchestrator started (interval: %ds)", self.name, LOOP_INTERVAL)
        self.running = True

        while self.running:
            try:
                events = self.read_events()
                reports = self.read_agent_reports()

                if not events and not reports:
                    logger.debug("[%s] Nothing to process — sleeping", self.name)
                    time.sleep(LOOP_INTERVAL)
                    continue

                logger.info(
                    "[%s] Processing %d event(s), %d report(s)",
                    self.name, len(events), len(reports),
                )
                context = self._build_context(events, reports)
                decision = self._call_llm(context)
                self._dispatch(decision)

            except json.JSONDecodeError as exc:
                logger.error("[%s] LLM returned non-JSON response: %s", self.name, exc)
            except Exception as exc:
                logger.error("[%s] Unexpected error: %s", self.name, exc, exc_info=True)

            time.sleep(LOOP_INTERVAL)

        logger.info("[%s] Orchestrator stopped", self.name)
