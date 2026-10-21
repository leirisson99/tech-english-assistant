# Backend Demands

Backlog of the backend, grouped by **theme**. Each **card** has a name, a description and its tasks.

Status legend: ✅ done · 🔄 in progress · ⬜ to do

Reference: `CONTITUTION.md` (v2.2).

---

## Theme 1 — Project Foundation

### ✅ Card 1.1 — Backend skeleton
**Description:** Create the `backend/` structure following §4.3 of the constitution, using the `src/` layout managed by `uv`.
**Tasks:**
- [x] Create the module folders: `api`, `simulation`, `speech`, `feedback`, `shared`.
- [x] Create `tests/unit`, `tests/integration` and `conftest.py`.
- [x] Write `pyproject.toml` (Python >= 3.12, ruff, mypy, pytest-asyncio).
- [x] Write `.env.example` and the root `.gitignore`.

### ✅ Card 1.2 — Docker Compose for local services
**Description:** Declare Postgres, STT and TTS in `docker-compose.yml` so the whole stack runs locally.
**Tasks:**
- [x] `postgres` service with a named volume and healthcheck.
- [x] `stt` service: ScribeCrate (`hwdsl2/whisper-server`), model `base`, language `en`.
- [x] `tts` service: OVOS TTS server with the Piper engine.
- [x] Bind every port to `127.0.0.1` only.
- [x] Update the constitution (Postgres, STT/TTS in containers).

---

## Theme 2 — Domain Core

### ✅ Card 2.1 — Session rules
**Description:** Model the session lifecycle and its business rules, with no vendor dependency.
**Tasks:**
- [x] `Mode`, `Role`, `Turn`, `Session`, `SessionStatus`.
- [x] Turns must alternate; no turns after the session is finished.
- [x] Empty transcription is rejected and never becomes a turn.
- [x] A session cannot be finished without user speech.
- [x] Usage (tokens and cost) accumulates per session.

### ✅ Card 2.2 — Voice-safe replies
**Description:** Guarantee the Tech Lead reply can be spoken: no markdown, symbols or code, at most 3 sentences.
**Tasks:**
- [x] `make_voice_safe()` strips markdown, links and code blocks.
- [x] Limit the reply to 3 sentences.
- [x] Reject replies with no speakable text.

### ✅ Card 2.3 — Scenarios
**Description:** Per-mode configuration (prompt file and opening line). v1 has only the Daily Stand-up.
**Tasks:**
- [x] `Scenario` model and `get_scenario()`.
- [x] Test that every `Mode` has a scenario.

### ✅ Card 2.4 — Ports and use cases
**Description:** Define the ports and implement the use cases that depend only on them.
**Tasks:**
- [x] Protocols: `SpeechToText`, `TextToSpeech`, `ConversationAgent`, `SessionStore`, `FeedbackGenerator`.
- [x] `SimulationService.start / reply / finish`.
- [x] Atomic turns: nothing is saved if STT, LLM or TTS fails (retry is safe).
- [x] Idempotent `finish`: the same feedback, with no second LLM call.
- [x] Fakes in `conftest.py` and 36 unit tests.

### ✅ Card 2.5 — Structured feedback models
**Description:** Pydantic models for the end-of-session feedback.
**Tasks:**
- [x] `Correction` (non-blank fields, `original != corrected`) and `SessionFeedback`.
- [x] `FeedbackService`: only user speech is sent to the generator.

---

## Theme 3 — Local Infrastructure (Docker)

### ⬜ Card 3.1 — Bring the containers up and validate them
**Description:** Start the stack and confirm the assumptions made while writing `docker-compose.yml`.
**Tasks:**
- [ ] Create `.env` from `.env.example` (change the passwords and the Whisper key).
- [ ] `docker compose up -d` and check that all services are healthy.
- [ ] Confirm the `smartgic/ovos-tts-server-piper:alpha` tag exists.
- [ ] Confirm the Whisper API key is accepted when set by environment variable.
- [ ] Confirm the config and cache mount paths of the TTS container.

