import pytest
from tests.conftest import FakeFeedbackGenerator

from app.feedback.models import NoUserSpeechError
from app.feedback.service import FeedbackService


async def test_generate_sends_only_non_blank_user_texts(generator: FakeFeedbackGenerator):
    result = await FeedbackService(generator).generate(["I finish the task", "  ", "Bye"])
    assert generator.received == [["I finish the task", "Bye"]]
    assert result.feedback.corrections


async def test_generate_without_speech_never_calls_the_llm(generator: FakeFeedbackGenerator):
    with pytest.raises(NoUserSpeechError):
        await FeedbackService(generator).generate(["", "  "])
    assert generator.received == []
