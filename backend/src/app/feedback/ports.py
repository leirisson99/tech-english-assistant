from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.feedback.models import SessionFeedback
from app.shared.usage import Usage


@dataclass(frozen=True)
class FeedbackResult:
    feedback: SessionFeedback
    usage: Usage


class FeedbackGenerator(Protocol):
    async def generate(self, user_texts: Sequence[str]) -> FeedbackResult: ...