### ⬜ Card 3.2 — TTS English voice
**Description:** Configure the Piper voice through `mycroft.conf`.
**Tasks:**
- [ ] Create `docker/ovos/config/mycroft.conf` with the Piper model.
- [ ] `GET /status` shows the expected plugin and language.
- [ ] Generate a WAV with `GET /v2/synthesize` and listen to it.

### ⬜ Card 3.3 — Speech latency spike
**Description:** Measure STT + TTS latency on the target machine (constitution §7).
**Tasks:**
- [ ] Transcribe a ~10 s audio with the `base` model and record the time.
- [ ] Try `small` and compare speed and accuracy.
- [ ] Time the synthesis of a 3-sentence reply.
- [ ] Optionally evaluate `ovos-docker-stt` against ScribeCrate.

---

## Theme 4 — Configuration and Dependencies

### ⬜ Card 4.1 — Update dependencies
**Description:** Adjust `pyproject.toml` to the new stack.
**Tasks:**
- [ ] Remove `faster-whisper` (STT is now a service).
- [ ] Move `httpx` from dev to regular dependencies.
- [ ] Add `sqlalchemy[asyncio]`, `asyncpg` and `alembic`.
- [ ] `uv sync` and keep ruff, mypy and pytest green.

### ⬜ Card 4.2 — Settings
**Description:** Read all configuration from `.env` in one place (`shared/config.py`).
**Tasks:**
- [ ] `Settings` with pydantic-settings: `DATABASE_URL`, `STT_URL`, `STT_API_KEY`, `TTS_URL`.
- [ ] LLM settings: `OPENROUTER_API_KEY`, `LLM_CONVERSATION_MODEL`, `LLM_FEEDBACK_MODEL`, `LLM_FALLBACK_MODEL`.
- [ ] Fail fast with a clear message when a required variable is missing.
- [ ] Unit tests for loading and validation.

---

## Theme 5 — Persistence (PostgreSQL)

### ⬜ Card 5.1 — Database connection and migrations
**Description:** Async engine and migration setup in `shared/db.py`.
**Tasks:**
- [ ] Async SQLAlchemy engine and session factory.
- [ ] Alembic configured for the async engine.
- [ ] First migration: the `sessions` table (turns, usage and feedback stored as JSONB).

### ⬜ Card 5.2 — Postgres session store
**Description:** Implement the `SessionStore` port over Postgres.
**Tasks:**
- [ ] `save` (upsert) and `get`, round-tripping the full `Session`.
- [ ] Integration test against the compose Postgres, behind a flag.
- [ ] Session transcript is persisted (MVP requirement §2.1).

---

## Theme 6 — Speech Adapters

### ⬜ Card 6.1 — ScribeCrate STT adapter
**Description:** Implement `SpeechToText` over `POST /v1/audio/transcriptions`.
**Tasks:**
- [ ] `speech/adapters/scribecrate_stt.py` with `httpx.AsyncClient` and the API key.
- [ ] Send the browser audio format (webm/ogg) and request English.
- [ ] Map HTTP and timeout errors to a clear domain error.
- [ ] Integration test with a real audio sample, behind a flag.

### ⬜ Card 6.2 — OVOS TTS adapter
**Description:** Implement `TextToSpeech` over `GET /v2/synthesize`.
**Tasks:**
- [ ] `speech/adapters/ovos_tts.py` returning WAV bytes.
- [ ] URL-encode the utterance and set a timeout.
- [ ] Map HTTP errors to a clear domain error.
- [ ] Integration test, behind a flag.

---

## Theme 7 — LLM and Agents

