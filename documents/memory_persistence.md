Memory Persistence Implementation

Problem
- Conversation history stored in in-memory dict is lost on container restarts
- Multi-turn conversations lose context between requests

Solution
- Use Modal Volume for persistent file-based storage
- Store each chat_id as a JSON file on the volume
- Keep in-memory as fallback when volume not available
- Maintain MemoryManager interface unchanged

Implementation

1. Update modal_fastapi.py

   Add volume creation after app definition:
   volume = modal.Volume.from_name("memory-storage", create_if_missing=True)

   Update @app.function decorator to mount volume:
   @app.function(
       image=image,
       secrets=[modal.Secret.from_name("whatsapp-secrets")],
       volumes={"/data/memory": volume},
       timeout=180,
   )

2. Update MemoryStore class in src/agent/memory.py

   Import at top:
   import json
   import re
   from pathlib import Path
   from typing import Dict, List

   Add helper function for filename sanitization:
   def _sanitize_filename(chat_id: str) -> str:
       """Sanitize chat_id for use as filename."""
       # Replace invalid characters with underscore
       sanitized = re.sub(r'[<>:"/\\|?*]', '_', chat_id)
       # Limit length to avoid filesystem issues
       return sanitized[:200] if len(sanitized) > 200 else sanitized

   Add class constants:
   VOLUME_PATH = Path("/data/memory")
   FALLBACK_PATH = Path("data/memory")

   Modify __init__:
   def __init__(self):
       self._store: Dict[str, List[MemoryEntry]] = {}  # In-memory cache
       
       # Check if Modal volume is mounted
       if VOLUME_PATH.exists():
           self._storage_path = VOLUME_PATH
           self._use_volume = True
           # Ensure directory exists
           self._storage_path.mkdir(parents=True, exist_ok=True)
       else:
           # Fallback to local directory
           self._storage_path = FALLBACK_PATH
           self._storage_path.mkdir(parents=True, exist_ok=True)
           self._use_volume = False

   Update get():
   def get(self, chat_id: str) -> List[MemoryEntry]:
       if self._use_volume:
           # Check cache first for performance
           if chat_id in self._store:
               return self._store[chat_id]
           
           # Load from disk
           file_path = self._storage_path / f"{_sanitize_filename(chat_id)}.json"
           if not file_path.exists():
               return []
           
           try:
               with open(file_path, 'r', encoding='utf-8') as f:
                   entries_dict = json.load(f)
               entries = [MemoryEntry(**entry) for entry in entries_dict]
               self._store[chat_id] = entries  # Cache it
               return entries
           except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
               print(f"Error loading memory for {chat_id}: {e}")
               return []
       
       return self._store.get(chat_id, [])

   Update save():
   def save(self, chat_id: str, entries: List[MemoryEntry]) -> None:
       # Update cache
       self._store[chat_id] = entries
       
       if self._use_volume:
           file_path = self._storage_path / f"{_sanitize_filename(chat_id)}.json"
           entries_dict = [
               {"role": e.role, "content": e.content, "timestamp": e.timestamp}
               for e in entries
           ]
           
           try:
               # Write atomically using temp file + rename
               temp_path = file_path.with_suffix('.json.tmp')
               with open(temp_path, 'w', encoding='utf-8') as f:
                   json.dump(entries_dict, f, indent=2)
               temp_path.replace(file_path)  # Atomic rename
               
               # Note: Modal volumes auto-commit on function exit
               # No explicit commit needed
           except OSError as e:
               print(f"Error saving memory for {chat_id}: {e}")
               # Remove from cache if write failed
               if chat_id in self._store:
                   del self._store[chat_id]
       else:
           self._store[chat_id] = entries

   Update clear():
   def clear(self, chat_id: str) -> None:
       if self._use_volume:
           file_path = self._storage_path / f"{_sanitize_filename(chat_id)}.json"
           if file_path.exists():
               try:
                   file_path.unlink()
               except OSError as e:
                   print(f"Error clearing memory for {chat_id}: {e}")
           
           # Clear from cache
           if chat_id in self._store:
               del self._store[chat_id]
       elif chat_id in self._store:
           del self._store[chat_id]

3. Verify chat_id is passed in src/main.py
   Line 39: chat_id = from_number if from_number else None
   Line 42: await agent.process_message({"body": body}, chat_id=chat_id)
   Both are correct, no changes needed.

Testing
- Unit: Test MemoryManager with volume mounted and unmounted
- Unit: Test filename sanitization with special characters (e.g., "whatsapp:+1234567890")
- Unit: Test in-memory cache (verify second get() doesn't hit disk)
- Integration: Send two messages with same chat_id, restart container, verify second message has context
- Integration: Verify atomic writes (no corrupted files on concurrent access)
- Verify files are created in /data/memory/ directory with sanitized names

Notes
- Modal Volume persists across container restarts
- Each chat_id gets its own JSON file: {sanitized_chat_id}.json
- Modal volumes auto-commit on function exit (no explicit commit needed)
- In-memory cache reduces disk I/O for frequently accessed conversations
- Atomic writes (temp file + rename) prevent corruption on concurrent access
- Filename sanitization handles special characters in chat_id (e.g., phone numbers with colons)
- Specific error handling for better debugging (FileNotFoundError, JSONDecodeError, OSError)
