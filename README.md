# Regulatory Portal — OpenEnv Environment

A simulated FDA-style drug regulatory web portal where an agent must navigate pages, extract information, and submit forms to complete tasks. Built for the Scaler/OpenEnv Hackathon Round 1.

## What It Is

Agents interact with a multi-page portal to look up drugs, retrieve prescribing documents, and submit regulatory forms. The environment follows the [OpenEnv spec](https://openenv.dev) — standard `/reset`, `/step`, `/state` endpoints, typed Pydantic models, and deterministic graders.

```
Agent
  ↓ POST /reset
FastAPI server
  ↓ returns Observation (current page, elements, task)
Agent reasons → picks Action
  ↓ POST /step {"content": action}
Server updates session state
  ↓ returns Observation + Reward + done
Agent loops until done=True
```

## Tasks

| Task | Description | Difficulty | Max Steps |
|------|-------------|------------|-----------|
| `task_1` | Find approval date and indication for NEXOLARA | Easy (~3 steps) | 10 |
| `task_2` | Find starting dose from NEXOLARA's Prescribing Information | Medium (~5 steps) | 15 |
| `task_3` | Look up NEXOLARA details, then submit a Labeling Inquiry form | Hard (~8 steps) | 20 |

### Task 1 — Drug Lookup
**Goal:** Find `approval_date` and `indication` for NEXOLARA.

Navigate to Drug Search → search for NEXOLARA → open drug detail page → submit answer.

Scoring: 1.0 (both fields + visited drug detail) | 0.5 (one field) | 0.25 (correct but hallucinated) | 0.0

### Task 2 — Document Retrieval
**Goal:** Find the recommended `starting_dose` from NEXOLARA's Prescribing Information document.

Navigate to Document Archive → filter by drug + doc type → open document → submit answer.

Scoring: 1.0 (correct dose + correct doc) | 0.5 (correct doc, wrong field) | 0.25 (correct value, wrong doc) | 0.0

### Task 3 — Form Submission
**Goal:** Submit a Labeling Inquiry form for NEXOLARA with `app_number`, `approval_date`, and `manufacturer`.

Agents must look up the values in the portal before filling the form — hallucinated values will fail the grader.

Scoring: 1.0 (submitted, all 3 fields correct) | 0.75 (2/3) | 0.5 (1/3) | 0.25 (form reached, not submitted) | 0.0

## Action Space

All actions are JSON objects sent as `{"content": <action>}` to `/step`.

```json
{"type": "navigate",  "page": "home|drug_search|doc_archive|forms_hub"}
{"type": "fill",      "element_id": "<field_id>", "value": "<text>"}
{"type": "select",    "element_id": "<dropdown_id>", "value": "<option>"}
{"type": "click",     "element_id": "<element_id>"}
{"type": "submit",    "form_id": "labeling_inquiry"}
{"type": "answer",    "fields": {"field_name": "value", ...}}
```

## Observation Schema

Each step returns:
```json
{
  "content": {
    "current_page": "drug_search",
    "title": "Drug Approval Search",
    "content": "Search for approved drugs...",
    "elements": [
      {"id": "drug_name", "type": "input", "label": "Drug Name (search)"},
      {"id": "search_btn", "type": "button", "label": "Search"}
    ],
    "data": {},
    "error": null,
    "task": "Find the approval date and approved indication for NEXOLARA...",
    "step": 1,
    "steps_remaining": 9
  },
  "metadata": {"session_id": "...", "task_id": "task_1"}
}
```

## Setup

### Local Development

```bash
git clone <repo>
cd open_env_hackthon

pip install -r requirements.txt

# Start the server
uvicorn server:app --host 0.0.0.0 --port 7860

# In another terminal — run the baseline agent
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_SPACE_URL=http://localhost:7860
export OPENAI_API_KEY=your_key_here

python inference.py
```

### Docker

```bash
docker build -t regulatory-portal .
docker run -p 7860:7860 regulatory-portal
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `API_BASE_URL` | OpenAI-compatible API base URL |
| `MODEL_NAME` | Model name (e.g. `gpt-4o-mini`) |
| `HF_SPACE_URL` | URL of the deployed environment |
| `OPENAI_API_KEY` | API key (or `"none"` for local models) |
| `HF_TOKEN` | Hugging Face token (for HF Spaces deployment) |

## API Endpoints

| Endpoint | Method | Body | Returns |
|---------|--------|------|---------|
| `/reset` | POST | `{"task_id": "task_1"}` (optional) | `Observation` |
| `/step` | POST | `{"content": <action>}` | `{"observation": ..., "reward": ..., "done": bool}` |
| `/state` | GET | — | current session state dict |
| `/` | GET | — | health check |

## File Structure

```
├── server.py           # FastAPI app — /reset, /step, /state
├── portal/
│   ├── database.py     # SQLite queries
│   ├── pages.py        # Page renderer (observation per page)
│   ├── actions.py      # Action handler (state transitions)
│   └── session.py      # Session state + task config
├── tasks/
│   ├── task_1.py       # Drug lookup grader
│   ├── task_2.py       # Document retrieval grader
│   └── task_3.py       # Form submission grader
├── models.py           # Pydantic models
├── inference.py        # Baseline agent script
├── portal.db           # Pre-seeded SQLite database
├── seed_db.py          # Recreate portal.db from scratch
├── Dockerfile
├── openenv.yaml
└── requirements.txt
```

## Why This Environment Is Useful

Web/portal navigation is one of the most active agent research areas. Regulatory document workflows represent a real enterprise pain point. This environment tests:

- **Multi-step planning** — the agent must plan a full navigation path, not react greedily
- **Cross-page memory** — values from page 3 must be remembered when filling a form on page 6
- **No hallucination** — graders check exact values from the database; training data guesses fail
- **Distractor navigation** — wrong forms, wrong drug pages, and wrong document types all look plausible
- **Error recovery** — invalid actions land on an error page; the agent must backtrack

The deterministic SQLite backend means ground truth is exact and reproducible across runs.
