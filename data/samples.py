EASY_SAMPLE_1 = {
    "filename": "user_service.py",
    "language": "python",
    "content": """\
import hashlib
from typing import List


class UserService:
    def __init__(self, users: dict):
        self.users = users

    def get_user_name(self, user_id: int) -> str:
        # BUG-1 (line 10): KeyError not handled
        return self.users[user_id]["name"]

    def get_active_users(self, users: List[dict]) -> List[dict]:
        result = []
        # BUG-2 (line 15): off-by-one, skips last user
        for i in range(len(users) - 1):
            if users[i].get("active"):
                result.append(users[i])
        return result

    def compute_checksum(self, data: str) -> str:
        # BUG-3 (line 22): MD5 is cryptographically broken
        return hashlib.md5(data.encode()).hexdigest()

    def update_email(self, user_id: int, new_email: str) -> bool:
        user = self.users.get(user_id)
        if user:
            user["email"] == new_email  # BUG-4 (line 27): == instead of =
            return True
        return False

    def calculate_average_age(self, user_ids: List[int]) -> float:
        total = 0
        for uid in user_ids:
            total += self.users[uid]["age"]
        # BUG-5 (line 34): ZeroDivisionError if user_ids is empty
        return total / len(user_ids)
""",
    "ground_truth_bugs": [
        {"line": 10, "type": "missing_error_handling", "severity": "high",
         "description": "KeyError not caught; user_id may not exist"},
        {"line": 15, "type": "off_by_one", "severity": "medium",
         "description": "range(len(users)-1) skips the last element"},
        {"line": 22, "type": "weak_cryptography", "severity": "high",
         "description": "MD5 is broken; use hashlib.sha256"},
        {"line": 27, "type": "assignment_operator", "severity": "high",
         "description": "== used instead of =; update silently ignored"},
        {"line": 34, "type": "zero_division", "severity": "medium",
         "description": "ZeroDivisionError when user_ids is empty"},
    ],
}

EASY_SAMPLE_2 = {
    "filename": "order_processor.py",
    "language": "python",
    "content": """\
from datetime import datetime
from typing import List, Dict, Any

DISCOUNT_RATES = {"gold": 0.20, "silver": 0.10, "bronze": 0.05}


def apply_discount(price: float, tier: str) -> float:
    # BUG-1 (line 8): KeyError if tier not in DISCOUNT_RATES
    discount = DISCOUNT_RATES[tier]
    return price * (1 - discount)


def process_orders(orders: List[Dict[str, Any]]) -> List[Dict]:
    results = []
    for order in orders:
        # BUG-2 (line 15): mutates original dict in-place
        order["processed"] = True
        order["timestamp"] = datetime.now().isoformat()
        results.append(order)
    return results


def find_duplicate_orders(orders: List[Dict]) -> List[str]:
    seen = []
    duplicates = []
    for order in orders:
        oid = order["order_id"]
        # BUG-3 (line 25): O(n^2) list scan; should be a set
        if oid in seen:
            duplicates.append(oid)
        seen.append(oid)
    return duplicates


def calculate_total(items: List[Dict]) -> float:
    # BUG-4 (line 32): no guard for empty list
    return sum(i["price"] * i["quantity"] for i in items) / len(items)


def format_currency(amount: float) -> str:
    # BUG-5 (line 36): float imprecision for financial data; use Decimal
    return f"${amount:.2f}"
""",
    "ground_truth_bugs": [
        {"line": 8,  "type": "missing_error_handling", "severity": "high",
         "description": "KeyError if tier not in DISCOUNT_RATES"},
        {"line": 15, "type": "mutation_side_effect", "severity": "medium",
         "description": "Mutates original dict instead of copying"},
        {"line": 25, "type": "performance", "severity": "low",
         "description": "O(n^2) list scan; use a set for O(1) lookup"},
        {"line": 32, "type": "zero_division", "severity": "medium",
         "description": "ZeroDivisionError when items is empty"},
        {"line": 36, "type": "financial_precision", "severity": "medium",
         "description": "Float imprecision for financial data; use Decimal"},
    ],
}

MEDIUM_SAMPLE_1 = {
    "filename": "auth_api.py",
    "language": "python",
    "content": """\
import sqlite3
from flask import Flask, request, jsonify, session

app = Flask(__name__)
# VULN-1 (line 5): hardcoded secret key
app.secret_key = "super_secret_key_123"

# VULN-2 (line 8): hardcoded DB password
DB_PASSWORD = "admin123"


def get_db():
    return sqlite3.connect("users.db")


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    db = get_db()
    # VULN-3 (line 20): SQL Injection via f-string
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    user = db.execute(query).fetchone()
    if user:
        session["user_id"] = user[0]
        return jsonify({"status": "ok"})
    return jsonify({"status": "invalid"}), 401


@app.route("/search", methods=["GET"])
def search():
    term = request.args.get("q", "")
    # VULN-4 (line 30): Reflected XSS
    return f"<html><body><h1>Results for: {term}</h1></body></html>"


@app.route("/profile", methods=["GET"])
def profile():
    user_id = request.args.get("user_id")
    # VULN-5 (line 36): IDOR - no authorization check
    db = get_db()
    user = db.execute(f"SELECT * FROM users WHERE id={user_id}").fetchone()
    return jsonify({"user": user})


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    # VULN-6 (line 43): Unrestricted file upload
    file.save(f"/uploads/{file.filename}")
    return jsonify({"status": "uploaded"})


if __name__ == "__main__":
    # VULN-7 (line 48): Debug mode in production
    app.run(debug=True, host="0.0.0.0")
""",
    "ground_truth_vulnerabilities": [
        {"line": 5,  "category": "A07_Identification_Failures",
         "owasp": "A07:2021", "severity": "critical",
         "description": "Hardcoded secret key in source"},
        {"line": 8,  "category": "A02_Cryptographic_Failures",
         "owasp": "A02:2021", "severity": "critical",
         "description": "Hardcoded DB password"},
        {"line": 20, "category": "A03_Injection",
         "owasp": "A03:2021", "severity": "critical",
         "description": "SQL Injection via f-string interpolation"},
        {"line": 30, "category": "A03_Injection",
         "owasp": "A03:2021", "severity": "high",
         "description": "Reflected XSS — unescaped user input in HTML"},
        {"line": 36, "category": "A01_Broken_Access_Control",
         "owasp": "A01:2021", "severity": "high",
         "description": "IDOR — no authorization before profile access"},
        {"line": 43, "category": "A04_Insecure_Design",
         "owasp": "A04:2021", "severity": "high",
         "description": "Unrestricted file upload, no type check"},
        {"line": 48, "category": "A05_Security_Misconfiguration",
         "owasp": "A05:2021", "severity": "medium",
         "description": "Flask debug mode exposes Werkzeug debugger"},
    ],
}

