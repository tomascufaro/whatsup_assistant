# Implementation Plan: Base Agent with Modal Integration & Spanish Support

## Overview

This document outlines the step-by-step plan to create a base agent that:
- Uses Modal-hosted models (not OpenAI)
- Supports Spanish language for Spanish-speaking clients
- Can be tested locally (simple model testing)
- Runs in production on Modal cloud infrastructure

---

## Phase 1: Model Selection for Spanish (Modal-hosted)

**Goal**: Choose a Modal-hosted model that works well with Spanish.

**Modal Model Options**:
1. **Llama 3.1 70B** - Excellent Spanish support, cost-effective
2. **Mistral Large** - Strong Spanish, good reasoning capabilities
3. **Mixtral 8x7B** - Fast responses, good Spanish support

**Recommendation**: Start with **Llama 3.1 70B** via Modal for best balance of cost and Spanish language quality.

**Action Items**:
- Update `src/agent/core.py` to use Modal's model serving
- Add Spanish-specific instructions to `src/agent/prompts.py`
- Create simple local test script (no Modal infrastructure, just model logic)

---

## Phase 2: Refactor Agent for Modal Model Integration

**Goal**: Replace OpenAI dependency with Modal's model serving.

**Changes Needed**:

1. **Update `src/agent/core.py`**
   - Remove OpenAI/LangChain OpenAI dependency
   - Add Modal model client integration
   - Keep existing agent interface
   - Make model selection configurable

2. **Update `src/agent/prompts.py`**
   - Add Spanish language instructions
   - Ensure prompts work well with chosen model

3. **Create `src/agent/model_client.py`** (new file)
   - Abstract model client interface
   - Modal model integration
   - Simple interface for agent to use

---

## Phase 3: Simple Local Model Testing

**Goal**: Test model responses locally without Modal infrastructure.

**Create**:

1. **`src/test_agent_model.py`** (new file)
   - Simple script to test agent with Spanish inputs
   - Uses Modal model client directly
   - No webhooks, no WhatsApp dependencies
   - Just: input text → model → output text

**Note**: This will still call Modal's API, but it's a simple script to verify the model works with Spanish.

---

## Phase 4: Modal App Setup

**Goal**: Set up Modal infrastructure for deployment.

**Files to Create**:

1. **`modal.py`** (root)
   - Modal app definition
   - Image definition with dependencies
   - Volume mounts for `data/`
   - Model endpoint definition

2. **`src/modal_app.py`** (new file)
   - Modal webhook function
   - Agent initialization in Modal context
   - WhatsApp webhook handler

3. **Update `requirements.txt`**
   - Add `modal` package
   - Remove `openai` (or keep for compatibility if needed)
   - Update LangChain if needed for Modal integration

---

## Phase 5: Update Main Application

**Goal**: Keep local FastAPI for development, Modal for production.

**Update `src/main.py`**:
- Keep existing FastAPI structure
- Update to use Modal model client instead of OpenAI
- Can run locally for development/testing

---

## Detailed File Structure Changes

```
├── modal.py                    # NEW: Modal app definition
├── src/
│   ├── main.py                 # MODIFY: Use Modal model instead of OpenAI
│   ├── modal_app.py            # NEW: Modal webhook functions
│   ├── agent/
│   │   ├── core.py             # MODIFY: Replace OpenAI with Modal model
│   │   ├── model_client.py     # NEW: Modal model client wrapper
│   │   └── prompts.py          # MODIFY: Add Spanish instructions
│   └── test_agent_model.py     # NEW: Simple model testing script
└── requirements.txt            # MODIFY: Add modal, remove/update openai
```

---

## Implementation Order (Step-by-Step)

### Step 1: Model Client Abstraction
- Create `src/agent/model_client.py`
- Implement Modal model client (Llama 3.1 70B)
- Simple interface: `generate(prompt: str) -> str`

### Step 2: Update Agent Core
- Modify `src/agent/core.py` to use Modal model client
- Remove OpenAI dependency
- Keep existing agent interface and tool integration

### Step 3: Spanish Prompts
- Update `src/agent/prompts.py` with Spanish instructions
- Test prompt structure

### Step 4: Simple Local Model Test
- Create `src/test_agent_model.py`
- Test agent with Spanish inputs
- Verify model responses (calls Modal API, but simple script)

### Step 5: Modal App Setup
- Add `modal` to requirements.txt
- Create `modal.py` with app definition
- Create `src/modal_app.py` with webhook function

### Step 6: Update Main App
- Update `src/main.py` to use Modal model
- Keep FastAPI structure for local development

### Step 7: Deploy to Modal
- Deploy Modal app
- Configure webhook URL
- Test with WhatsApp messages

---

## Key Technical Details

### Modal Model Integration
- Use Modal's `modal.functions` for model serving
- Or use Modal's hosted model endpoints directly
- Llama 3.1 70B via Modal's infrastructure

### Local Testing Approach
- `test_agent_model.py` will make API calls to Modal (when deployed) or use Modal SDK
- Simple: instantiate agent → send Spanish text → get response
- No webhook infrastructure needed

### Spanish Support
- Update system prompt to emphasize Spanish communication
- Test with common Spanish business phrases
- Ensure tools handle Spanish content correctly

---

## Dependencies to Update

### Add to `requirements.txt`:
- `modal` - Modal SDK for cloud deployment

### Remove/Update in `requirements.txt`:
- `openai` - No longer needed (using Modal models)
- Consider updating `langchain` if needed for Modal integration

---

## Testing Strategy

### Local Testing (Before Modal Deployment)
1. Use `src/test_agent_model.py` to test agent logic
2. Test with Spanish inputs
3. Verify model responses are appropriate

### Modal Deployment Testing
1. Deploy Modal app
2. Test webhook endpoint
3. Test with real WhatsApp messages
4. Verify Spanish responses in production

---

## Notes

- This plan follows the **agent.md** guidelines: minimal changes, step-by-step approach
- Each step should be tested before moving to the next
- Keep existing functionality intact while making changes
- Spanish language support is a priority throughout

---

*This plan will be updated as implementation progresses.*

