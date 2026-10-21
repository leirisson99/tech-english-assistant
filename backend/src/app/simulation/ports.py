from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.shared.usage import Usage
from app.simulation.models import Mode, Session, Turn


@dataclass(frozen=True)
class AgentReply:
    text: str
    usage: Usage


class ConversationAgent(Protocol):
    async def reply(self, mode: Mode, turns: Sequence[Turn]) -> AgentReply: ...


class SessionStore(Protocol):
    async def save(self, session: Session) -> None: ...

    async def get(self, session_id: str) -> Session | None: ...
