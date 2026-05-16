"""
OlympusOS FastAPI backend.
  WebSocket /ws  — streams simulation state + agent events to browser
  POST /run_demo — triggers 60-second demo sequence
"""
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

# Allow importing agents/ from project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("olympusos")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ── Config ──────────────────────────────────────────────────────────────────
FEATHERLESS_KEY  = os.getenv("FEATHERLESS_API_KEY", "")
FEATHERLESS_URL  = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")
SPEECHMATICS_KEY = os.getenv("SPEECHMATICS_API_KEY", "")
SUMO_DIR         = ROOT / "sumo" / "output"
AUDIO_FILE       = ROOT / "audio" / "emergency_call.wav"

llm = OpenAI(api_key=FEATHERLESS_KEY, base_url=FEATHERLESS_URL)

SCENARIO = (
    "Metro M5 has failed. 80,000 fans are leaving San Siro stadium. "
    "Crowd anomaly detected at Gate 4, severity 0.83, risk of crush imminent."
)

# Agent definitions: model, home location, LLM prompt
AGENTS = {
    "perception": {
        "model": "mistralai/Mistral-Nemo-Instruct-2407",
        "lat": 45.4783, "lng": 9.1238, "alt": 10,
        "system": "You are a crowd perception AI. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Analyze Gate 4. Return JSON: "
            '{"observation":"...","severity":0.83,"location":"Gate 4, San Siro","type":"crowd_anomaly"}'
        ),
    },
    "forecast": {
        "model": "deepseek-ai/DeepSeek-V3.2",
        "lat": 45.4856, "lng": 9.1409, "alt": 10,
        "system": "You are a crisis forecast AI. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Predict the next 10 minutes. Return JSON: "
            '{"prediction":"...","time_horizon_minutes":10,"confidence":0.87,"severity":0.91,"recommended_action":"..."}'
        ),
    },
    "mobility": {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "lat": 45.4790, "lng": 9.1280, "alt": 10,
        "system": "You are a traffic mobility controller. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Design a traffic rerouting plan. Return JSON: "
            '{"action":"signal_change","target_street":"Via Giuseppe Verdi","alternative_route":"Via Harar","estimated_improvement":"30%"}'
        ),
    },
    "transit": {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "lat": 45.4940, "lng": 9.1330, "alt": 10,
        "system": "You are a public transit coordinator. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Design emergency bus deployment. Return JSON: "
            '{"action":"deploy_buses","vehicles_needed":50,"route":"San Siro → Lampugnano → Centrale","capacity":5000,"estimated_wait_minutes":4}'
        ),
    },
    "safety": {
        "model": "mistralai/Mistral-Nemo-Instruct-2407",
        "lat": 45.4810, "lng": 9.1245, "alt": 10,
        "system": "You are a public safety commander. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Design emergency response. Return JSON: "
            '{"risk_level":"critical","action":"open_corridor","corridor_route":"Via Leonardo da Vinci","response_time_seconds":90,"units_needed":12}'
        ),
    },
    "communications": {
        "model": "mistralai/Mistral-Nemo-Instruct-2407",
        "lat": 45.4781, "lng": 9.1240, "alt": 10,
        "system": "You are a public communications officer. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Write a bilingual safety broadcast. Return JSON: "
            '{"message_en":"Please use Gates 2, 6, 8. Emergency buses available at north exit.","message_it":"Utilizzare Uscite 2, 6, 8. Bus di emergenza disponibili.","urgency":"emergency","channel":"speaker"}'
        ),
    },
    "orchestrator": {
        "model": "deepseek-ai/DeepSeek-V3.1",
        "lat": 45.4781, "lng": 9.1240, "alt": 200,
        "system": "You are the urban operations orchestrator. Output valid JSON only.",
        "prompt": (
            f"Scenario: {SCENARIO}\n\n"
            "Synthesize all agent actions into final coordinated plan. Return JSON: "
            '{"priority":"high","summary":"...","final_decisions":[{"agent":"...","action":"..."}],"estimated_resolution_minutes":18}'
        ),
    },
}

