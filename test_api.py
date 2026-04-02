"""Integration test for the revised CodeSentinel implementation."""
import urllib.request
import json

BASE = "http://localhost:7860"

def post(path, data):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    r = urllib.request.urlopen(req)
    return json.loads(r.read())

def get(path):
    r = urllib.request.urlopen(BASE + path)
    return json.loads(r.read())

# 1. Validate
v = get("/validate")
assert v["valid"], "validate must return valid=true"
assert "message" in v, "validate must have message field"
print(f"VALIDATE: {v['message']}")

# 2. Bug detection
r1 = post("/reset", {"task_id": "bug_detection", "seed": 42})
obs = r1
print(f"RESET bug_detection: step={obs['step']} max={obs['max_steps']} files={len(obs['files'])}")
assert obs["step"] == 0 and obs["max_steps"] == 20

# correct flag
s1 = post("/step", {"action_type": "flag_bug", "line": 10, "severity": "high", "message": "KeyError not handled"})
print(f"  STEP1 (hit):  reward={s1['reward']['value']:.4f} delta={s1['reward']['delta']:+.4f}")
assert s1["reward"]["value"] > 0

# false positive
s2 = post("/step", {"action_type": "flag_bug", "line": 99, "severity": "low", "message": "fake"})
print(f"  STEP2 (miss): reward={s2['reward']['value']:.4f} delta={s2['reward']['delta']:+.4f}")

# terminal
s3 = post("/step", {"action_type": "request_changes", "reason": "bugs found"})
assert s3["done"], "episode must end on request_changes"
print(f"  STEP3 (terminal): done={s3['done']} reward={s3['reward']['value']:.4f}")
assert "final_score" in s3["info"]

# state
st = get("/state")
print(f"  STATE: found={st['found_count']} fp={st['false_positive_count']} score={st['current_score']:.4f}")

# step after done → 400
try:
    post("/step", {"action_type": "add_comment", "message": "late"})
    print("ERROR: expected HTTP 400 after done")
    exit(1)
except urllib.error.HTTPError as e:
    assert e.code == 400
    print(f"  Step-after-done correctly returned HTTP {e.code}")

# 3. Security audit
r2 = post("/reset", {"task_id": "security_audit", "seed": 42})
obs2 = r2
print(f"RESET security_audit: files={len(obs2['files'])} max={obs2['max_steps']}")
assert obs2["max_steps"] == 30

s_sec = post("/step", {
    "action_type": "flag_vulnerability",
    "line": 5,
    "cve_category": "A07_Identification_Failures",
    "severity": "critical",
    "message": "hardcoded secret key"
})
print(f"  SEC STEP1: reward={s_sec['reward']['value']:.4f}")
assert s_sec["reward"]["value"] >= 0

# 4. Architecture review
r3 = post("/reset", {"task_id": "architecture_review", "seed": 42})
obs3 = r3
print(f"RESET architecture_review: files={len(obs3['files'])} max={obs3['max_steps']}")
assert obs3["max_steps"] == 50 and len(obs3["files"]) == 4

report = {
    "security":      ["Hardcoded production API key in payment service", "Hardcoded database credentials password in settings"],
    "reliability":   ["No retry logic on payment API calls transient network", "No request timeout on http calls", "Race condition in inventory reserve check-then-act atomic"],
    "api_design":    ["Generic dict input no pydantic schema validation on request", "Raw exception message returned to client", "Health endpoint no dependency check", "No idempotency key refund duplicate"],
    "observability": ["print mixed with logger inconsistent logging", "No tracing correlation distributed", "No structured json log format"],
    "scalability":   ["In-memory inventory store not distributed", "get_low_stock no pagination", "No connection pool"],
}
s_arch = post("/step", {"action_type": "submit_report", "report": report})
print(f"  ARCH SUBMIT: reward={s_arch['reward']['value']:.4f} done={s_arch['done']}")
assert s_arch["done"]
assert s_arch["reward"]["value"] > 0

print("\n=== ALL TESTS PASSED ===")
