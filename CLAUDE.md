# OpenEnv Hackathon — Project Context

## Event
**Scaler/OpenEnv Hackathon — Round 1**
**Deadline:** April 8, 2026 11:59 PM IST

---

## Current Status (as of March 30, 2026)

**All core code is written and smoke-tested locally. ✅**

### What's done
- `seed_db.py` — creates `portal.db` with drugs + documents
- `models.py` — OpenEnv Pydantic types (Observation, Action, Reward)
- `portal/database.py` — SQLite queries
- `portal/session.py` — session state + task config
- `portal/pages.py` — observation renderer per page
- `portal/actions.py` — all action handlers (navigate, fill, select, click, submit, answer)
- `tasks/task_1.py` — drug lookup grader (scores 1.0 on happy path ✅)
- `tasks/task_2.py` — document retrieval grader (scores 1.0 on happy path ✅)
- `tasks/task_3.py` — form submission grader (scores 1.0 on happy path ✅)
- `server.py` — FastAPI `/reset` `/step` `/state` endpoints (tested locally ✅)
- `inference.py` — baseline agent script
- `requirements.txt`, `Dockerfile`, `openenv.yaml`

### What still needs to be done (in order)

1. **Stress test failure paths locally**
   - Agent hits max steps → reward should be 0.0
   - Agent submits form with missing fields → error page, not crash
   - Agent answers with wrong values → partial scores
   - Agent hallucinates answer without visiting correct page → 0.25 penalty

2. **Write README.md** — required for submission, document tasks + setup + how to run

3. **Deploy to Hugging Face Spaces**
   - Create new Space (Docker SDK, public)
   - Push all files to the Space repo
   - Verify `/reset` returns HTTP 200

4. **Update `openenv.yaml`**
   - Replace `endpoint: https://YOUR-HF-SPACE.hf.space` with the real URL

5. **Install openenv CLI and run `openenv validate`**
   - `pip install openenv`
   - `openenv validate`
   - Fix any spec compliance issues

6. **Test `inference.py` end-to-end**
   - Set env vars: `API_BASE_URL`, `MODEL_NAME`, `HF_SPACE_URL`, `OPENAI_API_KEY`
   - Run against live Space
   - Confirm scores print for all 3 tasks

7. **Final submission checklist** (see Pre-Submission Checklist section below)

---

## Organizer Clarifications (confirmed March 30, 2026)

- **No training required** — Round 1 is about building a working, reproducible *evaluation/interaction* environment, not a learning setup
- **Open-ended problem** — no additional problem statements coming; choose your own domain and build within the guidelines
- **No waiting needed** — proceed immediately, everything needed is already on the dashboard
- Supporting RL/learning is optional and bonus — not mandatory

---

## What We're Building

A **simulated regulatory web portal** (FDA-style) where an agent must navigate pages, extract information, and submit forms to complete tasks. The environment is an OpenEnv-compliant multi-step interaction loop deployed on Hugging Face Spaces.

Each episode is a concrete task (drug lookup, document retrieval, form submission). The agent takes structured actions (fill, click, navigate, submit) and receives page observations after each step. A deterministic grader checks the final state.

```
Agent (inference.py)
    ↓  POST /reset
HF Space (FastAPI server)
    ↓  returns Observation
Agent reasons → picks Action
    ↓  POST /step  {action}
HF Space
    ↓  returns Observation + Reward + done flag
Agent loops until done
```

---

## Functional Requirements

1. **OpenEnv spec compliance** — implement `/reset`, `/step`, `/state` HTTP endpoints
2. **3 tasks minimum** with distinct graders (each returns a float reward 0.0–1.0)
3. **Real-world task simulation** — tasks should mimic something meaningful (e.g. form filling, search, data extraction, navigation)
4. **Reward function** — deterministic, returns `float` in `[0.0, 1.0]`
5. **Baseline inference script** (`inference.py`) — uses OpenAI client pointed at any model, runs through at least one task end-to-end

---

## Non-Functional Requirements

- **HF Spaces deployment** — server must respond with HTTP 200 at `/reset`
- **Dockerfile** — must build and run the environment reproducibly
- **README** — documents tasks, setup, and how to run

---

## Technical Constraints