HARD_SAMPLE_1 = {
    "files": [
        {
            "filename": "services/payment_service.py",
            "language": "python",
            "content": """\
import requests

PAYMENT_API_URL = "https://api.payments.io/v1"
API_KEY = "pk_live_abc123xyz"   # hardcoded production key


def charge_card(card_token: str, amount: int, currency: str = "USD"):
    # No retry, no timeout
    response = requests.post(
        f"{PAYMENT_API_URL}/charges",
        json={"token": card_token, "amount": amount, "currency": currency},
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    if response.status_code == 200:
        return response.json()
    raise Exception(f"Payment failed: {response.text}")


def refund_charge(charge_id: str, amount: int):
    # No idempotency key
    response = requests.post(
        f"{PAYMENT_API_URL}/refunds",
        json={"charge_id": charge_id, "amount": amount},
        headers={"Authorization": f"Bearer {API_KEY}"},
    )
    return response.json()
""",
        },
        {
            "filename": "services/inventory_service.py",
            "language": "python",
            "content": """\
from typing import Dict, List

# In-memory store — lost on restart, not thread-safe
_inventory: Dict[str, int] = {}


def reserve_item(item_id: str, quantity: int) -> bool:
    # Race condition: check-then-act not atomic
    current = _inventory.get(item_id, 0)
    if current < quantity:
        return False
    _inventory[item_id] = current - quantity
    return True


def restock(item_id: str, quantity: int) -> None:
    # No validation — accepts negative quantity
    _inventory[item_id] = _inventory.get(item_id, 0) + quantity


def get_low_stock(threshold: int = 10) -> List[str]:
    # No pagination — could return millions of items
    return [k for k, v in _inventory.items() if v < threshold]


def bulk_reserve(items: List[Dict]) -> Dict[str, bool]:
    # Not atomic — partial reservation possible
    results = {}
    for item in items:
        results[item["id"]] = reserve_item(item["id"], item["qty"])
    return results
""",
        },
        {
            "filename": "api/router.py",
            "language": "python",
            "content": """\
from fastapi import FastAPI, HTTPException
from services import payment_service, inventory_service

app = FastAPI()
print("Starting API server")   # mixing print with logger


@app.post("/orders")
def create_order(order: dict):   # no Pydantic schema
    item_id    = order["item_id"]
    quantity   = order["quantity"]
    card_token = order["card_token"]
    amount     = order["amount"]

    reserved = inventory_service.reserve_item(item_id, quantity)
    if not reserved:
        raise HTTPException(status_code=409, detail="Out of stock")

    try:
        result = payment_service.charge_card(card_token, amount)
        return {"status": "ok", "charge": result}
    except Exception as e:
        # Inventory NOT released on payment failure — leaked reservation
        # Raw exception message returned to client
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    # No dependency checks
    return {"status": "ok"}
""",
        },
        {
            "filename": "config/settings.py",
            "language": "python",
            "content": """\
# All config hardcoded — no env vars
DATABASE_URL   = "postgresql://admin:password123@localhost:5432/appdb"
REDIS_URL      = "redis://localhost:6379"
JWT_SECRET     = "my_jwt_secret_do_not_share"
LOG_LEVEL      = "DEBUG"   # leaks sensitive data in production
PAYMENT_API_KEY = "pk_live_abc123xyz"

# No pydantic BaseSettings, no dev/staging/prod distinction
""",
        },
    ],
    "ground_truth_issues": {
        "security": [
            "Hardcoded production API key in payment_service.py",
            "Hardcoded database credentials in settings.py",
            "JWT secret committed to source code",
            "DEBUG log level leaks sensitive data in production",
        ],
        "reliability": [
            "No retry logic on payment API calls",
            "No request timeout on external HTTP calls",
            "Race condition in inventory reserve_item",
            "Partial reservation in bulk_reserve — no atomicity",
            "Leaked inventory reservation on payment failure",
        ],
        "api_design": [
            "Generic dict input in create_order — no Pydantic schema",
            "Raw exception message returned to client",
            "Health endpoint has no dependency checks",
            "No idempotency key in refund_charge",
        ],
        "observability": [
            "print() mixed with logger — inconsistent logging",
            "No distributed tracing or correlation IDs",
            "No structured JSON log format",
        ],
        "scalability": [
            "In-memory inventory store — not distributed-safe",
            "get_low_stock has no pagination",
            "No connection pooling configured",
        ],
    },
}

EASY_SAMPLES   = [EASY_SAMPLE_1, EASY_SAMPLE_2]
MEDIUM_SAMPLES = [MEDIUM_SAMPLE_1]
HARD_SAMPLES   = [HARD_SAMPLE_1]
