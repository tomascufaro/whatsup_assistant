"""
Core agent logic for processing messages and orchestrating tools.
"""

import os
from typing import Dict, Any
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from agent.prompts import get_system_prompt
from tools.calendar import CalendarTool
from tools.email import EmailTool
from tools.database import DatabaseTool


class Agent:
    """Main agent that processes messages and uses tools."""
    
    def __init__(self):
        self.llm = OpenAI(
            temperature=0.7,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize tools
        self.tools = [
            CalendarTool(),
            EmailTool(),
            DatabaseTool(),
        ]
        
        # Initialize agent with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            agent_kwargs={
                "system_message": get_system_prompt()
            }
        )
    
    async def process_message(self, message: Dict[str, Any]) -> str:
        """Process incoming message and return response."""
        user_message = message.get("body", "")
        response = self.agent.run(input=user_message)
        return response

