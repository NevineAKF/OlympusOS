import logging
import threading

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(title="OlympusOS")

# Module-level references so /orchestrator/stop can be added later
_orchestrator_agent = None
_orchestrator_thread: threading.Thread | None = None


@app.get("/")
def root() -> dict:
    return {"status": "OlympusOS running"}


@app.post("/orchestrator/start")
def start_orchestrator() -> dict:
    """Launch the OrchestratorAgent in a background thread."""
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
    """Signal the OrchestratorAgent to stop after its current iteration."""
    global _orchestrator_agent, _orchestrator_thread

    if not _orchestrator_thread or not _orchestrator_thread.is_alive():
        raise HTTPException(status_code=409, detail="Orchestrator is not running")

    _orchestrator_agent.stop()
    return {"status": "stopping"}
