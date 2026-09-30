"""Unit tests for pipeline/llm_client.py -- no network, via httpx.MockTransport."""

import json

import httpx

from pipeline.coaching import Delta, generate_coaching_notes
from pipeline.llm_client import GROQ_CHAT_URL, _strip_code_fences, groq_llm_client

DELTAS = [Delta("release", "elbow_angle_deg", 141.4, 144.5, -3.1, "deg")]


def _client_returning(content: str, status: int = 200, seen: list | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(status, json={"choices": [{"message": {"content": content}}]})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_no_api_key_returns_none(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert groq_llm_client() is None


def test_valid_response_is_used_and_request_is_well_formed():
    seen = []
    content = json.dumps([{"phase": "release", "note": "Open your elbow 3.1 deg more at release."}])
    client = groq_llm_client(api_key="k", model="m", http_client=_client_returning(content, seen=seen))
    notes = generate_coaching_notes(DELTAS, client)
    assert notes == [{"phase": "release", "note": "Open your elbow 3.1 deg more at release."}]

    request = seen[0]
    assert str(request.url) == GROQ_CHAT_URL
    assert request.headers["authorization"] == "Bearer k"
    body = json.loads(request.content)
    assert body["model"] == "m"
    assert body["messages"][0]["role"] == "system"
    assert json.loads(body["messages"][1]["content"])[0]["metric_name"] == "elbow_angle_deg"


def test_http_error_falls_back_to_rule_based_notes():
    client = groq_llm_client(api_key="k", http_client=_client_returning("", status=429))
    notes = generate_coaching_notes(DELTAS, client)
    assert notes[0]["phase"] == "release"
    assert "3.10" in notes[0]["note"]  # the rule-based template's formatting


def test_code_fences_are_stripped():
    assert _strip_code_fences('```json\n[{"a": 1}]\n```') == '[{"a": 1}]'
    assert _strip_code_fences('[{"a": 1}]') == '[{"a": 1}]'
