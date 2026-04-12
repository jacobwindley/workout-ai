"""
Base agent wrapper for WorkoutAI.

Wraps Google ADK's Agent + InMemoryRunner into a synchronous interface
suitable for Dash callbacks. Each instance maintains its own in-memory
conversation history via ADK session IDs.
"""

import asyncio
import inspect
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

import config  # noqa: F401 — ensures env vars are set before ADK loads


def _run(coro_or_value):
    """Execute a coroutine synchronously, or return the value if already sync."""
    if inspect.iscoroutine(coro_or_value):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, coro_or_value)
                    return future.result()
            return loop.run_until_complete(coro_or_value)
        except RuntimeError:
            return asyncio.run(coro_or_value)
    return coro_or_value


def _load_prompt(filename: str) -> str:
    prompts_dir = Path(__file__).parent.parent / "prompts"
    return (prompts_dir / filename).read_text(encoding="utf-8").strip()


class WorkoutAgent:
    """Wraps an ADK LlmAgent with a synchronous chat() interface."""

    def __init__(self, name: str, prompt_file: str, tools: list | None = None):
        self.name = name
        self._base_instruction = _load_prompt(prompt_file)
        self._tools = tools or []
        self._runner: InMemoryRunner | None = None

    def _get_runner(self) -> InMemoryRunner:
        if self._runner is None:
            agent = Agent(
                name=self.name,
                model=config.GEMINI_MODEL,
                instruction=self._base_instruction,
                tools=self._tools,
            )
            self._runner = InMemoryRunner(agent=agent)
        return self._runner

    def ensure_session(self, session_id: str, profile_str: str = "") -> None:
        """Create an ADK session with user profile in state if it doesn't exist."""
        runner = self._get_runner()
        svc = runner.session_service
        app_name = runner.app_name
        session = _run(
            svc.get_session(
                app_name=app_name,
                user_id="user",
                session_id=session_id,
            )
        )
        if session is None:
            state = {"user_profile": profile_str} if profile_str else {}
            _run(
                svc.create_session(
                    app_name=app_name,
                    user_id="user",
                    session_id=session_id,
                    state=state,
                )
            )

    def chat(self, message: str, session_id: str, profile_str: str = "") -> str:
        """Send a message and return the agent's text response."""
        self.ensure_session(session_id, profile_str)

        runner = self._get_runner()
        user_msg = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        )

        response_parts: list[str] = []
        for event in runner.run(
            user_id="user",
            session_id=session_id,
            new_message=user_msg,
        ):
            if (
                hasattr(event, "is_final_response")
                and event.is_final_response()
                and event.content
                and event.content.parts
            ):
                response_parts = [
                    p.text for p in event.content.parts if hasattr(p, "text") and p.text
                ]
                break

        return "\n".join(response_parts) if response_parts else "I couldn't generate a response. Please try again."
