"""
Baseline inference script.
Runs all 3 tasks against the deployed environment using an LLM agent.

Required env vars:
  API_BASE_URL   — OpenAI-compatible base URL
  MODEL_NAME     — model identifier
  HF_SPACE_URL   — deployed HF Space URL (e.g. https://your-space.hf.space)

Optional:
  OPENAI_API_KEY — API key (default: "none" for local/open models)
"""
import os
import json
import requests
from openai import OpenAI

API_BASE_URL = os.environ["API_BASE_URL"]
MODEL_NAME   = os.environ["MODEL_NAME"]
HF_SPACE_URL = os.environ.get("HF_SPACE_URL", "http://localhost:7860").rstrip("/")
API_KEY      = os.environ.get("OPENAI_API_KEY", "none")

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


def call_llm(messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def parse_action(raw: str) -> dict | None:
    try:
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return json.loads(text)
    except Exception:
        return None


def run_episode(task_id: str) -> float:
    print(f"\n{'='*50}")
    print(f"Starting {task_id}")
    print('='*50)

    # Reset
    resp = requests.post(f"{HF_SPACE_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    obs = resp.json()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    done  = False
    score = 0.0

    while not done:
        page_content = obs.get("content", obs)
        task_desc    = page_content.get("task", "")
        step         = page_content.get("step", 0)
        remaining    = page_content.get("steps_remaining", "?")

        print(f"\n[Step {step} | {remaining} remaining] Page: {page_content.get('current_page')}")

        user_msg = (
            f"TASK: {task_desc}\n\n"
            f"CURRENT STATE:\n{json.dumps(page_content, indent=2)}\n\n"
            "What is your next action? Output JSON only."
        )
        messages.append({"role": "user", "content": user_msg})

        raw_action = call_llm(messages)
        messages.append({"role": "assistant", "content": raw_action})

        action = parse_action(raw_action)
        if action is None:
            print(f"  [WARN] Could not parse action: {raw_action[:100]}")
            action = {"type": "navigate", "page": "home"}

        print(f"  Action: {json.dumps(action)}")

        # Step
        step_resp = requests.post(
            f"{HF_SPACE_URL}/step",
            json={"content": action},
            timeout=30,
        )
        step_resp.raise_for_status()
        result = step_resp.json()

        obs   = result["observation"]
        done  = result["done"]
        score = result["reward"]["value"]

        if result["reward"]["reason"]:
            print(f"  Reward so far: {score} — {result['reward']['reason']}")

    print(f"\n[{task_id}] Final score: {score:.2f}")
    return score


def main():
    task_ids = ["task_1", "task_2", "task_3"]
    results  = {}

    for task_id in task_ids:
        try:
            score = run_episode(task_id)
            results[task_id] = score
        except Exception as e:
            print(f"[ERROR] {task_id} failed: {e}")
            results[task_id] = 0.0

    print("\n" + "="*50)
    print("FINAL SCORES")
    print("="*50)
    for task_id, score in results.items():
        print(f"  {task_id}: {score:.2f}")
    avg = sum(results.values()) / len(results)
    print(f"  Average: {avg:.2f}")


if __name__ == "__main__":
    main()
