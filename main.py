import logging
import threading

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="OlympusOS")

_orchestrator_agent = None
_orchestrator_thread: threading.Thread | None = None

_perception_agent = None
_perception_thread: threading.Thread | None = None


@app.get("/")
def root() -> dict:
    return {"status": "OlympusOS running"}


# ------------------------------------------------------------------
# Orchestrator
# ------------------------------------------------------------------

@app.post("/orchestrator/start")
def start_orchestrator() -> dict:
    global _orchestrator_agent, _orchestrator_thread

    if _orchestrator_thread and _orchestrator_thread.is_alive():
        raise HTTPException(status_code=409, detail="Orchestrator is already running")

    from agents.orchestrator import OrchestratorAgent

    _orchestrator_agent = OrchestratorAgent()
    _orchestrator_thread = threading.Thread(
        target=_orchestrator_agent.run,
        daemon=True,
        name="orchestrator",
    )
    _orchestrator_thread.start()
    logger.info("Orchestrator started via API")
    return {"status": "started"}


@app.post("/orchestrator/stop")
def stop_orchestrator() -> dict:
    global _orchestrator_agent, _orchestrator_thread

    if not _orchestrator_thread or not _orchestrator_thread.is_alive():
        raise HTTPException(status_code=409, detail="Orchestrator is not running")

    _orchestrator_agent.stop()
    return {"status": "stopping"}


# ------------------------------------------------------------------
# Perception
# ------------------------------------------------------------------

@app.post("/perception/start")
def start_perception() -> dict:
    global _perception_agent, _perception_thread

    if _perception_thread and _perception_thread.is_alive():
        raise HTTPException(status_code=409, detail="Perception agent is already running")

    from agents.perception import PerceptionAgent

    _perception_agent = PerceptionAgent()
    _perception_thread = threading.Thread(
        target=_perception_agent.run,
        daemon=True,
        name="perception",
    )
    _perception_thread.start()
    logger.info("Perception agent started via API")
    return {"status": "started"}


@app.post("/perception/stop")
def stop_perception() -> dict:
    global _perception_agent, _perception_thread

    if not _perception_thread or not _perception_thread.is_alive():
        raise HTTPException(status_code=409, detail="Perception agent is not running")

    _perception_agent.stop()
    return {"status": "stopping"}
