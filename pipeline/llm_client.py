"""Live LLM client for coaching notes (task 60), backed by Groq's
OpenAI-compatible chat completions API over plain httpx -- no vendor SDK.

`groq_llm_client()` returns a callable matching
pipeline/coaching.py::generate_coaching_notes()'s `llm_client` contract
(serialized deltas -> raw response string), or None when GROQ_API_KEY isn't
set, in which case the caller uses the rule-based notes directly. Any error
raised here is caught by generate_coaching_notes() and also falls back.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Callable

import httpx

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_TIMEOUT_SEC = 20.0

# Verbatim from docs/coaching_prompt.md's "System prompt (fixed, verbatim)".
SYSTEM_PROMPT = """You are a football throwing-mechanics coach. You will be given a JSON list of
measured differences ("deltas") between a user's throwing motion and a matched
NFL quarterback's, one delta per biomechanical metric. Each delta has already
been computed by a separate measurement system -- you are not measuring
anything yourself, and you must not state or imply any number that isn't
already present in the input.

For each distinct "phase" value in the input, write exactly one short coaching
sentence (max ~25 words) that:
- names the phase,
- references the specific numeric delta and unit for at least one metric in
  that phase,
- gives one concrete, actionable coaching cue tied to that number.

Do not comment on phases that aren't in the input. Do not rank or score the
user overall -- that's not your job. Do not mention the matched QB's name if
it isn't given to you. Output nothing except the JSON described below.

Output: a JSON array of objects, each with exactly two string keys, "phase"
and "note". No markdown, no code fences, no prose before or after."""


def _strip_code_fences(text: str) -> str:
    """Models sometimes wrap JSON in ```json fences despite being told not to;
    the schema validator downstream would reject that outright."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def groq_llm_client(
    api_key: str | None = None,
    model: str | None = None,
    timeout_sec: float | None = None,
    http_client: httpx.Client | None = None,
) -> Callable[[list[dict]], str] | None:
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    model = model or os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    timeout_sec = timeout_sec or float(os.environ.get("GROQ_TIMEOUT_SEC", DEFAULT_TIMEOUT_SEC))

    def call(deltas_payload: list[dict]) -> str:
        body = {
            "model": model,
            "temperature": 0.3,
            "max_completion_tokens": 1024,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(deltas_payload)},
            ],
        }
        headers = {"Authorization": f"Bearer {api_key}"}
        client = http_client or httpx.Client(timeout=timeout_sec)
        try:
            response = client.post(GROQ_CHAT_URL, json=body, headers=headers)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"] or ""
        except Exception:
            logger.warning("groq coaching call failed; using rule-based notes", exc_info=True)
            raise
        finally:
            if http_client is None:
                client.close()
        return _strip_code_fences(content)

    return call
