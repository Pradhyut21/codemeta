from environment.models import Action, ActionType, RewardBreakdown
from graders.base import BaseGrader
from typing import Dict, List
import re

CATEGORY_WEIGHTS = {
    "security":      0.30,
    "reliability":   0.25,
    "api_design":    0.20,
    "observability": 0.15,
    "scalability":   0.10,
}

ISSUE_KEYWORDS = {
    "security": [
        {"hardcoded", "api", "key", "payment"},
        {"hardcoded", "database", "credential", "password"},
        {"jwt", "secret", "source"},
        {"debug", "log", "sensitive", "production"},
    ],
    "reliability": [
        {"retry", "transient", "network", "payment"},
        {"timeout", "http", "request"},
        {"race", "condition", "inventory", "atomic"},
        {"atomic", "bulk", "partial", "reservation"},
        {"leaked", "reservation", "payment", "failure"},
    ],
    "api_design": [
        {"dict", "schema", "pydantic", "validation", "request"},
        {"exception", "raw", "client", "message"},
        {"health", "dependency", "check"},
        {"idempotency", "refund", "duplicate"},
    ],
    "observability": [
        {"print", "logger", "inconsistent", "logging"},
        {"tracing", "correlation", "distributed"},
        {"structured", "json", "log", "format"},
    ],
    "scalability": [
        {"in-memory", "memory", "distributed", "inventory"},
        {"pagination", "low_stock"},
        {"connection", "pool"},
    ],
}


def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-zA-Z_]+", text.lower()))


def _fuzzy_match(agent_text: str, keywords: set) -> bool:
    tokens = _tokenize(agent_text)
    return len(tokens & keywords) >= max(1, len(keywords) // 2)


class HardGrader(BaseGrader):

    def __init__(self, sample: Dict):
        super().__init__(ground_truth=sample["ground_truth_issues"])
        self.issues              = sample["ground_truth_issues"]
        self.report_submitted    = False
        self.report_score        = 0.0
        self.intermediate_flags: List[Dict] = []

    def _score_report(self, report: Dict) -> float:
        all_cats = set(report.keys()) >= set(CATEGORY_WEIGHTS.keys())
        total    = 0.0

        for cat, weight in CATEGORY_WEIGHTS.items():
            gt_issues   = self.issues.get(cat, [])
            agent_items = report.get(cat, [])
            if not gt_issues:
                continue
            kw_list = ISSUE_KEYWORDS.get(cat, [])
            hits = 0
            for i, kw in enumerate(kw_list):
                if i >= len(gt_issues):
                    break
                for item in agent_items:
                    if _fuzzy_match(str(item), kw):
                        hits += 1
                        break
            recall    = hits / len(gt_issues)
            precision = hits / max(len(agent_items), 1)
            f1 = (2 * precision * recall / (precision + recall)
                  if (precision + recall) > 0 else 0.0)
            total += f1 * weight

        bonus = 0.1 if all_cats else 0.0
        return min(1.0, total + bonus)

    def score_action(self, action: Action) -> RewardBreakdown:
        self.step_count += 1
        bd = RewardBreakdown()

        if action.action_type in (
            ActionType.flag_bug, ActionType.flag_vulnerability, ActionType.add_comment
        ):
            self.intermediate_flags.append({"action": action})
            self.found_ids.add(len(self.intermediate_flags))
            bd.coverage = min(len(self.intermediate_flags) / 15.0, 0.4)
            return bd

        if action.action_type == ActionType.submit_report and action.report:
            self.report_submitted = True
            self.report_score     = self._score_report(action.report)
            bd.report_quality     = self.report_score
            bd.coverage           = self.report_score

        return bd

    def final_score(self) -> float:
        if not self.report_submitted:
            return min(len(self.intermediate_flags) / 30.0, 0.25)
        return self.report_score

