from environment.models import Action, ActionType, RewardBreakdown, Severity
from graders.base import BaseGrader
from typing import Dict

SEVERITY_LEVELS = {
    Severity.low:      1,
    Severity.medium:   2,
    Severity.high:     3,
    Severity.critical: 4,
}


class EasyGrader(BaseGrader):

    def __init__(self, sample: Dict):
        super().__init__(ground_truth=sample["ground_truth_bugs"])
        self.bugs  = sample["ground_truth_bugs"]
        self.total = len(self.bugs)
        self.severity_bonus_earned: float = 0.0

    def _match_bug(self, line: int) -> int:
        for i, bug in enumerate(self.bugs):
            if i in self.found_ids:
                continue
            if abs(bug["line"] - line) <= 1:
                return i
        return -1

    def score_action(self, action: Action) -> RewardBreakdown:
        self.step_count += 1
        bd = RewardBreakdown()

        if action.action_type not in (
            ActionType.flag_bug, ActionType.add_comment, ActionType.suggest_fix
        ):
            bd.coverage = len(self.found_ids) / max(self.total, 1)
            return bd

        line = action.line or 0
        idx  = self._match_bug(line)

        if idx >= 0:
            self.found_ids.add(idx)
            gt_bug    = self.bugs[idx]
            agent_sev = SEVERITY_LEVELS.get(action.severity, 0)
            gt_sev    = SEVERITY_LEVELS.get(Severity(gt_bug["severity"]), 0)
            sev_diff  = abs(agent_sev - gt_sev)
            sev_score = max(0.0, 1.0 - sev_diff * 0.3)
            self.severity_bonus_earned += sev_score * 0.2
        else:
            self.false_positives += 1

        coverage  = len(self.found_ids) / self.total
        precision = len(self.found_ids) / (len(self.found_ids) + self.false_positives + 1e-9)
        fp_pen    = min(self.false_positives * 0.05, 0.3)

        bd.coverage               = coverage
        bd.precision              = precision
        bd.severity_match         = self.severity_bonus_earned
        bd.false_positive_penalty = fp_pen
        return bd

    def final_score(self) -> float:
        coverage   = len(self.found_ids) / self.total
        precision  = len(self.found_ids) / max(len(self.found_ids) + self.false_positives, 1)
        sev_bonus  = self.severity_bonus_earned / self.total
        fp_penalty = min(self.false_positives * 0.05, 0.3)
        efficiency = 0.1 if (len(self.found_ids) == self.total and self.step_count <= 10) else 0.0
        score = (0.5 * coverage + 0.25 * precision + 0.15 * sev_bonus + 0.1 * efficiency - fp_penalty)
        return max(0.0, min(1.0, score))
