import random
from environment.models import TaskId, CodeFile, Observation
from data.samples import EASY_SAMPLES, MEDIUM_SAMPLES, HARD_SAMPLES
from graders.easy_grader   import EasyGrader
from graders.medium_grader import MediumGrader
from graders.hard_grader   import HardGrader

TASK_META = {
    TaskId.bug_detection: {
        "description": (
            "Review the Python code below and find ALL logical bugs, type errors, "
            "and code quality issues. For each bug call flag_bug with the exact line "
            "number, severity (low/medium/high/critical), and a clear description. "
            "When done, call request_changes."
        ),
        "max_steps": 20,
        "hint": (
            "Look for: missing error handling, off-by-one errors, wrong operators, "
            "weak cryptography, and division-by-zero risks."
        ),
    },
    TaskId.security_audit: {
        "description": (
            "Perform a security audit of the web application code below. Identify "
            "OWASP Top-10 vulnerabilities. For each: call flag_vulnerability with "
            "line number, OWASP category (e.g. A03_Injection), and severity. "
            "Never call approve if vulnerabilities remain. End with request_changes."
        ),
        "max_steps": 30,
        "hint": None,
    },
    TaskId.architecture_review: {
        "description": (
            "Review this multi-file microservice codebase. Identify architectural "
            "issues across: security, reliability, api_design, observability, scalability. "
            "Add intermediate comments, then submit ONE final structured report via "
            "submit_report with format {category: [list of issues]}."
        ),
        "max_steps": 50,
        "hint": None,
    },
}


def build_episode(task_id: TaskId, seed: int = 42):
    random.seed(seed)
    meta = TASK_META[task_id]

    if task_id == TaskId.bug_detection:
        sample = random.choice(EASY_SAMPLES)
        grader = EasyGrader(sample)
        files  = [CodeFile(
            filename   = sample["filename"],
            language   = sample["language"],
            content    = sample["content"],
            line_count = len(sample["content"].splitlines()),
        )]

    elif task_id == TaskId.security_audit:
        sample = random.choice(MEDIUM_SAMPLES)
        grader = MediumGrader(sample)
        files  = [CodeFile(
            filename   = sample["filename"],
            language   = sample["language"],
            content    = sample["content"],
            line_count = len(sample["content"].splitlines()),
        )]

    else:  # architecture_review
        sample = random.choice(HARD_SAMPLES)
        grader = HardGrader(sample)
        files  = [
            CodeFile(
                filename   = f["filename"],
                language   = f["language"],
                content    = f["content"],
                line_count = len(f["content"].splitlines()),
            )
            for f in sample["files"]
        ]

    obs = Observation(
        task_id          = task_id,
        task_description = meta["description"],
        files            = files,
        step             = 0,
        max_steps        = meta["max_steps"],
        done             = False,
        hint             = meta.get("hint"),
    )
    return sample, grader, obs
