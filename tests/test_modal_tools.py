"""
Integration smoke tests that hit the Modal LLM endpoint to verify
the model emits ReAct-style tool intent for the available tools.

These tests do not execute tools; they only inspect the LLM output.
They are skipped unless MODAL_ENDPOINT_URL is set.
"""

import os
import httpx
import pytest


ENDPOINT = os.getenv("MODAL_ENDPOINT_URL")


pytestmark = pytest.mark.skipif(
    not ENDPOINT,
    reason="MODAL_ENDPOINT_URL not set; skipping Modal LLM integration tests",
)


def call_modal(messages, max_tokens: int = 300, temperature: float = 0.2) -> str:
    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    response = httpx.post(ENDPOINT, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def test_modal_emits_tool_intent_for_database():
    """Model should mention the database tool when asked to save a contact."""
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente secretarial útil. Tienes herramientas: "
                "client_database, gmail. Usa el formato: "
                "Pregunta/Pensamiento/Acción/Entrada de Acción/Observación/Respuesta Final."
            ),
        },
        {
            "role": "user",
            "content": "Guarda el contacto de Juan Pérez con email juan@example.com",
        },
    ]
    content = call_modal(messages)
    # Accept either explicit tool name or a ReAct-style action section.
    assert "client_database" in content or "Acción" in content


def test_modal_emits_tool_intent_for_gmail():
    """Model should mention the gmail tool when asked to send an email."""
    messages = [
        {
            "role": "system",
            "content": (
                "Eres un asistente secretarial útil. Tienes herramientas: "
                "client_database, gmail. Usa el formato: "
                "Pregunta/Pensamiento/Acción/Entrada de Acción/Observación/Respuesta Final."
            ),
        },
        {
            "role": "user",
            "content": "Envía un email a juan@example.com con asunto Reunión y dile que nos vemos mañana",
        },
    ]
    content = call_modal(messages)
    assert "gmail" in content or "Acción" in content
