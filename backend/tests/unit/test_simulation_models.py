import pytest

from app.shared.usage import Usage
from app.simulation.models import (
    EmptyTranscriptError,
    Mode,
    NothingToReviewError,
    Role,
    Session,
    SessionClosedError,
    SessionStatus,
    TurnOrderError,
    VoiceUnsafeReplyError,
    make_voice_safe,
)


def new_session() -> Session:
    return Session(mode=Mode.DAILY_STANDUP)


def test_new_session_is_active_and_empty():
    session = new_session()
    assert session.status is SessionStatus.ACTIVE
    assert session.turns == []
    assert session.feedback is None


def test_turns_must_alternate():
    session = new_session()
    session.add_tech_lead_turn("Good morning!")
    session.add_user_turn("Hi.")
    session.add_tech_lead_turn("What did you do yesterday?")
    assert [t.role for t in session.turns] == [Role.TECH_LEAD, Role.USER, Role.TECH_LEAD]


def test_two_user_turns_in_a_row_are_rejected():
    session = new_session()
    session.add_user_turn("Hi.")
    with pytest.raises(TurnOrderError):
        session.add_user_turn("Hello again.")


def test_two_tech_lead_turns_in_a_row_are_rejected():
    session = new_session()
    session.add_tech_lead_turn("Good morning!")
    with pytest.raises(TurnOrderError):
        session.add_tech_lead_turn("Anyone there?")


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_empty_user_text_is_rejected_and_not_recorded(text: str):
    session = new_session()
    with pytest.raises(EmptyTranscriptError):
        session.add_user_turn(text)
    assert session.turns == []


def test_turn_text_is_stripped():
    session = new_session()
    turn = session.add_user_turn("  hello  ")
    assert turn.text == "hello"


def test_cannot_finish_without_user_speech():
    session = new_session()
    session.add_tech_lead_turn("Good morning!")
    with pytest.raises(NothingToReviewError):
        session.finish()
    assert session.status is SessionStatus.ACTIVE


def test_finish_closes_the_session():
    session = new_session()
    session.add_user_turn("Hi.")
    session.finish()
    assert session.status is SessionStatus.FINISHED


def test_finished_session_rejects_new_turns_and_second_finish():
    session = new_session()
    session.add_user_turn("Hi.")
    session.finish()
    with pytest.raises(SessionClosedError):
        session.add_tech_lead_turn("Bye.")
    with pytest.raises(SessionClosedError):
        session.finish()


def test_user_turns_only_returns_user_speech():
    session = new_session()
    session.add_tech_lead_turn("Good morning!")
    session.add_user_turn("Hi.")
    assert [t.text for t in session.user_turns] == ["Hi."]


def test_usage_accumulates():
    session = new_session()
    session.record_usage(Usage(input_tokens=10, output_tokens=5, cost_usd=0.001))
    session.record_usage(Usage(input_tokens=1, output_tokens=2, cost_usd=0.002))
    assert session.usage.input_tokens == 11
    assert session.usage.output_tokens == 7
    assert session.usage.cost_usd == pytest.approx(0.003)


def test_voice_safe_keeps_plain_text():
    assert make_voice_safe("Nice work. Any blockers?") == "Nice work. Any blockers?"


def test_voice_safe_strips_markdown_and_code():
    text = "## Great!\n- **Nice** work on `login`.\n```py\nprint(1)\n```\nSee [docs](http://x.io)."
    result = make_voice_safe(text)
    assert not any(c in result for c in "#*`[]()")
    assert "print" not in result
    assert "docs" in result


def test_voice_safe_limits_to_three_sentences():
    result = make_voice_safe("One. Two. Three. Four. Five.")
    assert result == "One. Two. Three."


def test_voice_safe_rejects_empty_reply():
    with pytest.raises(VoiceUnsafeReplyError):
        make_voice_safe("```code only```")