# Demo timeline: (t_seconds, agent_name_or_None, event_type, payload)
TIMELINE = [
    (0,   None, "log",    {"text": "[SYS] OlympusOS scenario initialised", "cls": "active"}),
    (2,   None, "log",    {"text": "[WARN] Metro M5 failure detected at San Siro Stadio station", "cls": "alert"}),
    (3,   None, "log",    {"text": "[WARN] Crowd anomaly at Gate 4 — density 0.83", "cls": "alert"}),
    (3,   None, "status", {"status": "ACTIVE"}),
    (5,   None, "metro",  {"state": "failed"}),
    (10,  "perception",    None, None),
    (17,  "forecast",      None, None),
    (22,  "mobility",      None, None),
    (24,  "transit",       None, None),
    (28,  None, "intervention", {}),
    (30,  "safety",        None, None),
    (38,  "communications", None, None),
    (38,  None, "speechmatics", {}),
    (48,  "orchestrator",  None, None),
    (60,  None, "crisis_contained", {}),
]


# ── WebSocket manager ────────────────────────────────────────────────────────
class WSManager:
    def __init__(self):
        self._conns: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._conns.append(ws)
        log.info("WS connected. Total: %d", len(self._conns))

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._conns = [c for c in self._conns if c is not ws]

    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        async with self._lock:
            dead = []
            for ws in self._conns:
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self._conns.remove(ws)


manager = WSManager()
demo_running = False


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws)


@app.post("/run_demo")
async def run_demo():
    global demo_running
    if demo_running:
        return {"status": "already_running"}
    demo_running = True
    asyncio.create_task(_demo_sequence())
    return {"status": "started"}


