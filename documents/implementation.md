# Implementation Plan: Modal Integration & Spanish Support (MVP)

## Overview

Simple plan to:
- Replace OpenAI/LangChain with direct Modal API calls
- Use smaller model (Llama 3.1 8B) for cost-efficiency
- Add Spanish language support
- Deploy existing FastAPI app to Modal

**Key Principle**: Minimal changes. Remove LangChain, use Modal API directly, keep it simple.

---

## Model Selection

**Chosen Model**: Llama 3.1 8B via Modal
- Good Spanish support
- Very cost-effective for MVP
- Fast responses
- Sufficient for secretary/assistant tasks
- Can upgrade to 70B later if needed

---

## Implementation Steps

### Step 1: Remove LangChain, Use Modal API Directly

**File**: `src/agent/core.py`

Complete rewrite to:
- Remove all LangChain dependencies (agents, chains, memory)
- Make direct API calls to Modal's Llama 3.1 8B endpoint
- Simple structure: receive message → call Modal API → return response
- Manual tool calling logic (if needed later)
- Keep it minimal for MVP

### Step 2: Add Spanish Language Support

**File**: `src/agent/prompts.py`

Update system prompt to:
- Emphasize Spanish communication
- Keep assistant persona and capabilities
- Ensure natural Spanish responses

### Step 3: Deploy to Modal

**File**: `modal.py` (new, root level)

Create Modal app that:
- Defines image with dependencies from `requirements.txt`
- Deploys existing FastAPI app from `src/main.py`
- Exposes webhook endpoint
- Mounts `data/` volume if needed

### Step 4: Update Dependencies

**File**: `requirements.txt`

- Add `modal`
- Remove `langchain` and `openai`
- Keep FastAPI, Twilio, and tool-specific dependencies
- Minimal dependencies for MVP

---

## File Changes Summary

```
├── modal.py                    # NEW: Deploy FastAPI to Modal
├── requirements.txt            # MODIFY: Remove langchain/openai, add modal
└── src/
    ├── main.py                 # UNCHANGED: Works as-is
    ├── agent/
    │   ├── core.py             # REWRITE: Remove LangChain, direct Modal API
    │   └── prompts.py          # MODIFY: Add Spanish instructions
    └── ...                     # UNCHANGED: Tools stay the same
```

**No LangChain. No complex abstractions. Just FastAPI + Modal API calls.**

---

## Testing Approach

**Local**:
- Run FastAPI locally with `uvicorn src.main:app`
- Test via `/health` and `/webhook/whatsapp` endpoints
- Verify Spanish responses

**Production**:
- Deploy with `modal deploy modal.py`
- Configure WhatsApp webhook to Modal URL
- Test with real messages

---

## Technical Details

### Modal LLM Integration
- Direct HTTP requests to Modal's hosted Llama 3.1 8B endpoint
- Simple POST request with prompt, get response
- No LangChain complexity
- Lightweight and fast

### Spanish Support
- Add to system prompt: "Respond in Spanish" / "Responde en español"
- Test with common business phrases
- Tools already handle text in any language

### Modal Deployment
- Modal wraps existing FastAPI app
- No changes to app code required
- Environment variables passed via Modal secrets

---

## Why This Is Simpler

**What we're NOT doing**:
- ❌ No LangChain - Too heavy for MVP
- ❌ No `model_client.py` - Direct API calls
- ❌ No `modal_app.py` - Modal deploys existing `main.py`
- ❌ No `test_agent_model.py` - Test through FastAPI endpoints
- ❌ No tool calling initially - Add later if needed
- ❌ No 70B model - Start with lightweight 8B

**What we ARE doing**:
- ✅ Rewrite `core.py` to use direct Modal API calls (simple HTTP)
- ✅ Update prompt in `prompts.py` for Spanish
- ✅ Create one `modal.py` to deploy everything
- ✅ Remove LangChain, use Llama 3.1 8B
- ✅ Keep it minimal and fast

---

## Next Actions

1. Update `core.py` with Modal LLM configuration
2. Update `prompts.py` with Spanish instructions
3. Create `modal.py` deployment file
4. Test locally, then deploy

---

*MVP approach: Minimal changes, maximum results.*
