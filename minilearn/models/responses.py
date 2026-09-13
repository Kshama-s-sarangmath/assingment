from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LearningResponse(BaseModel):
    type: Literal[
        "search",
        "enroll",
        "enrolled",
        "enrollment_list",
        "unenroll",
        "unenrolled",
        "answer",
    ] = Field(
        description="Action category for this turn. Pick the value that best matches the learner request."
    )
    title: str = Field(
        description="Short UI-ready heading that summarizes the answer or action outcome."
    )
    learning_ids: list[str] = Field(
        default_factory=list,
        description="Relevant learning IDs referenced by the answer, in priority order.",
    )
    message: str = Field(
        description="Concise learner-facing explanation. Mention applied filters or action outcome when helpful."
    )
    next_step_questions: list[str] = Field(
        default_factory=list,
        description="Two to four short follow-up prompts the learner could ask next.",
    )


def fallback_response(message: str, title: str = "MiniLearn ran into a problem") -> LearningResponse:
    return LearningResponse(
        type="answer",
        title=title,
        learning_ids=[],
        message=message,
        next_step_questions=[
            "Show me beginner AI courses",
            "What am I enrolled in?",
        ],
    )
