from abc import ABC, abstractmethod
from typing import Any
from environment.models import Action, RewardBreakdown


class BaseGrader(ABC):

    def __init__(self, ground_truth: Any):
        self.ground_truth    = ground_truth
        self.found_ids:      set = set()
        self.false_positives: int = 0
        self.step_count:     int = 0

    @abstractmethod
    def score_action(self, action: Action) -> RewardBreakdown:
        ...

    @abstractmethod
    def final_score(self) -> float:
        ...

    def reset(self):
        self.found_ids       = set()
        self.false_positives = 0
        self.step_count      = 0
