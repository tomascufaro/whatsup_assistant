# WhatsApp Assistant - Architecture (MVP)

## System Architecture

```mermaid
graph TB
    subgraph "External Services"
        WA[WhatsApp User]
        TWILIO[Twilio/Meta API]
        MODAL_API[Modal Llama 3.1 8B API]
        GCAL[Google Calendar API]
        GMAIL[Gmail API]
    end

    subgraph "Application Layer - Deployed on Modal"
        WEBHOOK[FastAPI Webhook<br/>/webhook/whatsapp]
        WS[WhatsAppService<br/>services/whatsapp.py]

        subgraph "Agent Layer - Simplified"
            AGENT[Agent<br/>agent/core.py]
            PROMPT[Spanish System Prompts<br/>agent/prompts.py]
        end

        subgraph "Tools - Unused for MVP"
            CALTOOL[CalendarTool<br/>tools/calendar.py]
            EMAILTOOL[EmailTool<br/>tools/email.py]
            DBTOOL[DatabaseTool<br/>tools/database.py]
        end
    end

    subgraph "Data Storage"
        CSV[CSV Database<br/>data/clients.csv]
    end

    subgraph "Modal Cloud"
        MODAL_APP[Modal App<br/>modal.py]
        MODAL_VOL[Modal Volume<br/>data/]
    end

    WA -->|message| TWILIO
    TWILIO -->|webhook| WEBHOOK
    WEBHOOK --> WS
    WS -->|parsed message| AGENT
    AGENT -->|HTTP POST| MODAL_API
    MODAL_API -->|Spanish response| AGENT
    AGENT --> PROMPT
    AGENT -->|response| WS
    WS -->|send message| TWILIO
    TWILIO -->|delivers| WA

    MODAL_APP -.->|deploys| WEBHOOK
    MODAL_VOL -.->|mounts| CSV

    CALTOOL -.->|future| GCAL
    EMAILTOOL -.->|future| GMAIL
    DBTOOL -.->|future| CSV

    style MODAL_API fill:#4CAF50,stroke:#2E7D32,color:#000
    style AGENT fill:#4CAF50,stroke:#2E7D32,color:#000
    style PROMPT fill:#4CAF50,stroke:#2E7D32,color:#000
    style MODAL_APP fill:#2196F3,stroke:#1565C0,color:#000
    style MODAL_VOL fill:#2196F3,stroke:#1565C0,color:#000
    style WEBHOOK fill:#FFC107,stroke:#F57C00,color:#000
    style WS fill:#FFC107,stroke:#F57C00,color:#000
    style CALTOOL fill:#757575,stroke:#424242,color:#fff
    style EMAILTOOL fill:#757575,stroke:#424242,color:#fff
    style DBTOOL fill:#757575,stroke:#424242,color:#fff
    style WA fill:#E1BEE7,stroke:#7B1FA2,color:#000
    style TWILIO fill:#E1BEE7,stroke:#7B1FA2,color:#000
    style GCAL fill:#E1BEE7,stroke:#7B1FA2,color:#000
    style GMAIL fill:#E1BEE7,stroke:#7B1FA2,color:#000
    style CSV fill:#FFCCBC,stroke:#D84315,color:#000
```

**Legend:**
- 🟢 **Green** - New/Modified components (Modal integration)
- 🔵 **Blue** - Modal infrastructure
- 🟡 **Yellow** - FastAPI layer (unchanged)
- ⚫ **Gray** - Tools (kept for future, not used in MVP)
- 🟣 **Purple** - External services
- 🟠 **Orange** - Data storage

---

## Message Flow

```mermaid
sequenceDiagram
    participant User as WhatsApp User
    participant Twilio as Twilio API
    participant FastAPI as FastAPI (Modal)
    participant WhatsAppSvc as WhatsAppService
    participant Agent as Agent
    participant Modal as Modal Llama 8B

    User->>Twilio: Send message in Spanish
    Twilio->>FastAPI: POST /webhook/whatsapp
    FastAPI->>WhatsAppSvc: Parse message
    WhatsAppSvc->>Agent: process_message()
    Agent->>Modal: HTTP POST (prompt + context)
    Modal-->>Agent: Spanish response
    Agent-->>WhatsAppSvc: Return response
    WhatsAppSvc->>Twilio: Send response
    Twilio->>User: Deliver message
```

---

## File Structure

```
whatsup_assistant/
├── modal.py                   # NEW: Modal deployment config
├── requirements.txt           # MODIFY: Remove langchain/openai, add modal
├── architecture.md            # NEW: This file
├── implementation.md          # Plan document
│
└── src/
    ├── main.py               # UNCHANGED: FastAPI app
    │
    ├── agent/
    │   ├── core.py          # REWRITE: Simple Modal API calls
    │   └── prompts.py       # UPDATE: Spanish prompts
    │
    ├── services/
    │   └── whatsapp.py      # UNCHANGED: Message handling
    │
    ├── tools/               # KEEP: Not used in MVP
    │   ├── calendar.py      # (future use)
    │   ├── email.py         # (future use)
    │   └── database.py      # (future use)
    │
    └── data/
        └── clients.csv      # Client database
```

---

## Component Responsibilities

| Component | Responsibility | Change Type |
|-----------|---------------|-------------|
| `modal.py` | Deploy FastAPI to Modal cloud | **NEW** |
| `agent/core.py` | Process messages via Modal API | **REWRITE** |
| `agent/prompts.py` | Spanish system prompts | **UPDATE** |
| `main.py` | FastAPI webhook endpoints | Unchanged |
| `services/whatsapp.py` | Parse/send WhatsApp messages | Unchanged |
| `tools/*.py` | Calendar/Email/DB operations | Keep for future |
| `requirements.txt` | Dependencies | **UPDATE** |

---

## Key Design Decisions

### No LangChain
- Direct HTTP calls to Modal API
- Simpler debugging and maintenance
- Less overhead, faster responses
- More control over behavior

### Llama 3.1 8B
- Cost-effective for MVP testing
- Good Spanish support
- Fast inference times
- Easy upgrade path to 70B

### Stateless Agent
- No conversation memory initially
- Simpler deployment on Modal
- Can add Redis/database later
- Focus on basic flow first

### Keep Existing Tools
- Already implemented
- No overhead if unused
- Easy to integrate later
- Manual tool calling when ready

---

## Implementation Impact

**Minimal Changes Required:**
1. Rewrite `agent/core.py` (~50 lines)
2. Update `agent/prompts.py` (~10 lines)
3. Create `modal.py` (~30 lines)
4. Update `requirements.txt` (~5 lines)

**Total: ~95 lines of code changes**

---

## Next Steps

1. Update `core.py` - Remove LangChain, add Modal API client
2. Update `prompts.py` - Add Spanish system prompt
3. Create `modal.py` - Define Modal app deployment
4. Update `requirements.txt` - Swap dependencies
5. Test locally with Modal API
6. Deploy to Modal
7. Configure WhatsApp webhook
8. Test end-to-end in Spanish

---

*Architecture designed for simplicity and rapid MVP validation.*