# ── LLM call (runs in thread pool) ──────────────────────────────────────────
async def _call_agent(name: str) -> dict:
    cfg = AGENTS[name]
    loop = asyncio.get_event_loop()

    def _sync():
        try:
            resp = llm.chat.completions.create(
                model=cfg["model"],
                messages=[
                    {"role": "system", "content": cfg["system"]},
                    {"role": "user",   "content": cfg["prompt"]},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                parts = raw.split("```")
                raw = parts[1].lstrip("json").strip()
            return json.loads(raw)
        except Exception as exc:
            log.error("Agent %s LLM error: %s", name, exc)
            return _fallback(name)

    return await loop.run_in_executor(None, _sync)


def _fallback(name: str) -> dict:
    defaults = {
        "perception":     {"observation": "High crowd density at Gate 4. Fans pushing to exit.", "severity": 0.83, "location": "Gate 4, San Siro", "type": "crowd_anomaly"},
        "forecast":       {"prediction": "Crowd crush imminent in 8 minutes.", "confidence": 0.87, "severity": 0.91, "recommended_action": "Open evacuation corridor immediately"},
        "mobility":       {"action": "signal_change", "target_street": "Via Giuseppe Verdi", "alternative_route": "Via Harar → Via Piccolomini", "estimated_improvement": "35%"},
        "transit":        {"action": "deploy_buses", "vehicles_needed": 50, "route": "San Siro → Lampugnano → Centrale", "capacity": 5000, "estimated_wait_minutes": 4},
        "safety":         {"risk_level": "critical", "action": "open_corridor", "corridor_route": "Via Leonardo da Vinci", "response_time_seconds": 90, "units_needed": 12},
        "communications": {"message_en": "Please use Gates 2, 6, 8. Emergency buses available at north exit.", "message_it": "Utilizzare Uscite 2, 6, 8. Bus di emergenza disponibili.", "urgency": "emergency"},
        "orchestrator":   {"priority": "high", "summary": "All 6 agents coordinated. Evacuation in progress. Crisis containment estimated in 18 minutes.", "estimated_resolution_minutes": 18},
    }
    return defaults.get(name, {})


# ── Speechmatics streaming ───────────────────────────────────────────────────
async def _run_speechmatics():
    if not AUDIO_FILE.exists():
        log.warning("Audio file missing: %s", AUDIO_FILE)
        await _simulate_transcript()
        return
    try:
        from speechmatics.models import ConnectionSettings, TranscriptionConfig, AudioSettings, ServerMessageType
        from speechmatics.client import WebsocketClient

        settings = ConnectionSettings(
            url="wss://eu2.rt.speechmatics.com/v2",
            auth_token=SPEECHMATICS_KEY,
        )
        ws_client = WebsocketClient(settings)

        async def _on_transcript(msg):
            for result in msg.get("results", []):
                for alt in result.get("alternatives", []):
                    word = alt.get("content", "").strip()
                    if word:
                        await manager.broadcast({"type": "transcript", "text": word + " "})

        ws_client.add_event_handler(ServerMessageType.AddTranscript, _on_transcript)
        conf  = TranscriptionConfig(language="en", enable_partials=True)
        audio = AudioSettings()

        loop = asyncio.get_event_loop()
        with open(AUDIO_FILE, "rb") as f:
            await loop.run_in_executor(None, lambda: asyncio.run(ws_client.run(f, conf, audio)))
    except Exception as exc:
        log.error("Speechmatics error: %s — using simulated transcript", exc)
        await _simulate_transcript()


async def _simulate_transcript():
    words = (
        "Officer... there is a crowd surge at Gate Four. "
        "We need immediate assistance. "
        "Evacuation corridor required. "
        "Approximately eighty thousand fans attempting to exit. "
        "Gate Four is at critical density. Please respond."
    ).split()
    for word in words:
        await manager.broadcast({"type": "transcript", "text": word + " "})
        await asyncio.sleep(0.25)


# ── Simulation frame streamer ────────────────────────────────────────────────
async def _stream_frames(frames: list, duration: float, start_time: float):
    n = len(frames)
    idx = 0
    while time.time() - start_time < duration and idx < n:
        await manager.broadcast({"type": "sim_state", **frames[idx]})
        idx += 1
        await asyncio.sleep(0.1)


def _load_frames() -> tuple[list, list]:
    def _load(name):
        p = SUMO_DIR / name
        if p.exists():
            return json.loads(p.read_text())
        log.warning("%s not found — using empty frames", p)
        return []
    return _load("baseline.json"), _load("intervention.json")


# ── Main demo sequence ───────────────────────────────────────────────────────
async def _demo_sequence():
    global demo_running
    try:
        baseline, intervention = _load_frames()
        start = time.time()

        # Pre-schedule all agent tasks
        agent_tasks = {}
        for entry in TIMELINE:
            t_fire, agent_name, evt_type, payload = entry
            if agent_name:
                agent_tasks[agent_name] = t_fire

        async def _fire_agent(name: str, t_fire: float):
            while time.time() - start < t_fire:
                await asyncio.sleep(0.05)
            await manager.broadcast({"type": "agent_thinking", "agent": name,
                                     "lat": AGENTS[name]["lat"], "lng": AGENTS[name]["lng"]})
            await manager.broadcast({"type": "log", "text": f"[AGENT] {name.upper()} → THINKING", "cls": "info"})
            result = await _call_agent(name)
            cfg = AGENTS[name]
            await manager.broadcast({
                "type":   "agent_event",
                "agent":  name,
                "lat":    cfg["lat"],
                "lng":    cfg["lng"],
                "alt":    cfg.get("alt", 10),
                "result": result,
                "model":  cfg["model"].split("/")[-1],
            })
            await manager.broadcast({"type": "log", "text": f"[AGENT] {name.upper()} → COMPLETE", "cls": "success"})

        # Launch all agent coroutines concurrently
        all_tasks = [asyncio.create_task(_fire_agent(n, t)) for n, t in agent_tasks.items()]

        # Main loop: handle timed events + stream sim frames
        handled = set()
        frame_idx_b = 0
        frame_idx_i = 0
        use_intervention = False

        while time.time() - start < 62:
            elapsed = time.time() - start

            # Timed non-agent events
            for i, entry in enumerate(TIMELINE):
                if i in handled:
                    continue
                t_fire, agent_name, evt_type, payload = entry
                if elapsed < t_fire or agent_name:
                    continue
                handled.add(i)

                if evt_type == "log":
                    await manager.broadcast({"type": "log", **payload})
                elif evt_type == "status":
                    await manager.broadcast({"type": "status", **payload})
                elif evt_type == "metro":
                    await manager.broadcast({"type": "metro_event", "state": "failed"})
                    await manager.broadcast({"type": "log", "text": "[SYS] Metro M5 line → OFFLINE", "cls": "alert"})
                elif evt_type == "intervention":
                    use_intervention = True
                    await manager.broadcast({"type": "log", "text": "[SYS] Intervention protocol ACTIVATED", "cls": "success"})
                elif evt_type == "speechmatics":
                    asyncio.create_task(_run_speechmatics())
                elif evt_type == "crisis_contained":
                    await manager.broadcast({"type": "crisis_contained"})
                    await manager.broadcast({"type": "status", "status": "RESOLVED"})
                    await manager.broadcast({"type": "log", "text": "[SYS] ██ CRISIS CONTAINED ██", "cls": "success"})

            # Stream a sim frame
            frames = intervention if use_intervention else baseline
            frame_list = frames
            if frame_list:
                fi = int(elapsed * 10) % len(frame_list)
                await manager.broadcast({"type": "sim_state", **frame_list[fi]})

            await asyncio.sleep(0.1)

        # Wait for all agent tasks
        await asyncio.gather(*all_tasks, return_exceptions=True)
    finally:
        demo_running = False
        log.info("Demo sequence complete.")
