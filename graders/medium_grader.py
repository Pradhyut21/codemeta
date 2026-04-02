from environment.models import Action, ActionType, RewardBreakdown
from graders.base import BaseGrader
from typing import Dict

OWASP_WEIGHTS = {
    "A01_Broken_Access_Control":     1.5,
    "A02_Cryptographic_Failures":    1.3,
    "A03_Injection":                 1.5,
    "A04_Insecure_Design":           1.0,
    "A05_Security_Misconfiguration": 1.0,
    "A06_Vulnerable_Components":     1.0,
    "A07_Identification_Failures":   1.2,
}


class MediumGrader(BaseGrader):

    def __init__(self, sample: Dict):
        super().__init__(ground_truth=sample["ground_truth_vulnerabilities"])
        self.vulns                = sample["ground_truth_vulnerabilities"]
        self.total                = len(self.vulns)
        self.weighted_hits:       float = 0.0
        self.approved_vulnerable: bool  = False

    def _match_vuln(self, action: Action):
        for i, v in enumerate(self.vulns):
            if i in self.found_ids:
                continue
            cat_match  = (action.cve_category == v["category"])
            line_match = (action.line is not None and abs(action.line - v["line"]) <= 2)
            if cat_match and line_match:
                return i, False   # full hit
            if cat_match:
                return i, True    # partial hit
        return -1, False

    def score_action(self, action: Action) -> RewardBreakdown:
        self.step_count += 1
        bd = RewardBreakdown()

        if action.action_type == ActionType.approve:
            self.approved_vulnerable = True
            bd.false_positive_penalty = 0.5
            return bd

        if action.action_type != ActionType.flag_vulnerability:
            bd.coverage = self.weighted_hits / max(self.total, 1)
            return bd

        idx, partial = self._match_vuln(action)
        if idx >= 0:
            self.found_ids.add(idx)
            weight    = OWASP_WEIGHTS.get(self.vulns[idx]["category"], 1.0)
            hit_value = 0.5 if partial else 1.0
            self.weighted_hits += hit_value * weight
        else:
            self.false_positives += 1

        max_weighted = sum(OWASP_WEIGHTS.get(v["category"], 1.0) for v in self.vulns)
        precision    = len(self.found_ids) / max(len(self.found_ids) + self.false_positives, 1)

        bd.coverage               = self.weighted_hits / max(max_weighted, 1)
        bd.precision              = precision
        bd.false_positive_penalty = min(self.false_positives * 0.08, 0.4)
        return bd

    def final_score(self) -> float:
        if self.approved_vulnerable:
            return 0.0
        max_weighted = sum(OWASP_WEIGHTS.get(v["category"], 1.0) for v in self.vulns)
        recall    = self.weighted_hits / max(max_weighted, 1)
        precision = len(self.found_ids) / max(len(self.found_ids) + self.false_positives, 1)
        if precision + recall < 1e-9:
            return 0.0
        f1 = 2 * precision * recall / (precision + recall)
        return max(0.0, min(1.0, f1 - min(self.false_positives * 0.05, 0.25)))
