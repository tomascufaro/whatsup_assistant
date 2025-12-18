"""
In-memory conversation memory for the WhatsApp assistant.
Stores conversation history per chat_id with configurable turn limits.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from time import time


@dataclass
class MemoryEntry:
    """Single message entry in conversation memory."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float


class MemoryStore:
    """In-memory storage for conversation memories keyed by chat_id."""
    
    def __init__(self):
        self._store: Dict[str, List[MemoryEntry]] = {}
    
    def get(self, chat_id: str) -> List[MemoryEntry]:
        """Get conversation memory for a chat_id."""
        return self._store.get(chat_id, [])
    
    def save(self, chat_id: str, entries: List[MemoryEntry]) -> None:
        """Save conversation memory for a chat_id."""
        self._store[chat_id] = entries
    
    def clear(self, chat_id: str) -> None:
        """Clear conversation memory for a chat_id."""
        if chat_id in self._store:
            del self._store[chat_id]


class MemoryManager:
    """Manages conversation memory with turn limits and context building."""
    
    def __init__(self, max_turns: int = 20):
        """
        Initialize MemoryManager.
        
        Args:
            max_turns: Maximum number of conversation turns to keep (default: 20)
                      A turn is one user message + one assistant response.
        """
        self.store = MemoryStore()
        self.max_turns = max_turns
    
    def build_context(self, chat_id: str) -> List[Dict[str, str]]:
        """
        Build conversation context from memory for a chat_id.
        Returns list of message dicts in format expected by LLM API.
        
        Args:
            chat_id: The chat identifier
            
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        entries = self.store.get(chat_id)
        
        # Convert MemoryEntry objects to message dicts
        messages = [
            {"role": entry.role, "content": entry.content}
            for entry in entries
        ]
        
        return messages
    
    def record_turn(self, chat_id: str, user_content: str, assistant_content: str) -> None:
        """
        Record a conversation turn (user message + assistant response).
        Automatically truncates if over max_turns limit.
        
        Args:
            chat_id: The chat identifier
            user_content: User's message content
            assistant_content: Assistant's response content
        """
        entries = self.store.get(chat_id)
        
        # Create new entries
        user_entry = MemoryEntry(
            role="user",
            content=user_content,
            timestamp=time()
        )
        assistant_entry = MemoryEntry(
            role="assistant",
            content=assistant_content,
            timestamp=time()
        )
        
        # Append new entries
        entries.append(user_entry)
        entries.append(assistant_entry)
        
        # Calculate max entries (max_turns * 2, since each turn has user + assistant)
        max_entries = self.max_turns * 2
        
        # Truncate if over limit (keep most recent)
        if len(entries) > max_entries:
            entries = entries[-max_entries:]
        
        # Save back to store
        self.store.save(chat_id, entries)
    
    def clear(self, chat_id: str) -> None:
        """Clear conversation memory for a chat_id."""
        self.store.clear(chat_id)

