# Implementation: LangChain ReAct Agent for Tool Calling

## Goal
Enable WhatsApp agent to automatically trigger tools (database, email) using LangChain's ReAct agent with Modal/Qwen2.5-7B model.

## Prerequisites
- Modal endpoint at `MODAL_ENDPOINT_URL` (returns OpenAI-compatible format)
- Existing tools: `DatabaseTool`, `EmailTool` (LangChain-compatible)
- Existing memory: `MemoryManager` in `src/agent/memory.py`
- Python 3.11+

## Implementation Steps

### Step 1: Update Modal Model to Qwen2.5-7B

**File**: `modal_llm_app.py`

**Changes**:
```python
# Line 17: Change model
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"  # Was: Qwen2.5-3B-Instruct

# Line 18: Keep GPU config (A10G works for 7B)
GPU_CONFIG = "A10G"
```

**Deploy**:
```bash
modal deploy modal_llm_app.py
```

### Step 2: Install Dependencies

```bash
pip install langchain-openai langchainhub langchain
```

**Update** `requirements.txt`:
```text
langchain==0.1.0
langchain-openai==0.1.0
langchainhub==0.1.14
```

### Step 3: Create ReAct Prompt (Spanish)

**File**: `src/agent/prompts.py`

**Add function** `get_react_prompt()`:

```python
from langchain.prompts import PromptTemplate

def get_react_prompt():
    """ReAct prompt template in Spanish for tool calling."""
    template = """Eres un asistente secretarial útil para un negocio.

Tienes acceso a las siguientes herramientas:

{tools}

Usa el siguiente formato:

Pregunta: la pregunta o tarea del usuario
Pensamiento: siempre debes pensar qué hacer
Acción: la acción a tomar, debe ser una de [{tool_names}]
Entrada de Acción: la entrada para la acción
Observación: el resultado de la acción
... (este proceso Pensamiento/Acción/Entrada de Acción/Observación puede repetirse N veces)
Pensamiento: Ahora sé la respuesta final
Respuesta Final: la respuesta final al usuario en español

Comienza!

Historial de conversación:
{chat_history}

Pregunta: {input}
Pensamiento: {agent_scratchpad}"""

    return PromptTemplate(
        template=template,
        input_variables=["input", "chat_history", "agent_scratchpad", "tools", "tool_names"]
    )
```

**Keep** existing `get_system_prompt()` as-is.

### Step 4: Update Agent Core

**File**: `src/agent/core.py`

**Replace imports**:
```python
import os
import httpx
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.schema import OutputParserException

from agent.prompts import get_react_prompt
from agent.memory import MemoryManager
from tools.database import DatabaseTool
from tools.email import EmailTool
```

**Replace `Agent.__init__()`**:
```python
def __init__(self, max_turns: int = 20):
    """Initialize Agent with ReAct executor."""
    self.modal_endpoint = os.getenv("MODAL_ENDPOINT_URL")
    self.modal_token = os.getenv("MODAL_TOKEN")
    self.memory_manager = MemoryManager(max_turns=max_turns)

    if not self.modal_endpoint:
        raise ValueError("MODAL_ENDPOINT_URL environment variable not set")

    # Initialize LLM (ChatOpenAI points to Modal endpoint)
    base_url = self.modal_endpoint.rsplit('/', 1)[0]  # Remove /generate_endpoint
    self.llm = ChatOpenAI(
        base_url=base_url,
        api_key=self.modal_token or "dummy",
        model="qwen",
        temperature=0.7,
        max_tokens=500,
    )

    # Load tools
    self.tools = [DatabaseTool(), EmailTool()]

    # Create ReAct agent
    prompt = get_react_prompt()
    agent = create_react_agent(self.llm, self.tools, prompt)

    # Wrap in executor
    self.agent_executor = AgentExecutor(
        agent=agent,
        tools=self.tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )

    print(f"Agent initialized with {len(self.tools)} tools: {[t.name for t in self.tools]}")
```

