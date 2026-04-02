from __future__ import annotations
from typing import Optional

from environment.models import (
    Action, Observation, EnvironmentState,
    StepResponse, ResetResponse, TaskId, ReviewComment,
)
from environment.reward import compute_reward
from graders.base import BaseGrader
from tasks.registry import build_episode


class CodeSentinelEnv:

    def __init__(self):
        self._task_id:           Optional[TaskId]      = None
        self._obs:               Optional[Observation] = None
        self._grader:            Optional[BaseGrader]  = None
        self._prev_reward:       float = 0.0
        self._done:              bool  = False
        self._step:              int   = 0
        self._max_steps:         int   = 20
        self._cumulative_reward: float = 0.0

    def reset(
        self,
        task_id: TaskId = TaskId.bug_detection,
        seed:    int    = 42,
    ) -> ResetResponse:
        sample, grader, obs = build_episode(task_id, seed=seed)
        self._task_id            = task_id
        self._obs                = obs
        self._grader             = grader
        self._prev_reward        = 0.0
        self._done               = False
        self._step               = 0
        self._max_steps          = obs.max_steps
        self._cumulative_reward  = 0.0
        return ResetResponse(
            observation=obs,
            info={"task_id": task_id, "seed": seed, "max_steps": obs.max_steps},
        )

    def step(self, action: Action) -> StepResponse:
        if self._obs is None:
            raise RuntimeError("Call reset() before step().")
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        self._step += 1

        terminal_actions = {"approve", "request_changes", "submit_report"}
        episode_done = (
            action.action_type.value in terminal_actions
            or self._step >= self._max_steps
        )

        breakdown = self._grader.score_action(action)
        reward    = compute_reward(
            grader=self._grader,
            breakdown=breakdown,
            prev_reward=self._prev_reward,
            done=episode_done,
            step=self._step,
        )

        self._prev_reward        = reward.value
        self._cumulative_reward += reward.value
        self._done               = episode_done

        self._obs.history.append(ReviewComment(
            step     = self._step,
            action   = action.action_type,
            line     = action.line,
            message  = action.message or str(action.report or action.reason or ""),
            severity = action.severity,
        ))
        self._obs.step = self._step
        self._obs.done = episode_done

        return StepResponse(
            observation=self._obs,
            reward=reward,
            done=episode_done,
            info={
                "step": self._step,
                "cumulative_reward": self._cumulative_reward,
                "final_score": self._grader.final_score() if episode_done else None,
            },
        )

    def state(self) -> EnvironmentState:
        if self._task_id is None:
            raise RuntimeError("Call reset() first.")
        g = self._grader
        return EnvironmentState(
            task_id              = self._task_id,
            step                 = self._step,
            max_steps            = self._max_steps,
            done                 = self._done,
            ground_truth_count   = len(g.ground_truth) if isinstance(g.ground_truth, list) else sum(len(v) for v in g.ground_truth.values()),
            found_count          = len(g.found_ids),
            false_positive_count = g.false_positives,
            cumulative_reward    = self._cumulative_reward,
            current_score        = g.final_score(),
        )
