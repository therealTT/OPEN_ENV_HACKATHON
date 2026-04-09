from pydantic import BaseModel
from typing import Any, Optional


class Observation(BaseModel):
    content: Any
    metadata: dict = {}


class Action(BaseModel):
    content: Any


class Reward(BaseModel):
    value: Any
    reason: str = ""


class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
