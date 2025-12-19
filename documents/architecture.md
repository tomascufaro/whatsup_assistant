# Architecture Overview

## High-Level Diagram

```mermaid
flowchart LR
    subgraph External
        U[WhatsApp User]
        Twilio[Twilio/Meta API]
    end

    subgraph Backend
        FastAPI[FastAPI Webhook\nwhatsapp-assistant-fastapi-app\n(CPU)]
        Agent[Agent (LangGraph)\nChatOpenAI client\nMemoryManager]
        VLLM[vLLM Server\nmistralai/Mistral-7B-Instruct-v0.3\n(H100)]
    end

    subgraph Data
        Vol[Modal Volumes\nHF cache, vLLM cache]
        Mem[In-memory chat history\n(per chat_id)]
    end

    U --> Twilio -->|POST /webhook/whatsapp| FastAPI --> Agent -->|/v1/chat/completions| VLLM
    Agent -->|store/recall| Mem
    VLLM --> Vol
```

## Components
- **FastAPI Webhook (CPU)**: Receives Twilio WhatsApp webhooks, forwards to Agent, returns TwiML.
- **Agent (CPU)**: LangGraph/ChatOpenAI client pointing at the vLLM server; handles memory (in-memory per chat_id).
- **vLLM Server (GPU)**: Modal `@web_server` exposing OpenAI-compatible `/v1/chat/completions`, serving Mistral-7B-Instruct; tools disabled for now.
- **Volumes**: Hugging Face cache and vLLM cache mounted into the GPU app for faster starts.

## Endpoints
- Webhook: `https://tomascufaro--whatsapp-assistant-fastapi-app.modal.run/webhook/whatsapp`
- LLM: `https://tomascufaro--vllm-serve-serve.modal.run/v1` (model: `mistralai/Mistral-7B-Instruct-v0.3`)

## Notes
- Tool calling is disabled client-side; server runs a tool-capable model for future use.
- Memory lives in-process (MemoryManager) keyed by chat_id. No persistent store yet.
- For future tools, enable server flags and reintroduce tools in the Agent.
