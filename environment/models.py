from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"


class ActionType(str, Enum):
    add_comment        = "add_comment"
    flag_bug           = "flag_bug"
    flag_vulnerability = "flag_vulnerability"
    suggest_fix        = "suggest_fix"
    request_changes    = "request_changes"
    approve            = "approve"
    submit_report      = "submit_report"


class TaskId(str, Enum):
    bug_detection       = "bug_detection"
    security_audit      = "security_audit"
    architecture_review = "architecture_review"


class CodeFile(BaseModel):
    filename:   str = Field(..., description="Relative path of the file")
    language:   str = Field(..., description="Programming language")
    content:    str = Field(..., description="Full source code content")
    line_count: int = Field(..., description="Number of lines")


class ReviewComment(BaseModel):
    step:     int
    action:   ActionType
    line:     Optional[int] = None
    message:  str
    severity: Optional[Severity] = None


class Observation(BaseModel):
    task_id:          TaskId
    task_description: str
    files:            List[CodeFile]
    history:          List[ReviewComment] = Field(default_factory=list)
    step:             int  = Field(0)
    max_steps:        int  = Field(20)
    done:             bool = Field(False)
    hint:             Optional[str] = Field(None)


class Action(BaseModel):
    action_type:    ActionType
    line:           Optional[int]    = None
    filename:       Optional[str]    = None
    message:        Optional[str]    = None
    severity:       Optional[Severity] = None
    cve_category:   Optional[str]    = None
    original_code:  Optional[str]    = None
    suggested_code: Optional[str]    = None
    report:         Optional[Dict[str, Any]] = None
    reason:         Optional[str]    = None


class RewardBreakdown(BaseModel):
    coverage:               float = 0.0
    precision:              float = 0.0
    severity_match:         float = 0.0
    false_positive_penalty: float = 0.0
    efficiency:             float = 0.0
    report_quality:         float = 0.0


class Reward(BaseModel):
    value:     float = Field(..., ge=0.0, le=1.0)
    breakdown: RewardBreakdown
    delta:     float = 0.0
    done:      bool  = False
    info:      Dict[str, Any] = Field(default_factory=dict)


class EnvironmentState(BaseModel):
    task_id:              TaskId
    step:                 int
    max_steps:            int
    done:                 bool
    ground_truth_count:   int
    found_count:          int
    false_positive_count: int
    cumulative_reward:    float
    current_score:        float


class StepResponse(BaseModel):
    observation: Observation
    reward:      Reward
    done:        bool
    info:        Dict[str, Any] = Field(default_factory=dict)


class ResetResponse(BaseModel):
    observation: Observation
    info:        Dict[str, Any] = Field(default_factory=dict)


class ValidateResponse(BaseModel):
    valid:   bool
    version: str
    tasks:   List[str]
    message: str
