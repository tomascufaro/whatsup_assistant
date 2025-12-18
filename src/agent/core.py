"""
Core agent logic for processing messages via Modal API.
"""

import os
import httpx
from typing import Dict, Any, Optional

from agent.prompts import get_system_prompt
from agent.memory import MemoryManager


class Agent:
    """Main agent that processes messages using Modal's Qwen model."""

    def __init__(self, max_turns: int = 20):
        """
        Initialize Agent.
        
        Args:
            max_turns: Maximum number of conversation turns to keep in memory (default: 20)
        """
        self.modal_endpoint = os.getenv("MODAL_ENDPOINT_URL")
        self.modal_token = os.getenv("MODAL_TOKEN")
        self.system_prompt = get_system_prompt()
        self.memory_manager = MemoryManager(max_turns=max_turns)

        print(f"Agent initialized with endpoint: {self.modal_endpoint}")

        if not self.modal_endpoint:
            raise ValueError("MODAL_ENDPOINT_URL environment variable not set")

    async def process_message(self, message: Dict[str, Any], chat_id: Optional[str] = None) -> str:
        """
        Process incoming message and return response.
        
        Args:
            message: Message dict with 'body' key containing user message
            chat_id: Optional chat identifier for memory (defaults to None)
            
        Returns:
            Assistant response string
        """
        user_message = message.get("body", "").strip()
        print(f"Processing message: {user_message} (chat_id: {chat_id})")

        # Handle /reset command
        if user_message.lower() == "/reset":
            if chat_id:
                self.memory_manager.clear(chat_id)
                return "Memoria de conversación borrada. Empezamos de nuevo."
            else:
                return "Memoria de conversación borrada. Empezamos de nuevo."

        if not user_message:
            return "Lo siento, no recibí ningún mensaje."

        try:
            # Build context with memory
            context_messages = self.memory_manager.build_context(chat_id) if chat_id else []
            
            # Call Modal API with context
            response = await self._call_modal_api(user_message, context_messages)
            print(f"Got response: {response}")
            
            # Record turn in memory
            if chat_id:
                self.memory_manager.record_turn(chat_id, user_message, response)
            
            return response
        except Exception as e:
            error_msg = f"Lo siento, hubo un error: {str(e)}"
            print(f"ERROR in process_message: {error_msg}")
            import traceback
            traceback.print_exc()
            return error_msg

    async def _call_modal_api(self, user_message: str, context_messages: list = None) -> str:
        """
        Make HTTP request to Modal's Qwen API endpoint.
        
        Args:
            user_message: Current user message
            context_messages: List of previous conversation messages (optional)
        """
        headers = {
            "Content-Type": "application/json",
        }

        if self.modal_token:
            headers["Authorization"] = f"Bearer {self.modal_token}"

        # Build messages list: system prompt + context + current user message
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add context messages if available
        if context_messages:
            messages.extend(context_messages)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})

        payload = {
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }

        print(f"Calling Modal endpoint: {self.modal_endpoint}")
        print(f"Message count: {len(messages)} (1 system + {len(context_messages) if context_messages else 0} context + 1 user)")

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