### ⬜ Card 7.1 — OpenRouter model factory
**Description:** `shared/llm.py` builds Strands models pointing to OpenRouter. Model choice is configuration only.
**Tasks:**
- [ ] Factory for the conversation model and for the feedback model.
- [ ] Fallback to `LLM_FALLBACK_MODEL` when the primary model fails.
- [ ] Spike: one tool-capable model talking to OpenRouter through Strands.
- [ ] Check that each configured model supports tool calling and structured output.

### ⬜ Card 7.2 — Tech Lead conversation agent
**Description:** Implement the `ConversationAgent` port with a Strands agent.
**Tasks:**
- [ ] `simulation/agent.py` builds the agent from the scenario and loads the prompt file.
- [ ] Write `simulation/prompts/tech_lead.md`: short spoken English, no markdown, never corrects the user.
- [ ] Return the reply text plus token usage and cost from OpenRouter.
- [ ] Integration test, behind a flag.

### ⬜ Card 7.3 — Coach feedback generator
**Description:** Implement the `FeedbackGenerator` port with Strands structured output into `SessionFeedback`.
**Tasks:**
- [ ] Write `feedback/prompts/coach.md`: grammar, phrasing and vocabulary; never comments on pronunciation.
- [ ] Use structured output (never parse free text).
- [ ] Return the feedback plus usage and cost.
- [ ] Integration test, behind a flag.

### ⬜ Card 7.4 — Cost tracking
**Description:** Log token usage and cost per session (golden rule 5).
**Tasks:**
- [ ] Log usage after every turn and after the feedback.
- [ ] Log the session total when it finishes.

---

## Theme 8 — HTTP API

### ⬜ Card 8.1 — App factory and error handling
**Description:** FastAPI app with `create_app()` and domain-to-HTTP error mapping.
**Tasks:**
- [ ] `main.py` registers the routers.
- [ ] Session not found → 404.
- [ ] Session finished, invalid turn order, nothing to review → 409.
- [ ] Empty transcription → 422.
- [ ] Unusable agent reply → 502.

### ⬜ Card 8.2 — Dependency wiring
**Description:** `api/deps.py` is the only place that binds ports to adapters.
**Tasks:**
- [ ] Build the store, STT, TTS, agent and feedback service from `Settings`.
- [ ] Swapping an adapter is a one-line change.

### ⬜ Card 8.3 — Routes
**Description:** Expose the voice loop over HTTP.
**Tasks:**
- [ ] `GET /health`.
- [ ] `POST /sessions` returns the id and the opening line.
- [ ] `POST /sessions/{id}/turns` (audio upload) returns `user_text`, `reply_text` and `audio_base64`.
- [ ] `POST /sessions/{id}/finish` returns `SessionFeedback`.
- [ ] CORS for the Next.js frontend.
- [ ] API tests with `TestClient` and dependency overrides.

---

## Theme 9 — Quality and Documentation

### ⬜ Card 9.1 — Quality gates
**Description:** Keep the checks of §5.3 green and easy to run.
**Tasks:**
- [ ] One command that runs `ruff`, `mypy` and `pytest`.
- [ ] Integration tests skipped unless the flag is set.

### ⬜ Card 9.2 — Design notes
**Description:** One-page notes for the core flows (§5.1).
**Tasks:**
- [ ] `docs/design-notes/001-voice-pipeline.md`: goal, contracts, sequence, risks, cost per session.
- [ ] Notes for the agent loop and the feedback generation.

### ⬜ Card 9.3 — MVP end-to-end check
**Description:** Run a full Daily Stand-up and decide what v2 needs.
**Tasks:**
- [ ] Record, transcribe, reply, speak and finish a real session.
- [ ] Use it daily for one week.
- [ ] Write down what v2 needs.

---

## Suggested order

1. Theme 3 (validate the containers) → Theme 4 (dependencies and settings).
2. Theme 5 (Postgres) and Theme 6 (speech adapters).
3. Theme 7 (LLM and agents).
4. Theme 8 (API) → Theme 9 (quality, docs, end-to-end check).
