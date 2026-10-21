from collections.abc import Sequence

from app.feedback.models import NoUserSpeechError
from app.feedback.ports import FeedbackGenerator, FeedbackResult


class FeedbackService:
    def __init__(self, generator: FeedbackGenerator) -> None:
        self._generator = generator

    async def generate(self, user_texts: Sequence[str]) -> FeedbackResult:
        texts = [t.strip() for t in user_texts if t.strip()]
        if not texts:
            raise NoUserSpeechError("no user speech to review")
        return await self._generator.generate(texts)