| Constraint | Value |
|-----------|-------|
| Runtime limit | < 20 minutes per episode |
| CPU | 2 vCPU |
| RAM | 8 GB |
| LLM client | OpenAI-compatible (`openai` Python package) |
| API base URL | `API_BASE_URL` env var |
| Model name | `MODEL_NAME` env var |
| HF token | `HF_TOKEN` env var |

---

## OpenEnv Spec Details

### Pydantic Models

```python
from pydantic import BaseModel
from typing import Any, Optional

class Observation(BaseModel):
    content: Any          # what the agent sees
    metadata: dict = {}

class Action(BaseModel):
    content: Any          # what the agent does

class Reward(BaseModel):
    value: float          # 0.0 to 1.0
    reason: str = ""
```

### HTTP Endpoints

| Endpoint | Method | Body | Returns |
|---------|--------|------|---------|
| `/reset` | POST | `{"task_id": "..."}` (optional) | `Observation` |
| `/step` | POST | `Action` | `{"observation": Observation, "reward": Reward, "done": bool}` |
| `/state` | GET | — | current environment state dict |

### openenv.yaml

```yaml
name: your-env-name
version: "1.0"
tasks:
  - id: task_1
    description: "Description of task 1"
  - id: task_2
    description: "Description of task 2"
  - id: task_3
    description: "Description of task 3"
endpoint: https://your-hf-space.hf.space
```

### Validation

```bash
openenv validate  # checks spec compliance
```

---

## Project File Structure

```
open_env_hackthon/
├── server.py           # FastAPI app — /reset, /step, /state endpoints
├── portal/
│   ├── __init__.py
│   ├── database.py     # SQLite portal DB — drugs, documents, form_submissions
│   ├── pages.py        # Page renderer — returns structured observation per page
│   ├── actions.py      # Action handler — transitions state based on action type
│   └── session.py      # Session state — current page, filled fields, task
├── tasks/
│   ├── __init__.py
│   ├── task_1.py       # Drug lookup grader
│   ├── task_2.py       # Document retrieval grader
│   └── task_3.py       # Form submission grader
├── models.py           # Pydantic models (Observation, Action, Reward, SessionState)
├── inference.py        # Baseline agent script
├── portal.db           # Pre-seeded SQLite database (committed to repo)
├── seed_db.py          # Script to recreate portal.db from scratch
├── Dockerfile
├── openenv.yaml
├── requirements.txt
├── CLAUDE.md
└── README.md
```

---

## Inference Script Pattern

```python
import os
from openai import OpenAI
import requests

API_BASE_URL = os.environ["API_BASE_URL"]   # e.g. https://api.openai.com/v1
MODEL_NAME = os.environ["MODEL_NAME"]       # e.g. gpt-4o-mini
HF_SPACE_URL = os.environ["HF_SPACE_URL"]  # your deployed space URL

client = OpenAI(base_url=API_BASE_URL, api_key=os.environ.get("OPENAI_API_KEY", "none"))

def run_episode(task_id: str):
    # Reset environment
    obs = requests.post(f"{HF_SPACE_URL}/reset", json={"task_id": task_id}).json()

    messages = [{"role": "system", "content": "You are an AI agent. Complete the task."}]
    done = False

    while not done:
        messages.append({"role": "user", "content": str(obs["content"])})

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        action_text = response.choices[0].message.content
        messages.append({"role": "assistant", "content": action_text})

        result = requests.post(f"{HF_SPACE_URL}/step", json={"content": action_text}).json()
        obs = result["observation"]
        reward = result["reward"]["value"]
        done = result["done"]
        print(f"Reward: {reward}, Done: {done}")

    return reward

if __name__ == "__main__":
    for task_id in ["task_1", "task_2", "task_3"]:
        score = run_episode(task_id)
        print(f"{task_id}: {score:.2f}")
```

---

