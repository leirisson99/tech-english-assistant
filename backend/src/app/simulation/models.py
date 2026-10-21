import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.feedback.models import SessionFeedback
from app.shared.usage import Usage

MAX_REPLY_SENTENCES = 3


class SessionError(Exception):
    """Base class for session rule violations."""


class SessionNotFoundError(SessionError): ...


class SessionClosedError(SessionError): ...


class TurnOrderError(SessionError): ...


class EmptyTranscriptError(SessionError): ...


class NothingToReviewError(SessionError): ...


class VoiceUnsafeReplyError(SessionError): ...


class Mode(StrEnum):
    DAILY_STANDUP = "daily_standup"


class Role(StrEnum):
    USER = "user"
    TECH_LEAD = "tech_lead"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    FINISHED = "finished"


def _now() -> datetime:
    return datetime.now(UTC)


class Turn(BaseModel):
    role: Role
    text: str
    created_at: datetime = Field(default_factory=_now)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    mode: Mode
    status: SessionStatus = SessionStatus.ACTIVE
    turns: list[Turn] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
    feedback: SessionFeedback | None = None
    created_at: datetime = Field(default_factory=_now)

    @property
    def user_turns(self) -> list[Turn]:
        return [t for t in self.turns if t.role is Role.USER]

    def add_user_turn(self, text: str) -> Turn:
        if not text.strip():
            raise EmptyTranscriptError("the transcription is empty")
        return self._add_turn(Role.USER, text)

    def add_tech_lead_turn(self, text: str) -> Turn:
        return self._add_turn(Role.TECH_LEAD, text)

    def record_usage(self, usage: Usage) -> None:
        self.usage = self.usage + usage

    def finish(self) -> None:
        self.ensure_active()
        if not self.user_turns:
            raise NothingToReviewError("the session has no user speech to review")
        self.status = SessionStatus.FINISHED

    def _add_turn(self, role: Role, text: str) -> Turn:
        self.ensure_active()
        if self.turns and self.turns[-1].role is role:
            raise TurnOrderError(f"two {role.value} turns in a row")
        turn = Turn(role=role, text=text.strip())
        self.turns.append(turn)
        return turn

    def ensure_active(self) -> None:
        if self.status is not SessionStatus.ACTIVE:
            raise SessionClosedError("the session is already finished")


_CODE_BLOCK = re.compile(r"```.*?```", re.DOTALL)
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_LINE_MARKER = re.compile(r"^\s*(?:[#>*+\-]+|\d+\.)\s+", re.MULTILINE)
_SYMBOLS = re.compile(r"[*_`~#>|\[\]()]")
_SENTENCE = re.compile(r"[^.!?]+[.!?]*")


def make_voice_safe(text: str, max_sentences: int = MAX_REPLY_SENTENCES) -> str:
    """Strip markdown/code and keep at most `max_sentences`, so the text can be spoken."""
    text = _CODE_BLOCK.sub(" ", text)
    text = _LINK.sub(r"\1", text)
    text = _LINE_MARKER.sub("", text)
    text = " ".join(_SYMBOLS.sub("", text).split())
    sentences = [s.strip() for s in _SENTENCE.findall(text) if s.strip()]
    if not sentences:
        raise VoiceUnsafeReplyError("the reply has no speakable text")
    return " ".join(sentences[:max_sentences])
