"""
OpenEnv-compliant FastAPI server.
Endpoints: POST /reset, POST /step, GET /state
"""
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from server.models import Action, Observation, Reward, StepResult
from portal import actions as portal_actions
from portal import pages as portal_pages
from portal.session import SessionState, TASK_CONFIG
from tasks import task_1, task_2, task_3

# ── In-memory session store ───────────────────────────────────────────────────
sessions: dict[str, SessionState] = {}

GRADERS = {
    "task_1": task_1.grade,
    "task_2": task_2.grade,
    "task_3": task_3.grade,
}


# ── App startup: ensure DB exists ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    if not os.path.exists("portal.db"):
        from seed_db import create_and_seed
        create_and_seed()
    yield


app = FastAPI(
    title="Regulatory Portal — OpenEnv Environment",
    description="Agent navigates a simulated FDA-style drug regulatory portal.",
    lifespan=lifespan,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_observation(session: SessionState) -> Observation:
    content = portal_pages.render(session)
    return Observation(
        content=content,
        metadata={"session_id": session.session_id, "task_id": session.task_id},
    )


def _run_grader(session: SessionState) -> Reward:
    grader = GRADERS.get(session.task_id)
    if grader is None:
        return Reward(value=0.0, reason="Unknown task.")
    value, reason = grader(session)
    value = max(0.0, min(1.0, float(value)))
    return Reward(value=value, reason=reason)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/reset")
def reset(body: dict = {}) -> Observation:
    """
    Start a new episode.
    Body (optional): {"task_id": "task_1" | "task_2" | "task_3"}
    Returns the initial Observation.
    """
    task_id = body.get("task_id", "task_1") if body else "task_1"
    if task_id not in TASK_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task_id '{task_id}'. Valid: {list(TASK_CONFIG)}",
        )

    session_id = str(uuid.uuid4())
    session = SessionState(session_id=session_id, task_id=task_id)
    sessions[session_id] = session

    return _make_observation(session)


@app.post("/step")
def step(action: Action) -> StepResult:
    """
    Take one action in the current episode.
    Action body: {"content": {"type": "...", ...}}
    The most recently created session is used (single-session mode for simplicity).
    For multi-session, pass session_id in action metadata.
    """
    if not sessions:
        raise HTTPException(status_code=400, detail="No active session. Call /reset first.")

    # Use most recently created session
    session_id = list(sessions.keys())[-1]
    session = sessions[session_id]

    if session.done:
        obs = _make_observation(session)
        return StepResult(
            observation=obs,
            reward=Reward(value=0.0, reason="Episode already done. Call /reset to start a new one."),
            done=True,
        )

    # Parse action
    raw_action = action.content
    if not isinstance(raw_action, dict):
        raise HTTPException(status_code=400, detail="Action content must be a JSON object.")

    # Execute action
    session, error = portal_actions.handle(session, raw_action)
    session.step_count += 1

    # Check termination
    done = session.done

    # Max steps exceeded
    if not done and session.step_count >= session.max_steps:
        session.done = True
        done = True

    # Compute reward only on termination
    if done:
        reward = _run_grader(session)
    else:
        reward = Reward(value=0.0, reason="Episode in progress.")

    obs = _make_observation(session)
    return StepResult(observation=obs, reward=reward, done=done)


@app.get("/state")
def state() -> dict:
    """Return current environment state (for debugging / spec compliance)."""
    if not sessions:
        return {"status": "no_active_session"}

    session_id = list(sessions.keys())[-1]
    session = sessions[session_id]
    return {
        "session_id":     session.session_id,
        "task_id":        session.task_id,
        "current_page":   session.current_page,
        "step_count":     session.step_count,
        "max_steps":      session.max_steps,
        "done":           session.done,
        "available_tasks": list(TASK_CONFIG.keys()),
    }


@app.get("/")
def root():
    return {"status": "ok", "message": "Regulatory Portal OpenEnv is running."}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