**Replace `Agent.process_message()`**:
```python
async def process_message(self, message: Dict[str, Any], chat_id: Optional[str] = None) -> str:
    """Process message using ReAct agent."""
    user_message = message.get("body", "").strip()
    print(f"Processing message: {user_message} (chat_id: {chat_id})")

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

        # Format context as string
        chat_history = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in context_messages
        ]) if context_messages else "No hay historial previo."

        # Call agent executor
        result = await self.agent_executor.ainvoke({
            "input": user_message,
            "chat_history": chat_history
        })

        response = result["output"]
        print(f"Agent response: {response}")

        # Record turn in memory
        if chat_id:
            self.memory_manager.record_turn(chat_id, user_message, response)

        return response

    except OutputParserException as e:
        error_msg = f"Error procesando respuesta: {str(e)}"
        print(f"OutputParserException: {error_msg}")
        return "Lo siento, tuve un problema procesando la respuesta. ¿Puedes reformular tu pregunta?"

    except Exception as e:
        error_msg = f"Lo siento, hubo un error: {str(e)}"
        print(f"ERROR in process_message: {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg
```

**Remove** `_call_modal_api()` method (no longer needed).

### Step 5: Verify Tool Compatibility

**Files**: `src/tools/database.py`, `src/tools/email.py`

**Check** both files have:
- Class extends `BaseTool`
- `name` attribute defined
- `description` attribute in Spanish
- `args_schema` defined
- `_run()` method implemented

**No changes needed** if already LangChain-compatible.

### Step 6: Test Implementation

**Test Phase 1: Basic Tool Call**
```bash
# Start your application
python src/main.py

# Send test message
"Guarda el contacto de María, email maria@test.com"

# Check verbose logs for:
# - Pensamiento: ... (agent reasoning)
# - Acción: client_database (tool selection)
# - Observación: ... (tool result)
# - Respuesta Final: ... (final response)
```

**Test Phase 2: Multiple Scenarios**
```python
# Test cases
test_cases = [
    "Guarda los datos de Juan Pérez, email juan@example.com",  # Add client
    "Envía un email a juan@example.com con asunto 'Reunión'",  # Send email
    "Hola, ¿cómo estás?",  # No tool needed
]
```

**Test Phase 3: Memory**
```python
# Multi-turn conversation
Turn 1: "Guarda a Juan con email juan@example.com"
Turn 2: "¿Qué datos guardé?"  # Should remember Juan
```

**Expected**: Agent should call tools correctly and respond in Spanish.

## Verification Checklist

- [ ] Modal deployed with Qwen2.5-7B
- [ ] Dependencies installed (`langchain-openai`, `langchainhub`)
- [ ] `get_react_prompt()` added to `prompts.py`
- [ ] `core.py` updated with ReAct agent
- [ ] Agent initializes without errors
- [ ] Test Phase 1 passes (single tool call)
- [ ] Test Phase 2 passes (all scenarios)
- [ ] Test Phase 3 passes (memory integration)
- [ ] Verbose logs show Pensamiento/Acción/Observación cycles

## Configuration

Environment variables:
- `MODAL_ENDPOINT_URL`: Modal endpoint (e.g., `https://your-app.modal.run/generate_endpoint`)
- `MODAL_TOKEN`: Optional auth token
- CSV path: `data/clients.csv`
- Gmail OAuth: `credentials.json` + `gmail_token.pickle`

## Troubleshooting

**Issue**: Agent doesn't call tools
- Check verbose logs for "Acción:" lines
- Verify tool descriptions are in Spanish
- Model may need better examples in prompt

**Issue**: `OutputParserException`
- Agent output doesn't match ReAct format
- Handled with `handle_parsing_errors=True`
- Returns fallback message to user

**Issue**: Agent loops without finishing
- Hits `max_iterations=10` limit
- Check if tool results are clear
- May need to improve tool descriptions

**Issue**: Memory not working
- Verify `chat_id` is passed consistently
- Check `MemoryManager.build_context()` returns messages
- Ensure context formatted correctly as string
