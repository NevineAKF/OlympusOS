import logging
import threading

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="OlympusOS")

# Agent instance + thread pairs, keyed by agent name
_agents: dict[str, object] = {}
_threads: dict[str, threading.Thread] = {}


def _is_alive(name: str) -> bool:
    t = _threads.get(name)
    return t is not None and t.is_alive()


def _start(name: str, factory) -> dict:
    if _is_alive(name):
        raise HTTPException(status_code=409, detail=f"{name} is already running")
    agent = factory()
    _agents[name] = agent
    t = threading.Thread(target=agent.run, daemon=True, name=name)
    _threads[name] = t
    t.start()
    logger.info("%s started via API", name)
    return {"status": "started", "agent": name}


def _stop(name: str) -> dict:
    if not _is_alive(name):
        raise HTTPException(status_code=409, detail=f"{name} is not running")
    _agents[name].stop()
    return {"status": "stopping", "agent": name}


# ------------------------------------------------------------------
# Health
# ------------------------------------------------------------------

@app.get("/")
def root() -> dict:
    return {"status": "OlympusOS running"}


@app.get("/agents/status")
def agents_status() -> dict:
    return {name: _is_alive(name) for name in
            ["orchestrator", "perception", "forecast", "mobility", "transit", "safety", "communications"]}


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------

@app.post("/orchestrator/start")
def start_orchestrator() -> dict:
    from agents.orchestrator import OrchestratorAgent
    return _start("orchestrator", OrchestratorAgent)


@app.post("/orchestrator/stop")
def stop_orchestrator() -> dict:
    return _stop("orchestrator")


# ------------------------------------------------------------------
# Perception
# ------------------------------------------------------------------

@app.post("/perception/start")
def start_perception() -> dict:
    from agents.perception import PerceptionAgent
    return _start("perception", PerceptionAgent)


@app.post("/perception/stop")
def stop_perception() -> dict:
    return _stop("perception")


# ------------------------------------------------------------------
# Forecast
# ------------------------------------------------------------------

@app.post("/forecast/start")
def start_forecast() -> dict:
    from agents.forecast import ForecastAgent
    return _start("forecast", ForecastAgent)


@app.post("/forecast/stop")
def stop_forecast() -> dict:
    return _stop("forecast")


# ------------------------------------------------------------------
# Mobility
# ------------------------------------------------------------------

@app.post("/mobility/start")
def start_mobility() -> dict:
    from agents.mobility import MobilityAgent
    return _start("mobility", MobilityAgent)


@app.post("/mobility/stop")
def stop_mobility() -> dict:
    return _stop("mobility")


# ------------------------------------------------------------------
# Transit
# ------------------------------------------------------------------

@app.post("/transit/start")
def start_transit() -> dict:
    from agents.transit import TransitAgent
    return _start("transit", TransitAgent)


@app.post("/transit/stop")
def stop_transit() -> dict:
    return _stop("transit")


# ------------------------------------------------------------------
# Safety
# ------------------------------------------------------------------

@app.post("/safety/start")
def start_safety() -> dict:
    from agents.safety import SafetyAgent
    return _start("safety", SafetyAgent)


@app.post("/safety/stop")
def stop_safety() -> dict:
    return _stop("safety")


# ------------------------------------------------------------------
# Communications
# ------------------------------------------------------------------

@app.post("/communications/start")
def start_communications() -> dict:
    from agents.communications import CommunicationsAgent
    return _start("communications", CommunicationsAgent)


@app.post("/communications/stop")
def stop_communications() -> dict:
    return _stop("communications")