## Dockerfile Pattern

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
```

**Note:** HF Spaces uses port 7860 by default.

---

## Judging — Two Phases

### Phase 1: Automated Validation (Pass/Fail Gate)
Must pass ALL of these or you're **disqualified**:

| Check | What's tested |
|-------|--------------|
| HF Space deploy | Automated ping — must return 200 and respond to `reset()` |
| OpenEnv spec compliance | Validates `openenv.yaml`, typed models, `reset()`/`step()`/`state()` endpoints |
| Dockerfile builds | `docker build` on submitted repo must succeed |
| Baseline reproduces | `inference.py` must complete without errors and produce scores |
| 3+ tasks with graders | Each grader runs, verifies score is in 0.0–1.0 range |

### Phase 2: Agentic Evaluation (Scored)
Baseline agent re-run with standard Open LLM, score variance check.

---

## Scoring Criteria (100 points total)

| Criterion | Weight | What judges look for |
|----------|--------|---------------------|
| **Real-world utility** | 30% | Does it model a genuine task? Would someone actually use this to train/evaluate agents? |
| **Task & grader quality** | 25% | Well-defined objectives, accurate graders, meaningful difficulty progression |
| **Environment design** | 20% | Clean state management, sensible action/observation spaces, good reward shaping, proper episode boundaries |
| **Code quality & spec compliance** | 15% | Follows OpenEnv spec, clean structure, typed models, documented, tested, Dockerfile works |
| **Creativity & novelty** | 10% | Novel problem domain, interesting mechanics, clever reward design, original approach |

### Detailed Scoring Rubrics

**Real-world utility (30%)**
- 0–5: Toy/artificial problem with no practical application
- 6–15: Valid domain but shallow modeling of the real task
- 16–25: Good domain modeling, would be useful for agent evaluation
- 26–30: Excellent — fills a real gap, immediate value for the RL/agent community

**Task & grader quality (25%)**
- 3+ tasks with difficulty range?
- Graders produce scores between 0.0–1.0?
- Graders deterministic and reproducible?
- Hard task genuinely challenges frontier models?

**Environment design (20%)**
- `reset()` produces clean state?
- Action/observation types well-designed and documented?
- Reward function provides **useful varying signal** (not just sparse/binary)?
- Episode boundaries sensible?

**Code quality & spec compliance (15%)**
- `openenv validate` passes?
- `docker build && docker run` works?
- HF Space deploys and responds?
- Baseline script runs and reproduces scores?

**Creativity & novelty (10%)**
- Domain we haven't seen in OpenEnv before?
- Reward design has interesting properties?
- Clever mechanics that make the environment engaging?

---

## Pre-Submission Checklist (all must pass or you're disqualified)

- [ ] HF Space returns HTTP 200 on `POST /reset` and responds to `reset()`
- [ ] `openenv validate` passes (typed models, all endpoints present)
- [ ] `docker build` succeeds on the submitted repo
- [ ] `inference.py` runs end-to-end without errors and produces scores
- [ ] 3+ tasks, each grader returns float in `[0.0, 1.0]`
- [ ] `openenv.yaml` present with correct endpoint URL
- [ ] `CLAUDE.md` present at project root (required by judges)
- [ ] `README.md` documents tasks and setup
- [ ] Episode completes within 20 minutes on 2 vCPU / 8 GB
- [ ] Env vars `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` are used (not hardcoded)
- [ ] Run the pre-submission validation script before submitting

---

## Validation Script (3-step check)

```bash
# 1. Ping HF Space
curl -X POST https://your-space.hf.space/reset -H "Content-Type: application/json" -d '{}'

# 2. Build Docker image
docker build -t openenv-test . && docker run -p 7860:7860 openenv-test

