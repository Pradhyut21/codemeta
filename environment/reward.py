from environment.models import Reward, RewardBreakdown
from graders.base import BaseGrader

STEP_PENALTY = 0.005


def compute_reward(
    grader: BaseGrader,
    breakdown: RewardBreakdown,
    prev_reward: float,
    done: bool,
    step: int,
) -> Reward:

    if done:
        value = grader.final_score()
        delta = value - prev_reward
        return Reward(
            value=max(0.0, min(1.0, value)),
            breakdown=breakdown,
            delta=delta,
            done=True,
            info={"final_score": value, "terminal": True},
        )

    raw = (
        0.50 * breakdown.coverage
        + 0.20 * breakdown.precision
        + 0.15 * breakdown.severity_match
        + 0.10 * breakdown.report_quality
        + 0.05 * breakdown.efficiency
        - breakdown.false_positive_penalty
        - step * STEP_PENALTY
    )
    value = max(0.0, min(1.0, raw))
    delta = value - prev_reward

    return Reward(
        value=value,
        breakdown=breakdown,
        delta=delta,
        done=False,
        info={"intermediate": True, "step": step},
    )
