"""
Core agent logic for processing messages via Modal API.
"""

import os
import requests
from typing import Dict, Any

from agent.prompts import get_system_prompt


class Agent:
    """Main agent that processes messages using Modal's Llama 3.1 8B."""

    def __init__(self):
        self.modal_endpoint = os.getenv("MODAL_ENDPOINT_URL")
        self.modal_token = os.getenv("MODAL_TOKEN")
        self.system_prompt = get_system_prompt()

        if not self.modal_endpoint:
            raise ValueError("MODAL_ENDPOINT_URL environment variable not set")

    async def process_message(self, message: Dict[str, Any]) -> str:
        """Process incoming message and return response."""
        user_message = message.get("body", "")

        try:
            response = await self._call_modal_api(user_message)
            return response
        except Exception as e:
            return f"Lo siento, hubo un error al procesar tu mensaje: {str(e)}"

    async def _call_modal_api(self, user_message: str) -> str:
        """Make HTTP request to Modal's Llama API endpoint."""
        headers = {
            "Content-Type": "application/json",
        }

        if self.modal_token:
            headers["Authorization"] = f"Bearer {self.modal_token}"

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }

        response = requests.post(
            self.modal_endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        # Extract response based on Modal's response format
        # Adjust this based on actual Modal API response structure
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        elif "response" in result:
            return result["response"]
        else:
            return result.get("content", "No response from model")
