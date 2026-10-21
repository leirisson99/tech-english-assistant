# 📜 Project Constitution: Tech English Assistant

> Version 2.2 — October 2026
> Personal, locally-run tool for daily English practice through voice simulations with an AI "Tech Lead".

---

## 1. Purpose

The **Tech English Assistant** helps a software professional build English fluency through short, daily, voice-driven simulations of real tech work situations (dailies, code reviews, interviews), followed by immediate, structured feedback on grammar, phrasing and corporate vocabulary.

**Primary goal:** daily practice.
**Secondary goal:** a well-engineered portfolio project.

When these conflict, **practice wins**: a usable feature today beats a perfect architecture next month.

---

## 2. Scope

### 2.1 MVP (v1) — "usable in two weekends"
- One simulation: **Daily Stand-up**.
- **Turn-based voice loop (push-to-talk):** record → transcribe → agent replies → reply is spoken.
- **End-of-session feedback** returned as structured data (corrections, better phrasing, vocabulary).
- Session transcript saved locally.
- Single user, no authentication.

### 2.2 Out of scope for v1
- Bidirectional real-time audio streaming (WebSockets).
- Multiple users, accounts, cloud deployment.
- Progress analytics and spaced repetition.

### 2.3 Planned (v2+)
- Simulations: **Code Review**, **Mock Interview**, **Incident Postmortem**.
- Streaming pipeline (WebSocket) for lower perceived latency.
- Progress tracking: recurring mistakes, vocabulary acquired over time.

---

## 3. Technology Stack

### 3.1 Backend — Python + FastAPI + Strands Agents
- **FastAPI:** async HTTP API with automatic OpenAPI docs.
- **Strands Agents SDK (`strands-agents`):** agent loop, conversation/session management, tools and structured output for the "Tech Lead" persona.
- **Pydantic:** all input/output contracts and structured feedback models.
- **Persistence:** PostgreSQL, running in Docker (`docker-compose.yml`). Single local user for now; the data lives in a named Docker volume.

### 3.2 LLM Provider — OpenRouter
- **OpenRouter** is the single gateway for all LLM calls, through its OpenAI-compatible API (`https://openrouter.ai/api/v1`).
- Integrated in Strands via the OpenAI-compatible model provider, pointing `base_url` to OpenRouter.
- **Model choice is configuration, never code.** Models are selected by environment variables:

| Variable | Purpose |
|---|---|
| `OPENROUTER_API_KEY` | Authentication |
| `LLM_CONVERSATION_MODEL` | Fast, cheap model for the live conversation turns |
| `LLM_FEEDBACK_MODEL` | Stronger model for end-of-session structured feedback |
| `LLM_FALLBACK_MODEL` | Used if the primary model fails or is unavailable |

- **Requirement:** every configured model must support **tool calling** and **structured output** on OpenRouter. Verify this on the model page before adopting it.
- **Two-model strategy:** conversation turns need low latency; feedback needs quality. Splitting them keeps the loop fast and the cost low.
- **Cost tracking:** log token usage and cost reported by OpenRouter per session. Set a monthly spending limit in the OpenRouter dashboard.