# 3. Validate spec
openenv validate
```

---

## Problem Statement

**Domain:** Simulated Regulatory Web Portal Navigation

An agent interacts with a fake FDA-style drug regulatory portal. It must navigate pages, extract information, fill forms, and submit correctly — all within a multi-step episode. The environment serves structured page observations; the agent sends actions (fill, click, navigate, submit). The grader checks whether the agent reached the correct final state with accurate information.

**Why this scores well on real-world utility:**
- Web/portal navigation is one of the most active agent research problems
- Regulatory document workflows are a genuine enterprise pain point
- Information-gathering + form-filling tests multi-step planning and memory
- Deterministic grading — we control all portal data, so GT is exact
- Generalises beyond pharma: any enterprise portal with multi-page workflows

---

## Portal Structure

The server maintains a session per episode. Each `/step` transitions the session to a new page based on the action taken.

### Pages

| Page ID | Title | Description |
|---------|-------|-------------|
| `home` | Regulatory Portal Home | Navigation hub — links to all sections |
| `drug_search` | Drug Approval Search | Search by drug name or application number |
| `drug_detail` | Drug Detail | Approval date, manufacturer, indication, app number |
| `doc_archive` | Document Archive | Filter documents by drug + type |
| `doc_detail` | Document Viewer | Structured document content (dose, warnings, etc.) |
| `forms_hub` | Submit a Form | List of available form types |
| `form_labeling` | Labeling Inquiry Form | Multi-field form requiring drug info |
| `form_safety` | Safety Report Form | Multi-field form for adverse event reporting |
| `confirmation` | Submission Confirmed | Reference number + submitted fields |
| `error` | Error | Shown on invalid action or missing required field |

### Action Space

```json
{"type": "navigate",  "page": "<page_id>"}
{"type": "fill",      "element_id": "<field_id>", "value": "<text>"}
{"type": "click",     "element_id": "<element_id>"}
{"type": "select",    "element_id": "<dropdown_id>", "value": "<option>"}
{"type": "submit",    "form_id": "<form_id>"}
```

### Observation Schema

```json
{
  "current_page": "drug_search",
  "title": "Drug Approval Search",
  "content": "Search for approved drugs by name or application number.",
  "elements": [
    {"id": "drug_name",   "type": "input",  "label": "Drug Name"},
    {"id": "app_number",  "type": "input",  "label": "Application Number"},
    {"id": "search_btn",  "type": "button", "label": "Search"},
    {"id": "nav_home",    "type": "link",   "label": "Home"},
    {"id": "nav_docs",    "type": "link",   "label": "Document Archive"},
    {"id": "nav_forms",   "type": "link",   "label": "Submit a Form"}
  ],
  "result": null,
  "error": null,
  "task": "Find the approval date and approved indication for NEXOLARA"
}
```

---

## Portal Database (Synthetic — we define, so GT is exact)

### `drugs`

| drug_name | app_number | approval_date | manufacturer | indication | status |
|-----------|------------|--------------|--------------|------------|--------|
| NEXOLARA | NDA-042817 | 2022-03-15 | Helivar Therapeutics | Myelofibrosis | Approved |
| ZETHROVAN | NDA-039204 | 2020-11-08 | Coraxis Pharma | Myelofibrosis | Approved |
| PRIMAVEX | NDA-051673 | 2023-06-22 | Dunmore BioSciences | Myelofibrosis | Approved |
| VALDIPRINE | NDA-028941 | 2018-04-30 | Solvanta Inc | Thrombocytopenia | Approved |

### `documents`

| doc_id | drug_name | doc_type | content |
|--------|-----------|----------|---------|
| DOC-001 | NEXOLARA | Prescribing Information | `{"starting_dose": "100mg once daily", "max_dose": "200mg once daily", "renal_adjustment": "50mg once daily if eGFR < 30"}` |
| DOC-002 | NEXOLARA | Patient Medication Guide | `{"storage": "Room temperature", "missed_dose": "Take as soon as remembered"}` |
| DOC-003 | ZETHROVAN | Prescribing Information | `{"starting_dose": "150mg twice daily", ...}` |
| DOC-004 | PRIMAVEX | Prescribing Information | `{"starting_dose": "200mg once daily", ...}` |

### `form_submissions` (written to on submit)

| submission_id | form_type | drug_name | app_number | submitted_at | fields_json |

---

## The 3 Tasks

### Task 1 — Easy: Drug Lookup (~3 steps)

**Task given to agent:**
> "Find the approval date and approved indication for **NEXOLARA**."

**Expected navigation path:**
```
home → drug_search → fill drug_name="NEXOLARA" → click search_btn
     → drug_detail page → extract approval_date + indication → done
