"""
Core agent logic for processing messages via ReAct agent with LangChain.
"""

import os
from typing import Dict, Any, Optional
import logging
import time

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.prompts import get_system_prompt
from agent.memory import MemoryManager
from tools.database import DatabaseTool
from tools.email import EmailTool
from logging_setup import set_request_id


class Agent:
    """Main agent that processes messages using ReAct agent with Modal's Qwen model."""

    def __init__(self, max_turns: int = 20):
        """
        Initialize Agent with ReAct executor.
        
        Args:
            max_turns: Maximum number of conversation turns to keep in memory (default: 20)
        """
        self.modal_endpoint = os.getenv("MODAL_ENDPOINT_URL")
        self.modal_token = os.getenv("MODAL_TOKEN")
        self.memory_manager = MemoryManager(max_turns=max_turns)
        self.system_prompt = get_system_prompt()

        if not self.modal_endpoint:
            raise ValueError("MODAL_ENDPOINT_URL environment variable not set")

        # Initialize LLM (ChatOpenAI points to Modal endpoint)
        # Remove /generate_endpoint from URL if present
        base_url = self.modal_endpoint.rsplit('/', 1)[0] if '/' in self.modal_endpoint else self.modal_endpoint
        
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key=self.modal_token or "dummy",
            model="qwen",
            temperature=0.7,
            max_tokens=500,
        )

        # Load tools
        self.tools = [DatabaseTool(), EmailTool()]

        # Create ReAct agent with LangGraph
        # Note: LangGraph's create_react_agent uses default ReAct prompt
        self.agent_executor = create_react_agent(self.llm, self.tools)

        print(f"Agent initialized with {len(self.tools)} tools: {[t.name for t in self.tools]}")

    async def process_message(self, message: Dict[str, Any], chat_id: Optional[str] = None, request_id: Optional[str] = None) -> str:
        """
        Process message using ReAct agent.
        
        Args:
            message: Message dict with 'body' key containing user message
            chat_id: Optional chat identifier for memory (defaults to None)
            request_id: Correlation identifier for logging
            
        Returns:
            Assistant response string
        """
        log = logging.getLogger("agent")
        user_message = message.get("body", "").strip()
        set_request_id(request_id)
        start = time.time()

        log.info("agent_invoke_start", extra={
            "stage": "agent_invoke_start",
            "request_id": request_id,
            "chat_id": chat_id,
            "user_preview": user_message[:200],
        })

        # Handle /reset command
        if user_message.lower() == "/reset":
            if chat_id:
                self.memory_manager.clear(chat_id)
            return "Memoria de conversación borrada. Empezamos de nuevo."

        if not user_message:
            return "Lo siento, no recibí ningún mensaje."

        try:
            # Build context from memory
            context_messages = self.memory_manager.build_context(chat_id) if chat_id else []

            # Format context as conversational history for the messages
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
            
            messages = [SystemMessage(content=self.system_prompt)]
            
            # Add conversation history
            for msg in context_messages:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            
            # Add current user message
            messages.append(HumanMessage(content=user_message))

            # Call agent executor
            result = await self.agent_executor.ainvoke({"messages": messages})

            # Extract response from last AI message
            response = result["messages"][-1].content
            log.info("agent_invoke_end", extra={
                "stage": "agent_invoke_end",
                "request_id": request_id,
                "chat_id": chat_id,
                "history_len": len(context_messages),
                "duration_ms": int((time.time() - start) * 1000),
                "response_preview": response[:200],
            })

            # Record turn in memory
            if chat_id:
                self.memory_manager.record_turn(chat_id, user_message, response)

            return response

        except Exception as e:
            error_msg = f"Lo siento, hubo un error: {str(e)}"
            log.error("agent_invoke_error", extra={
                "stage": "agent_invoke_error",
                "request_id": request_id,
                "chat_id": chat_id,
                "error": str(e),
            })
            import traceback
            traceback.print_exc()
            return error_msg
