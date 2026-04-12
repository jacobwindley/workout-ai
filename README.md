# WorkoutAI

A single-user fitness assistant with a chat-based web UI, powered by Google Gemini and built with Dash.

## Features

- **Profile** — onboarding chat that captures your fitness goals, experience, and preferences
- **Workout** — personalised workout recommendations
- **Consistency** — habit tracking and accountability coaching
- **Diet** — nutrition guidance tailored to your profile

## Tech Stack

- [Dash](https://dash.plotly.com/) + [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/) — web UI
- [Google ADK](https://google.github.io/adk-docs/) — agent framework
- [Google Gemini](https://ai.google.dev/) (`gemini-2.0-flash` by default) — LLM backend
- SQLite — local storage for user profile and workout log

## Setup

**Requirements:** Python 3.14+

1. Clone the repo and install dependencies:
   ```bash
   pip install uv
   uv sync
   ```

2. Copy `.env.example` to `.env` and add your Google AI Studio API key:
   ```bash
   cp .env.example .env
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Open [http://localhost:8050](http://localhost:8050) in your browser.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `GOOGLE_API_KEY` | — | Required. Get one at [aistudio.google.com](https://aistudio.google.com) |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `DB_PATH` | `workout.db` | Path to the SQLite database file |
