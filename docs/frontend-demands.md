# Frontend Demands

Backlog of the frontend (Next.js App Router + TypeScript), grouped by **theme**. Each **card** has a name, a description and its tasks.

Status legend: ✅ done · 🔄 in progress · ⬜ to do

Reference: `CONTITUTION.md` (v2.2), §3.4 and §4.3. Backend backlog: `docs/backend-demands.md`.

The frontend does **not exist yet**, so every card is to do.

---

## Theme 1 — Project Foundation

### ⬜ Card 1.1 — Frontend skeleton
**Description:** Create the `frontend/` project following §4.3 of the constitution.
**Tasks:**
- [ ] Create the Next.js app (App Router, TypeScript, `src/` directory).
- [ ] Create the folders: `app`, `features/{recorder,conversation,feedback}`, `components/ui`, `lib`.
- [ ] Create the routes: `app/page.tsx` and `app/session/[id]/page.tsx` (empty for now).
- [ ] Add `frontend/.env.example` with the backend URL (`NEXT_PUBLIC_API_URL`).
- [ ] Update the root `.gitignore` for `node_modules` and `.next`.

### ⬜ Card 1.2 — Quality gates
**Description:** Keep the checks of §5.3 green and easy to run.
**Tasks:**
- [ ] ESLint and Prettier configured.
- [ ] `tsc --noEmit` as a script.
- [ ] Vitest configured, with one passing sample test.
- [ ] One command that runs lint, type check and tests.

---

## Theme 2 — Backend Contract

### ⬜ Card 2.1 — Generated API types
**Description:** Generate TypeScript types from the FastAPI OpenAPI schema, so a contract change breaks `tsc` instead of production (§4.3, rule 7).
**Tasks:**
- [ ] Add `openapi-typescript`.
- [ ] Script that reads the backend `/openapi.json` and writes `lib/api-types.ts`.
- [ ] Never edit `api-types.ts` by hand; document the regenerate command.
- [ ] Depends on the backend routes (backend Card 8.3).

### ⬜ Card 2.2 — Typed API client
**Description:** One typed client for all backend calls (`lib/api.ts`).
**Tasks:**
- [ ] `createSession(mode)`.
- [ ] `sendTurn(sessionId, audio)` as multipart upload, returning `user_text`, `reply_text` and `audio_base64`.
- [ ] `finishSession(sessionId)` returning the structured feedback.
- [ ] Map HTTP errors (404, 409, 422, 502) to typed errors the UI can show.
- [ ] Unit tests with a mocked `fetch`.

---

## Theme 3 — Session Start

### ⬜ Card 3.1 — Simulation selector
**Description:** Home page where the user picks the simulation (`app/page.tsx`). v1 has only the Daily Stand-up.
**Tasks:**
- [ ] List the available modes (only Daily Stand-up in v1).
- [ ] Show the other planned simulations as "coming soon" (disabled).
- [ ] Start a session through the API and navigate to `/session/[id]`.
- [ ] Loading and error states.

### ⬜ Card 3.2 — Session page shell
**Description:** Page that holds the whole voice loop (`app/session/[id]/page.tsx`).
**Tasks:**
- [ ] Layout with the transcript, the push-to-talk button and the finish button.
- [ ] Show the Tech Lead opening line returned when the session starts.
- [ ] Handle an unknown or already finished session (404 / 409).

---

## Theme 4 — Voice Capture

### ⬜ Card 4.1 — Recorder hook
**Description:** `features/recorder/useRecorder` wraps the browser `MediaRecorder` API.
**Tasks:**
- [ ] Request microphone permission and handle denial with a clear message.
- [ ] Start and stop recording, returning the audio `Blob`.
- [ ] Pick a supported MIME type (webm/ogg) and expose it for the upload.
- [ ] Release the microphone when the component unmounts.
- [ ] Unit tests with a mocked `MediaRecorder`.

### ⬜ Card 4.2 — Push-to-talk button
**Description:** The main control of the app (§2.1: turn-based, push-to-talk).
**Tasks:**
- [ ] Hold (or toggle) to record, release to send.
- [ ] Visual states: idle, recording, processing, speaking.
- [ ] Disabled while a turn is being processed; while the reply is playing, pressing it stops the playback and starts recording.
- [ ] Keyboard shortcut (space bar) for hands-free use.
- [ ] Ignore very short recordings (accidental clicks).

