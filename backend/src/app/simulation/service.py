from dataclasses import dataclass

from app.feedback.models import SessionFeedback
from app.feedback.service import FeedbackService
from app.simulation.models import (
    Mode,
    Session,
    SessionNotFoundError,
    SessionStatus,
    make_voice_safe,
)
from app.simulation.ports import ConversationAgent, SessionStore
from app.simulation.scenarios import get_scenario
from app.speech.ports import SpeechToText, TextToSpeech


@dataclass(frozen=True)
class TurnResult:
    user_text: str
    reply_text: str
    audio: bytes


class SimulationService:
    def __init__(
        self,
        store: SessionStore,
        agent: ConversationAgent,
        stt: SpeechToText,
        tts: TextToSpeech,
        feedback: FeedbackService,
    ) -> None:
        self._store = store
        self._agent = agent
        self._stt = stt
        self._tts = tts
        self._feedback = feedback

    async def start(self, mode: Mode) -> Session:
        session = Session(mode=mode)
        session.add_tech_lead_turn(get_scenario(mode).opening_line)
        await self._store.save(session)
        return session

    async def reply(self, session_id: str, audio: bytes) -> TurnResult:
        session = await self._load(session_id)
        session.ensure_active()  # fail before spending any STT time

        # Work on a copy: nothing is saved unless the whole turn succeeds.
        work = session.model_copy(deep=True)
        text = await self._stt.transcribe(audio)
        user_turn = work.add_user_turn(text)

        agent_reply = await self._agent.reply(work.mode, work.turns)
        reply_text = make_voice_safe(agent_reply.text)
        work.add_tech_lead_turn(reply_text)
        work.record_usage(agent_reply.usage)

        speech = await self._tts.synthesize(reply_text)
        await self._store.save(work)
        return TurnResult(user_text=user_turn.text, reply_text=reply_text, audio=speech)

    async def finish(self, session_id: str) -> SessionFeedback:
        session = await self._load(session_id)
        if session.status is SessionStatus.FINISHED and session.feedback is not None:
            return session.feedback

        work = session.model_copy(deep=True)
        work.finish()

        result = await self._feedback.generate([t.text for t in work.user_turns])
        work.feedback = result.feedback
        work.record_usage(result.usage)
        await self._store.save(work)
        return result.feedback

    async def _load(self, session_id: str) -> Session:
        session = await self._store.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session
