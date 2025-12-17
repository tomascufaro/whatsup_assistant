"""
Core agent logic for processing messages via Modal API.
"""

import os
import httpx
from typing import Dict, Any

from agent.prompts import get_system_prompt


class Agent:
    """Main agent that processes messages using Modal's Qwen model."""

    def __init__(self):
        self.modal_endpoint = os.getenv("MODAL_ENDPOINT_URL")
        self.modal_token = os.getenv("MODAL_TOKEN")
        self.system_prompt = get_system_prompt()

        print(f"Agent initialized with endpoint: {self.modal_endpoint}")

        if not self.modal_endpoint:
            raise ValueError("MODAL_ENDPOINT_URL environment variable not set")

    async def process_message(self, message: Dict[str, Any]) -> str:
        """Process incoming message and return response."""
        user_message = message.get("body", "")
        print(f"Processing message: {user_message}")

        try:
            response = await self._call_modal_api(user_message)
            print(f"Got response: {response}")
            return response
        except Exception as e:
            error_msg = f"Lo siento, hubo un error: {str(e)}"
            print(f"ERROR in process_message: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg

    async def _call_modal_api(self, user_message: str) -> str:
        """Make HTTP request to Modal's Qwen API endpoint."""
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

        print(f"Calling Modal endpoint: {self.modal_endpoint}")

        # Long timeout for cold starts (GPU + model loading can take 60s+)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.modal_endpoint,
                json=payload,
                headers=headers,
            )

            print(f"Modal response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"Modal response: {result}")

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        elif "response" in result:
            return result["response"]
        else:
            return result.get("content", "No response from model")
