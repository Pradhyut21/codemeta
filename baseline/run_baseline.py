"""
CodeSentinel Baseline Inference Script
Uses the OpenAI client to run gpt-4o against all 3 tasks.
Reads API key from OPENAI_API_KEY env var.
Usage: python baseline/run_baseline.py [--base-url http://localhost:7860] [--seed 42]
"""
import os
import json
import argparse
import sys

try:
    import httpx
except ImportError:
    import urllib.request as _urllib
    httpx = None

from openai import OpenAI

BASE_URL = "http://localhost:7860"

SYSTEM_PROMPT = """\
You are an expert software engineer performing code review.
You will be shown code and must identify issues by calling the correct action.

Available actions (respond ONLY with valid JSON, no prose, no markdown fences):
  flag_bug:           {"action_type":"flag_bug","line":<int>,"severity":<low|medium|high|critical>,"message":"<description>"}
  flag_vulnerability: {"action_type":"flag_vulnerability","line":<int>,"cve_category":"<OWASP cat>","severity":<level>,"message":"<desc>"}
  add_comment:        {"action_type":"add_comment","line":<int>,"message":"<comment>"}
  request_changes:    {"action_type":"request_changes","reason":"<summary of all findings>"}
  approve:            {"action_type":"approve","reason":"<reason — only if truly no issues>"}
  submit_report:      {"action_type":"submit_report","report":{"security":[...],"reliability":[...],"api_design":[...],"observability":[...],"scalability":[...]}}

Respond with exactly ONE JSON action per turn. No prose, no markdown fences.
"""


def _post(url: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    if httpx:
        return httpx.post(url, content=body, headers={"Content-Type": "application/json"}).json()
    req = __import__("urllib.request").request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with __import__("urllib.request").request.urlopen(req) as r:
        return json.loads(r.read())


def _get(url: str) -> dict:
    if httpx:
        return httpx.get(url).json()
    with __import__("urllib.request").request.urlopen(url) as r:
        return json.loads(r.read())


def obs_to_prompt(obs: dict) -> str:
    lines = [
        f"Task: {obs['task_id']}",
        f"Step: {obs['step']}/{obs['max_steps']}",
    ]
    if obs.get("hint"):
        lines.append(f"Hint: {obs['hint']}")
    lines.append(f"\nObjective:\n{obs['task_description']}\n")
    for f in obs["files"]:
        lines.append(f"=== {f['filename']} ===\n{f['content']}")
    if obs["history"]:
        lines.append("\nYour actions so far:")
        for h in obs["history"][-6:]:
            lines.append(f"  Step {h['step']}: {h['action']} line={h.get('line')} — {h['message']}")
    return "\n".join(lines)


def run_task(client: OpenAI, task_id: str, seed: int = 42) -> float:
    print(f"\n{'='*60}")
    print(f"  Task: {task_id.upper()}")
    print(f"{'='*60}")

    reset_resp = _post(f"{BASE_URL}/reset", {"task_id": task_id, "seed": seed})
    obs        = reset_resp["observation"]
    messages   = [{"role": "system", "content": SYSTEM_PROMPT}]
    final_score = 0.0

    for _ in range(obs["max_steps"]):
        messages.append({"role": "user", "content": obs_to_prompt(obs)})

        completion = client.chat.completions.create(
            model       = "gpt-4o",
            messages    = messages,
            temperature = 0.0,
            max_tokens  = 512,
        )
        raw_action = completion.choices[0].message.content.strip()
        print(f"  Step {obs['step']+1}: {raw_action[:100]}")
        messages.append({"role": "assistant", "content": raw_action})

        try:
            action = json.loads(raw_action)
        except json.JSONDecodeError:
            print("  [WARN] Invalid JSON — skipping step")
            continue

        step_resp   = _post(f"{BASE_URL}/step", action)
        obs         = step_resp["observation"]
        reward      = step_resp["reward"]
        done        = step_resp["done"]
        final_score = step_resp["info"].get("final_score") or reward["value"]

        print(f"         reward={reward['value']:.3f}  delta={reward['delta']:+.3f}  done={done}")
        if done:
            break

    print(f"\n  FINAL SCORE: {final_score:.4f}")
    return final_score or 0.0


def ascii_bar(score: float, width: int = 20) -> str:
    filled = round(score * width)
    return "█" * filled + "░" * (width - filled)


def main():
    parser = argparse.ArgumentParser(description="CodeSentinel GPT-4o baseline")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--seed",     type=int, default=42)
    args = parser.parse_args()

    global BASE_URL
    BASE_URL = args.base_url

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("ERROR: Set OPENAI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    tasks  = ["bug_detection", "security_audit", "architecture_review"]
    scores = {}

    for task_id in tasks:
        try:
            scores[task_id] = run_task(client, task_id, seed=args.seed)
        except Exception as exc:
            print(f"  [ERROR] {exc}")
            scores[task_id] = 0.0

    print(f"\n{'='*60}")
    print("  BASELINE RESULTS")
    print(f"{'='*60}")
    for task_id, score in scores.items():
        print(f"  {task_id:<25} [{ascii_bar(score)}]  {score:.4f}")
    avg = sum(scores.values()) / len(scores)
    print(f"\n  Average score: {avg:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
