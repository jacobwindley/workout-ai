# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
python app.py
```

Starts the Dash web server at http://localhost:8050 with debug mode enabled. Requires a `.env` file with `GOOGLE_API_KEY` set (see `.env.example`).

No build, lint, or test infrastructure is currently set up.

## Architecture

WorkoutAI is a single-user fitness assistant with a Dash web UI backed by Google Gemini (via ADK) and SQLite.

### Layer Overview

- **`app.py`** — Dash app entry point. Defines four chat tabs (Profile, Workout, Consistency, Diet), manages in-memory session/chat-history state, routes messages to the correct agent, and reloads profile after onboarding saves it.
- **`agents/`** — Agent implementations. `base.py` provides `WorkoutAgent`, a synchronous wrapper around Google ADK's async `Agent` + `InMemoryRunner`. Each of the four agent files instantiates a `WorkoutAgent` with a name, prompt file, and optional tools.
- **`db/database.py`** — SQLite helpers. Two tables: `user_profile` (single row, id=1) and `workout_log`. Key functions: `init_db`, `get_profile`, `save_profile`, `format_profile`, `get_workouts`, `add_workout`.
- **`prompts/`** — Plain-text system prompts, one per agent. Each contains a `{user_profile}` placeholder filled at session creation time.
- **`config.py`** — Loads `.env`, sets `GOOGLE_API_KEY`, `GEMINI_MODEL` (default `gemini-2.0-flash`), `DB_PATH`, and forces `GOOGLE_GENAI_USE_VERTEXAI=FALSE`.

### Agent Lifecycle

1. `WorkoutAgent.chat(message, session_id, profile)` is called from `app.py`.
2. On first call for a session, `ensure_session()` creates an ADK session and injects the formatted profile string into session state.
3. `_run()` executes ADK's async runner synchronously, handling cases where an event loop is already running.
4. The only agent with a registered tool is **onboarding**: its `save_profile()` tool writes collected profile fields to SQLite.

### Profile Gating

Non-onboarding tabs check `onboarding_complete` on the profile before passing messages to their agents. If the profile is incomplete, the UI returns a prompt to finish onboarding first.