---

## Theme 5 — Conversation

### ⬜ Card 5.1 — Turn flow
**Description:** Connect recording, API and UI state for one turn.
**Tasks:**
- [ ] Send the recording to `/turns` and wait for the response.
- [ ] Append the user text and the Tech Lead reply to the transcript.
- [ ] On an empty transcription (422), ask the user to record again without adding a turn.
- [ ] On backend failure (502), keep the transcript and allow a retry.

### ⬜ Card 5.2 — Transcript view
**Description:** `features/conversation` shows the conversation so far.
**Tasks:**
- [ ] Messages with a clear distinction between user and Tech Lead.
- [ ] Auto-scroll to the latest message.
- [ ] Show a placeholder while the reply is being generated.
- [ ] Accessible markup (roles and labels for screen readers).

### ⬜ Card 5.3 — Reply audio player
**Description:** Play the Tech Lead reply returned by the TTS **automatically**, with no click needed: the user records, the reply arrives and is spoken right away.
**Tasks:**
- [ ] Decode `audio_base64` (WAV) and start playing as soon as the reply arrives, with no play button in the main flow.
- [ ] Unlock audio playback on the first push-to-talk press, so the browser autoplay policy never blocks the replies.
- [ ] Fallback: if the browser still blocks autoplay, show a "tap to hear the reply" prompt.
- [ ] Block a new recording (or stop the playback) when the user starts talking while the reply is playing.
- [ ] Optional replay button on each Tech Lead message (secondary, not part of the main flow).

---

## Theme 6 — Feedback

### ⬜ Card 6.1 — Finish session
**Description:** End the session and request the structured feedback.
**Tasks:**
- [ ] "Finish" button, disabled until the user has spoken at least once (backend rule).
- [ ] Confirmation before finishing.
- [ ] Loading state while the feedback is generated (this call is slower than a turn).
- [ ] Lock the recorder after the session is finished.

### ⬜ Card 6.2 — Feedback panel
**Description:** `features/feedback` renders `SessionFeedback`.
**Tasks:**
- [ ] Corrections: original → corrected, with the explanation.
- [ ] Better phrasing list.
- [ ] Vocabulary list.
- [ ] Overall comment.
- [ ] Empty states for lists with no items.
- [ ] Option to start a new session.

---

## Theme 7 — UI Foundation

### ⬜ Card 7.1 — Generic components
**Description:** Small reusable pieces in `components/ui`, with no domain knowledge.
**Tasks:**
- [ ] Button, spinner, alert/error message and card.
- [ ] Consistent spacing, typography and colors (light and dark).
- [ ] Responsive layout that works on desktop and phone width.

### ⬜ Card 7.2 — Error and loading states
**Description:** Make every failure understandable, since the stack is made of several local services.
**Tasks:**
- [ ] Backend unreachable: tell the user to start it.
- [ ] Microphone denied: explain how to allow it.
- [ ] Generic fallback error boundary for the session page.

---

## Theme 8 — Quality and Delivery

### ⬜ Card 8.1 — Tests
**Description:** Pragmatic tests for the logic that can break (§5.2).
**Tasks:**
- [ ] Unit tests for the API client and its error mapping.
- [ ] Tests for `useRecorder` and for the turn flow state machine.
- [ ] Component tests for the transcript and the feedback panel.

### ⬜ Card 8.2 — MVP end-to-end check
**Description:** Use the real app with the real backend.
**Tasks:**
- [ ] Run a full Daily Stand-up: record, hear the reply, finish, read the feedback.
- [ ] Test in the browser you will use daily.
- [ ] Write down UX friction and what v2 needs (e.g. streaming, progress tracking).

---

## Suggested order

1. Theme 1 (skeleton and gates).
2. Theme 7.1 (generic UI) and Theme 2 (contract and client). Needs backend Card 8.3 for the real types; until then, a hand-written type can stand in.
3. Theme 3 (start a session) → Theme 4 (voice capture).
4. Theme 5 (conversation) → Theme 6 (feedback).
5. Theme 7.2 and Theme 8 (error states, tests, end-to-end check).
