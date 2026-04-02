# 🛡️ CodeSentinel

**A real-world AI training environment for automated code review and security auditing.**

CodeSentinel is a production-grade [OpenEnv](https://huggingface.co/spaces/openenv/openenv)-compliant environment submitted to the Hugging Face OpenEnv hackathon. Agents learn to review code the way a senior software engineer would — finding bugs, auditing for OWASP vulnerabilities, and producing structured architecture reports.

---

## Motivation

Code review is one of the most high-stakes daily tasks in software engineering. Every line of code that ships without review is a potential bug or security hole. Despite this, code review is still largely a manual process that is:

- **Time-consuming** — a typical PR review takes 30–120 minutes.
- **Inconsistent** — quality varies widely by reviewer expertise and fatigue.
- **Incomplete** — reviewers miss between 15% and 35% of defects on average.

Training language models to review code well is not just an academic exercise. A model that can reliably flag injection vulnerabilities, catch off-by-one errors, and evaluate microservice designs would provide direct value to every software team in the world.

CodeSentinel provides a **dense, structured reward signal** that teaches agents not just *what* to report, but *how precise* to be, *how severe* to classify issues, and *how efficiently* to complete a review.

---

## Tasks

| Task | Difficulty | Max Steps | Description |
|---|---|---|---|
| `bug_detection` | 🟢 Easy | 20 | Find 5 logical bugs in a Python service |
| `security_audit` | 🟡 Medium | 30 | Identify 7 OWASP Top-10 vulnerabilities in a Flask app |
| `architecture_review` | 🔴 Hard | 50 | Produce a structured report on a 4-file microservice codebase |

---

## Observation Space

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Task identifier |
| `task_description` | string | Natural language task brief |
| `files` | `CodeFile[]` | Source files to review (filename, language, content, line_count) |
| `history` | `ReviewComment[]` | All previous actions taken this episode |
| `step` | int | Current step number (0-indexed) |
| `max_steps` | int | Maximum allowed steps before episode terminates |
| `done` | bool | Whether the episode has ended |
| `hint` | string \| null | Optional task hint |

---

## Action Space

| Field | Type | Description |
|---|---|---|
| `action_type` | enum | One of: `flag_bug`, `flag_vulnerability`, `add_comment`, `suggest_fix`, `request_changes`, `approve`, `submit_report` |
| `line` | int \| null | Source line number the action refers to |
| `filename` | string \| null | Target filename |
| `message` | string \| null | Human-readable description of the finding |
| `severity` | `low\|medium\|high\|critical` \| null | Finding severity |
| `cve_category` | string \| null | OWASP category string (e.g. `A03_Injection`) |
| `original_code` | string \| null | Code being replaced (for `suggest_fix`) |
| `suggested_code` | string \| null | Replacement code (for `suggest_fix`) |
| `report` | dict \| null | Structured architecture report (for `submit_report`) |
| `reason` | string \| null | Explanation for terminal actions |

---

## Reward Function

### Non-terminal steps

```
reward = 0.50 × coverage
       + 0.20 × precision
       + 0.15 × severity_match
       + 0.10 × report_quality
       + 0.05 × efficiency
       − false_positive_penalty
       − step × 0.005
```
Clamped to `[0.0, 1.0]`. Delta (change from previous step) is also returned.

### Terminal step

```
reward = grader.final_score() − step × 0.005
```

### Grader Details

**Bug Detection (Easy)**
```
final = 0.50 × coverage
      + 0.25 × precision
      + 0.15 × severity_match   (0.20 bonus per exact severity match)
      + 0.10 × efficiency_bonus (0.10 if all bugs found ≤ 10 steps)
      − 0.05 × false_positives
```
A correct flag requires line number within **±1** of the ground-truth bug.

**Security Audit (Medium)**
- Full hit (correct OWASP category + line within ±2): `category_weight`
- Partial hit (correct OWASP category, wrong line): `0.5 × category_weight`
- OWASP weights: A01/A03=1.5, A02/A07=1.3, others=1.0
- Terminal score = weighted F1 − FP penalty
- `approve` on vulnerable codebase → **score 0.0**

**Architecture Review (Hard)**
- Only `submit_report` action scores terminally
- Fuzzy keyword matching (≥50% keywords must match)
- Per-category F1, weights: security=0.30, reliability=0.25, api_design=0.20, observability=0.15, scalability=0.10
- +0.10 bonus if all 5 categories present
- Intermediate flags give partial credit (capped at 0.25)

---

## Setup — Local Development

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app:app --host 0.0.0.0 --port 7860 --reload

# 4. Visit http://localhost:7860
```

---

## Docker

```bash
# Build
docker build -t codesentinel .

# Run
docker run -p 7860:7860 codesentinel

# Visit http://localhost:7860
```

---

## API Usage Examples

### Start an episode
```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "bug_detection", "seed": 42}'
```

### Submit an action
```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "flag_bug", "line": 20, "severity": "high", "message": "KeyError on missing cache key"}'
```

### Check environment state
```bash
curl http://localhost:7860/state
```

### Health check
```bash
curl http://localhost:7860/validate
```

---

## Baseline Scores (GPT-4o)

```bash
export OPENAI_API_KEY="sk-..."
python baseline/run_baseline.py --base-url http://localhost:7860 --seed 42
```

| Task | Score | Progress |
|---|---|---|
| `bug_detection` | ~0.71 | `████████████████░░░░` |
| `security_audit` | ~0.58 | `████████████░░░░░░░░` |
| `architecture_review` | ~0.43 | `█████████░░░░░░░░░░░` |
| **Average** | **~0.57** | `███████████░░░░░░░░░` |

---

## Project Structure

```
codesentinel/
├── Dockerfile              # Container definition for Hugging Face Spaces
├── README.md
├── openenv.yaml            # OpenEnv metadata and spec
├── requirements.txt
├── app.py                  # FastAPI server
├── environment/
│   ├── models.py           # Pydantic v2 models
│   ├── env.py              # CodeSentinelEnv (reset/step/state)
│   └── reward.py           # Non-sparse reward computation
├── tasks/
│   └── registry.py         # Episode builder and task metadata
├── graders/
│   ├── base.py             # Abstract grader
│   ├── easy_grader.py      # Bug detection grader
│   ├── medium_grader.py    # Security audit grader
│   └── hard_grader.py      # Architecture review grader
├── data/
│   └── samples.py          # Embedded code samples and ground truth
└── baseline/
    └── run_baseline.py     # GPT-4o evaluation script
```

---

## License

MIT — see `openenv.yaml` for metadata.