```

**Grader checks:**
- `approval_date == "2022-03-15"` extracted correctly
- `indication == "Myelofibrosis"` extracted correctly

**Scoring:**
- 1.0 — both fields correct
- 0.5 — one field correct
- 0.0 — neither correct, or agent never reached drug_detail page

**Common failure modes:**
- Agent navigates to doc_archive instead of drug_search
- Agent searches by app_number field instead of drug_name
- Agent stops after search results without clicking into drug_detail
- Agent confuses NEXOLARA with ZETHROVAN data

---

### Task 2 — Medium: Document Retrieval + Field Extraction (~5 steps)

**Task given to agent:**
> "Find the **recommended starting dose** for NEXOLARA from its Prescribing Information document."

**Expected navigation path:**
```
home → doc_archive → select drug="NEXOLARA" → select doc_type="Prescribing Information"
     → click search → doc_detail (DOC-001) → extract starting_dose → done
```

**Grader checks:**
- Agent reached `doc_detail` for `DOC-001` (correct document)
- `starting_dose == "100mg once daily"` extracted correctly

**Scoring:**
- 1.0 — correct document + correct dose extracted
- 0.5 — correct document found but wrong field extracted (e.g., max_dose)
- 0.25 — wrong document type (e.g., Patient Medication Guide) but dose attempt made
- 0.0 — never reached doc_detail or extracted from wrong drug

**Common failure modes:**
- Agent opens Patient Medication Guide instead of Prescribing Information
- Agent goes to drug_detail (drug page) instead of doc_archive
- Agent extracts `max_dose` instead of `starting_dose`
- Agent uses ZETHROVAN's document instead of NEXOLARA's

---

### Task 3 — Hard: Multi-page Info Gathering + Form Submission (~7-8 steps)

**Task given to agent:**
> "Submit a **Labeling Inquiry** for NEXOLARA. The form requires: application number, approval date, and manufacturer name. You must look these up before submitting."

**Expected navigation path:**
```
Step 1: home → drug_search → search "NEXOLARA" → drug_detail
        → note: app_number="NDA-042817", approval_date="2022-03-15",
                manufacturer="Helivar Therapeutics"
Step 2: home → forms_hub → click "Labeling Inquiry"
Step 3: form_labeling → fill app_number, approval_date, manufacturer
        → submit form
Step 4: confirmation page → episode done
```

**Grader checks:**
- Form submitted (confirmation page reached)
- `app_number == "NDA-042817"`
- `approval_date == "2022-03-15"`
- `manufacturer == "Helivar Therapeutics"`

**Scoring:**
- 1.0 — form submitted, all 3 fields correct
- 0.75 — form submitted, 2 of 3 fields correct
- 0.5 — form submitted, 1 of 3 fields correct (or submitted with wrong drug's data)
- 0.25 — reached form page but did not submit
- 0.0 — never reached forms section

**Common failure modes:**
- Agent guesses field values from memory instead of navigating to drug_detail first
- Agent submits Safety Report form instead of Labeling Inquiry
- Agent uses ZETHROVAN's app number (wrong drug)
- Agent fills form before looking up values (hallucinated data)
- Agent navigates to drug_detail but forgets manufacturer, only submits 2 fields

---

## What Makes This Hard for LLMs

| Challenge | Why LLMs struggle |
|-----------|------------------|
| Multi-step planning | Must plan full path before starting, not react greedily |
| Cross-page memory | Must remember values from page 3 when filling form on page 6 |
| Correct form selection | Portal has multiple form types — must pick the right one |
| No hallucination allowed | Grader checks exact values — guessing from training data fails |
| Distractors | doc_archive, safety form, wrong drug pages all look plausible |
| Recovery from errors | Wrong action → error page → must backtrack correctly |

---

## Common Mistakes to Avoid

1. **Reward outside [0.0, 1.0]** — graders must clamp or return within range
2. **Non-deterministic graders** — same action must always yield same reward
3. **Sparse/binary rewards** — judges want *varying* signal, not just 0 or 1
4. **HF port mismatch** — use port 7860, not 5000 or 8000
5. **Missing `done=True`** — episodes must terminate, agent can't loop forever
6. **openenv.yaml endpoint wrong** — must match the actual deployed HF Space URL
7. **inference.py crashes** — must run cleanly with only env vars set, no hardcoded keys
8. **Tasks too easy** — at least one task should genuinely challenge frontier models
9. **Missing CLAUDE.md** — judges require it at project root
10. **Toy domain** — real-world utility is 30% of the score; avoid contrived problems
