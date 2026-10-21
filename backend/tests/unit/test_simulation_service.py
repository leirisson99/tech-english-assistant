import pytest
from tests.conftest import (
    FakeAgent,
    FakeFeedbackGenerator,
    FakeSTT,
    FakeTTS,
    InMemorySessionStore,
)

from app.simulation.models import (
    EmptyTranscriptError,
    Mode,
    NothingToReviewError,
    Role,
    SessionClosedError,
    SessionNotFoundError,
    SessionStatus,
)
from app.simulation.scenarios import get_scenario
from app.simulation.service import SimulationService


async def test_start_opens_with_the_tech_lead_and_persists(
    service: SimulationService, store: InMemorySessionStore
):
    session = await service.start(Mode.DAILY_STANDUP)
    assert session.status is SessionStatus.ACTIVE
    assert [t.role for t in session.turns] == [Role.TECH_LEAD]
    assert session.turns[0].text == get_scenario(Mode.DAILY_STANDUP).opening_line
    assert session.id in store.sessions


async def test_reply_runs_the_voice_pipeline(
    service: SimulationService, store: InMemorySessionStore, tts: FakeTTS
):
    session = await service.start(Mode.DAILY_STANDUP)
    result = await service.reply(session.id, b"audio")

    assert result.user_text == "I finished the login task."
    assert result.reply_text == "Nice. Any blockers?"
    assert result.audio == b"fake-audio"
    assert tts.spoken == ["Nice. Any blockers?"]

    saved = store.sessions[session.id]
    assert [t.role for t in saved.turns] == [Role.TECH_LEAD, Role.USER, Role.TECH_LEAD]
    assert saved.usage.cost_usd == pytest.approx(0.001)


async def test_reply_is_made_voice_safe(
    service: SimulationService, agent: FakeAgent, tts: FakeTTS
):
    agent.text = "**Great** job! One. Two. Three."
    session = await service.start(Mode.DAILY_STANDUP)
    result = await service.reply(session.id, b"audio")
    assert result.reply_text == "Great job! One. Two."
    assert tts.spoken == ["Great job! One. Two."]


async def test_reply_unknown_session(service: SimulationService):
    with pytest.raises(SessionNotFoundError):
        await service.reply("nope", b"audio")


async def test_empty_transcription_is_not_recorded_and_agent_not_called(
    store: InMemorySessionStore, agent: FakeAgent, tts: FakeTTS, generator: FakeFeedbackGenerator
):
    from app.feedback.service import FeedbackService

    service = SimulationService(
        store=store, agent=agent, stt=FakeSTT([" "]), tts=tts, feedback=FeedbackService(generator)
    )
    session = await service.start(Mode.DAILY_STANDUP)
    with pytest.raises(EmptyTranscriptError):
        await service.reply(session.id, b"audio")
    assert agent.calls == []
    assert len(store.sessions[session.id].turns) == 1


async def test_agent_failure_leaves_the_session_untouched_and_retryable(
    service: SimulationService, store: InMemorySessionStore, agent: FakeAgent
):
    session = await service.start(Mode.DAILY_STANDUP)
    agent.error = RuntimeError("llm down")
    with pytest.raises(RuntimeError):
        await service.reply(session.id, b"audio")
    assert len(store.sessions[session.id].turns) == 1

    agent.error = None
    result = await service.reply(session.id, b"audio")
    assert result.reply_text


async def test_reply_on_finished_session_does_not_transcribe(
    service: SimulationService, stt: FakeSTT
):
    session = await service.start(Mode.DAILY_STANDUP)
    await service.reply(session.id, b"audio")
    await service.finish(session.id)
    calls_before = stt.calls
    with pytest.raises(SessionClosedError):
        await service.reply(session.id, b"audio")
    assert stt.calls == calls_before


async def test_finish_generates_feedback_from_user_turns_only(
    service: SimulationService, store: InMemorySessionStore, generator: FakeFeedbackGenerator
):
    session = await service.start(Mode.DAILY_STANDUP)
    await service.reply(session.id, b"audio")

    feedback = await service.finish(session.id)

    assert generator.received == [["I finished the login task."]]
    saved = store.sessions[session.id]
    assert saved.status is SessionStatus.FINISHED
    assert saved.feedback == feedback
    assert saved.usage.cost_usd == pytest.approx(0.011)


async def test_finish_is_idempotent(
    service: SimulationService, generator: FakeFeedbackGenerator
):
    session = await service.start(Mode.DAILY_STANDUP)
    await service.reply(session.id, b"audio")
    first = await service.finish(session.id)
    second = await service.finish(session.id)
    assert first == second
    assert len(generator.received) == 1


async def test_finish_without_user_speech_is_rejected_before_the_llm(
    service: SimulationService, generator: FakeFeedbackGenerator, store: InMemorySessionStore
):
    session = await service.start(Mode.DAILY_STANDUP)
    with pytest.raises(NothingToReviewError):
        await service.finish(session.id)
    assert generator.received == []
    assert store.sessions[session.id].status is SessionStatus.ACTIVE


async def test_finish_unknown_session(service: SimulationService):
    with pytest.raises(SessionNotFoundError):
        await service.finish("nope")
