"""
Baseline inference script.
Runs tasks against the deployed environment using an LLM agent.

Required env vars:
  API_BASE_URL   — OpenAI-compatible base URL
  MODEL_NAME     — model identifier
  HF_TOKEN       — Hugging Face / API key

Optional:
  TASK_ID        — run a single task (task_1 | task_2 | task_3); runs all 3 if unset
"""
import os
import json
import sys
import requests
from typing import List, Optional
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "moonshotai/kimi-k2-instruct")
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "none")
HF_SPACE_URL = "https://t-t123-regulatory-portal-nav.hf.space"
BENCHMARK    = "regulatory-portal-nav"
SUCCESS_THRESHOLD = 0.5

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

SYSTEM_PROMPT = """You are an agent navigating a simulated drug regulatory portal.
On each turn you receive the current page state as JSON and must output a single action as JSON.

Available action types:
  {"type": "navigate",  "page": "<page_id>"}
  {"type": "fill",      "element_id": "<id>", "value": "<text>"}
  {"type": "select",    "element_id": "<id>", "value": "<option>"}
  {"type": "click",     "element_id": "<id>"}
  {"type": "submit",    "form_id": "<form_id>"}
  {"type": "answer",    "fields": {"<field>": "<value>", ...}}

Valid top-level pages for navigate: home, drug_search, doc_archive, forms_hub
Detail pages are reached by clicking search results.

Output ONLY a valid JSON object — no markdown, no explanation."""


# ── Structured log helpers ────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


# ── LLM helpers ───────────────────────────────────────────────────────────────

def call_llm(messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def parse_action(raw: str) -> dict:
    try:
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception:
        return {"type": "navigate", "page": "home"}


# ── Episode runner ────────────────────────────────────────────────────────────

def run_episode(task_id: str) -> float:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        resp = requests.post(f"{HF_SPACE_URL}/reset", json={"task_id": task_id}, timeout=30)
        resp.raise_for_status()
        obs = resp.json()
        done = False

        while not done:
            page_content = obs.get("content", obs)
            task_desc    = page_content.get("task", "")
            step_num     = page_content.get("step", 0) + 1

            user_msg = (
                f"TASK: {task_desc}\n\n"
                f"CURRENT STATE:\n{json.dumps(page_content, indent=2)}\n\n"
                "What is your next action? Output JSON only."
            )
            messages.append({"role": "user", "content": user_msg})

            raw_action = call_llm(messages)
            messages.append({"role": "assistant", "content": raw_action})

            action     = parse_action(raw_action)
            action_str = json.dumps(action, separators=(",", ":"))

            step_resp = requests.post(f"{HF_SPACE_URL}/step", json={"content": action}, timeout=30)
            step_resp.raise_for_status()
            result = step_resp.json()

            obs    = result["observation"]
            done   = result["done"]
            reward = result["reward"]["value"]

            rewards.append(reward)
            steps_taken = step_num
            score = reward

            log_step(step=step_num, action=action_str, reward=reward, done=done, error=None)

        success = score >= SUCCESS_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", file=sys.stderr, flush=True)
        if not rewards:
            rewards = [0.0]

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    task_id_env = os.getenv("TASK_ID")
    task_ids = [task_id_env] if task_id_env else ["task_1", "task_2", "task_3"]
    for task_id in task_ids:
        run_episode(task_id)


if __name__ == "__main__":
    main()