### 3.3 Speech — Local by default
OpenRouter covers text generation only. Speech runs locally, in Docker containers, to keep it free and private:
- **STT:** [ScribeCrate](https://github.com/hwdsl2/scribecrate) (`hwdsl2/whisper-server`, faster-whisper inside). OpenAI-compatible API: `POST /v1/audio/transcriptions`. Start with the `base` English model; tune for speed vs. accuracy.
- **TTS:** [ovos-docker-tts](https://github.com/OpenVoiceOS/ovos-docker-tts) with the **Piper** engine (`smartgic/ovos-tts-server-piper`). Kokoro is available in the same project as an alternative.
- **STT candidate to evaluate:** [ovos-docker-stt](https://github.com/OpenVoiceOS/ovos-docker-stt). It does the same job as ScribeCrate, so it is only worth adding as a second adapter if it measures better.
- Both sit behind interfaces (see §4.4) so another engine or a cloud provider can be swapped in later.
- All services (Postgres, STT, TTS) are declared in `docker-compose.yml` at the repository root. The backend itself runs on the host.

### 3.4 Frontend — Next.js (App Router) + TypeScript
- Simple UI: simulation selector, push-to-talk button, transcript view, feedback panel.
- Audio capture with the browser `MediaRecorder` API; audio playback of TTS responses.

---

## 4. Architecture

### 4.1 Pipeline (v1, turn-based)

```
[Browser] --audio--> POST /sessions/{id}/turns
                        │
                        ├─ Speech.transcribe()      (ScribeCrate container, local)
                        ├─ Simulation.reply()       (Strands agent → OpenRouter)
                        ├─ Speech.synthesize()      (OVOS Piper container, local)
                        ▼
[Browser] <--text + audio-- response

POST /sessions/{id}/finish → Feedback.generate() → structured feedback (Pydantic)
```

### 4.2 Modules (lightweight DDD)
Clear boundaries, without ceremony. The backend is organized **by domain module (vertical slices)**; each module owns its models, logic, ports and adapters.

- `simulation/` — scenarios, Tech Lead persona, Strands agent and session lifecycle.
- `speech/` — STT and TTS.
- `feedback/` — structured feedback generation and models.
- `shared/` — config, LLM provider factory, persistence.

A `user/` module will only be created when there is user data beyond a config file.

### 4.3 Project structure (monorepo)

```
tech-english-assistant/
├── CONSTITUTION.md
├── docker-compose.yml             # Postgres, STT (ScribeCrate), TTS (OVOS Piper)
├── .env.example                   # variables read by docker-compose
├── docker/                        # config mounted into the containers
├── docs/
│   └── design-notes/              # lightweight SDDs (001-voice-pipeline.md, ...)
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── src/app/
│   │   ├── main.py                # FastAPI app factory, router registration
│   │   ├── api/
│   │   │   ├── deps.py            # dependency injection: binds ports to adapters
│   │   │   └── routes/
│   │   │       ├── sessions.py
│   │   │       └── health.py
│   │   ├── simulation/
│   │   │   ├── models.py          # Session, Turn, Mode (Pydantic)
│   │   │   ├── service.py         # start / reply / finish use cases
│   │   │   ├── agent.py           # builds the Strands Agent
│   │   │   ├── scenarios.py       # per-mode configuration
│   │   │   └── prompts/
│   │   │       └── tech_lead.md
│   │   ├── speech/
│   │   │   ├── ports.py           # SpeechToText, TextToSpeech (Protocols)
│   │   │   └── adapters/
│   │   │       ├── scribecrate_stt.py
│   │   │       └── ovos_tts.py
│   │   ├── feedback/
│   │   │   ├── models.py          # SessionFeedback, Correction
│   │   │   ├── service.py
│   │   │   └── prompts/
│   │   │       └── coach.md
│   │   └── shared/
│   │       ├── config.py          # pydantic-settings (reads .env)
│   │       ├── llm.py             # OpenRouter model factory
│   │       └── db.py              # PostgreSQL
│   └── tests/
│       ├── unit/                  # mirrors src/app
│       ├── integration/           # real adapters, behind a flag
│       └── conftest.py            # fake STT / TTS / LLM
└── frontend/
    ├── package.json
    └── src/
        ├── app/                   # App Router routes
        │   ├── page.tsx           # mode selection
        │   └── session/[id]/page.tsx
        ├── features/
        │   ├── recorder/          # useRecorder (MediaRecorder), push-to-talk
        │   ├── conversation/      # transcript, audio player
        │   └── feedback/          # feedback panel
        ├── components/ui/         # generic UI components
        └── lib/
            ├── api.ts             # typed backend client
            └── api-types.ts       # generated from FastAPI OpenAPI
```

**Structure rules**
1. **Services depend on ports, never on vendors.** `service.py` imports only `ports.py` and models. Strands, ScribeCrate, OVOS, the Postgres driver and OpenRouter appear only in `agent.py`, `adapters/` and `shared/llm.py`.
2. **`api/deps.py` is the only place that wires ports to adapters.** Swapping an adapter is a one-line change there.
3. **Prompts are Markdown files inside their module**, loaded at runtime and versioned in Git.
4. **Unit tests use fakes from `conftest.py`.** No network or real models; those belong in `integration/`.
5. **No speculative folders.** `user/`, `repositories/` or new layers are added only when a second real use case exists.
6. **Backend uses the `src/` layout** (managed with `uv`) to avoid import issues in tests.
7. **Frontend types are generated from the FastAPI OpenAPI schema** (`openapi-typescript`), so a contract change breaks `tsc` instead of production.

### 4.4 Adapter rule
The domain never imports a vendor SDK directly. Every external capability has an interface:

- `LLMProvider` → OpenRouter model factory in `shared/llm.py` (default)
- `SpeechToText` → `ScribeCrateSTT` (default)
- `TextToSpeech` → `OvosTTS` (default, Piper engine)

Switching a model or provider must require **only a configuration change**.

### 4.5 Structured feedback
Feedback is produced with Strands **structured output** into a Pydantic model — never by parsing free text:

```python
class Correction(BaseModel):
    original: str
    corrected: str
    explanation: str

class SessionFeedback(BaseModel):
    corrections: list[Correction]
    better_phrasing: list[str]
    vocabulary: list[str]
    overall_comment: str
```

### 4.6 Agents and prompts
Two agents with separate responsibilities:

| Agent | Model | Prompt | Output |
|---|---|---|---|
| Conversation (Tech Lead) | `LLM_CONVERSATION_MODEL` | `simulation/prompts/tech_lead.md` | Short spoken English text, sent to TTS |
| Feedback (Coach) | `LLM_FEEDBACK_MODEL` | `feedback/prompts/coach.md` | `SessionFeedback` (structured output) |

- The conversation agent **never corrects** during the session; it only keeps the conversation flowing.
- Conversation output is **voice-safe**: no markdown, symbols or code; 1–3 sentences per turn.
- The feedback agent **never comments on pronunciation**, since it only sees STT text.

---

## 5. Engineering Practices

### 5.1 Design notes (lightweight SDD)
- Required only for **core flows**: the voice pipeline, the agent loop, and the feedback generation.
- Format: one page max — goal, contracts (Pydantic), sequence, risks, estimated cost per session.
- Small features go straight to code.

### 5.2 Testing (pragmatic TDD)
- **Red → Green → Refactor** for domain logic, Pydantic schemas and session rules.
- External services (OpenRouter, STT, TTS) are **mocked** behind their interfaces in unit tests.
- One integration test per adapter, run manually or behind a flag (it costs tokens).
- Tools: **Pytest** (+ `pytest-asyncio`) on the backend, **Vitest** on the frontend.

### 5.3 Quality gates
- Linting/formatting: Ruff (backend), ESLint + Prettier (frontend).
- Type checking: mypy or Pyright (backend), `tsc --noEmit` (frontend).

---

## 6. Golden Rules

1. **English First.** All code, commits, docs and technical notes are written in English. Feedback explanations to the user default to English; Portuguese is an optional setting.
2. **Practice over perfection.** If a decision delays the first usable version, simplify it.
3. **Provider-agnostic AI.** OpenRouter is the gateway, but no model is hard-coded. Models live in configuration.
4. **Local and private by default.** Audio never leaves the machine. Only text goes to OpenRouter.
5. **Cost-aware.** Every session logs token usage and cost. Budget limits are set at the provider.
6. **Secrets stay out of Git.** API keys live in `.env`; the repo ships a `.env.example`.

---

## 7. Next Steps

- [ ] Scaffold the monorepo following §4.3.
- [ ] Spike: Strands agent talking to OpenRouter with one tool-capable model.
- [ ] Spike: measure local STT + TTS latency on the target machine.
- [ ] Write the first design note: *Turn-based Voice Pipeline*.
- [ ] Build the MVP Daily Stand-up simulation end to end.
- [ ] Use it daily for one week, then decide what v2 needs.