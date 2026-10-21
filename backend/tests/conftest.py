from collections.abc import Sequence

import pytest

from app.feedback.models import Correction, SessionFeedback
from app.feedback.ports import FeedbackResult
from app.feedback.service import FeedbackService
from app.shared.usage import Usage
from app.simulation.models import Mode, Session, Turn
from app.simulation.ports import AgentReply
from app.simulation.service import SimulationService


class FakeSTT:
    def __init__(self, texts: Sequence[str] = ("I finished the login task.",)) -> None:
        self._texts = list(texts)
        self.calls = 0

    async def transcribe(self, audio: bytes) -> str:
        self.calls += 1
        return self._texts.pop(0) if len(self._texts) > 1 else self._texts[0]


class FakeTTS:
    def __init__(self) -> None:
        self.spoken: list[str] = []

    async def synthesize(self, text: str) -> bytes:
        self.spoken.append(text)
        return b"fake-audio"


class FakeAgent:
    def __init__(self, text: str = "Nice. Any blockers?") -> None:
        self.text = text
        self.calls: list[list[Turn]] = []
        self.error: Exception | None = None

    async def reply(self, mode: Mode, turns: Sequence[Turn]) -> AgentReply:
        self.calls.append(list(turns))
        if self.error:
            raise self.error
        usage = Usage(input_tokens=10, output_tokens=5, cost_usd=0.001)
        return AgentReply(text=self.text, usage=usage)


class FakeFeedbackGenerator:
    def __init__(self) -> None:
        self.received: list[Sequence[str]] = []

    async def generate(self, user_texts: Sequence[str]) -> FeedbackResult:
        self.received.append(list(user_texts))
        feedback = SessionFeedback(
            corrections=[
                Correction(
                    original="I finish the task",
                    corrected="I finished the task",
                    explanation="Use the past tense for completed actions.",
                )
            ],
            better_phrasing=["I wrapped up the login task."],
            vocabulary=["blocker"],
            overall_comment="Good session.",
        )
        usage = Usage(input_tokens=100, output_tokens=50, cost_usd=0.01)
        return FeedbackResult(feedback=feedback, usage=usage)


class InMemorySessionStore:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    async def save(self, session: Session) -> None:
        self.sessions[session.id] = session.model_copy(deep=True)

    async def get(self, session_id: str) -> Session | None:
        session = self.sessions.get(session_id)
        return session.model_copy(deep=True) if session else None


@pytest.fixture
def stt() -> FakeSTT:
    return FakeSTT()


@pytest.fixture
def tts() -> FakeTTS:
    return FakeTTS()


@pytest.fixture
def agent() -> FakeAgent:
    return FakeAgent()


@pytest.fixture
def generator() -> FakeFeedbackGenerator:
    return FakeFeedbackGenerator()


@pytest.fixture
def store() -> InMemorySessionStore:
    return InMemorySessionStore()


@pytest.fixture
def service(
    store: InMemorySessionStore,
    agent: FakeAgent,
    stt: FakeSTT,
    tts: FakeTTS,
    generator: FakeFeedbackGenerator,
) -> SimulationService:
    return SimulationService(
        store=store,
        agent=agent,
        stt=stt,
        tts=tts,
        feedback=FeedbackService(generator),
    )
