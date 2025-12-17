# Setup Guide: Modal Deployment

## Step 1: Install Modal

```bash
pip install modal
```

## Step 2: Authenticate with Modal

```bash
modal token new
```

This will open a browser for authentication.

## Step 3: Deploy the LLM Model

```bash
modal deploy modal_llm_app.py
```

This will:
- Deploy the LLM model on Modal with vLLM
- Create an HTTP endpoint
- Give you a URL like: `https://your-workspace--whatsup-llm-generate-endpoint.modal.run`

**Copy this URL** - you'll need it for the next step.

## Step 4: Create Modal Secrets

Create secrets for your environment variables:

```bash
modal secret create whatsapp-secrets \
  MODAL_ENDPOINT_URL="<paste-the-url-from-step-3>" \
  TWILIO_ACCOUNT_SID="your_twilio_sid" \
  TWILIO_AUTH_TOKEN="your_twilio_token" \
  TWILIO_PHONE_NUMBER="your_twilio_number"
```

**Note**: You can also add secrets via Modal dashboard at https://modal.com/secrets

## Step 5: Deploy the FastAPI App

```bash
modal deploy modal.py
```

This will give you a webhook URL like:
`https://your-workspace--whatsapp-assistant-fastapi-app.modal.run`

## Step 6: Configure WhatsApp Webhook

### For Twilio:
1. Go to Twilio Console → WhatsApp → Sandbox (or your number)
2. Set webhook URL to: `https://your-modal-url/webhook/whatsapp`
3. Method: POST

### For Meta:
1. Go to Meta Developer Console → WhatsApp → Configuration
2. Set webhook URL to: `https://your-modal-url/webhook/whatsapp`
3. Verify token (if needed)

## Step 7: Test

Send a WhatsApp message to your number. You should get a Spanish response!

## Useful Commands

### Check deployment status
```bash
modal app list
```

### View logs (LLM)
```bash
modal app logs whatsup-llm
```

### View logs (FastAPI)
```bash
modal app logs whatsapp-assistant
```

### Stop deployments
```bash
modal app stop whatsup-llm
modal app stop whatsapp-assistant
```

## Cost Optimization

The LLM uses:
- **GPU**: A10G (cost-effective for 8B models)
- **Idle timeout**: 5 minutes (shuts down when not in use)
- **Auto-scaling**: Scales to zero when idle

**Expected cost**: ~$0.50-1.00 per hour of active GPU time. With idle timeout, you only pay when processing messages.

## Troubleshooting

### "MODAL_ENDPOINT_URL not set" error
- Make sure you created the secret in Step 4
- Verify the secret name matches in `modal.py`: `modal.Secret.from_name("whatsapp-secrets")`

### Model taking too long to respond
- First request after idle period takes 1-2 minutes (cold start)
- Subsequent requests are fast (<5 seconds)
- Consider increasing `container_idle_timeout` if needed

### Out of memory errors
- The 8B model needs ~16GB GPU memory
- A10G has 24GB, so should be fine
- If issues persist, reduce `gpu_memory_utilization` in `modal_llm.py`

## Local Testing (Optional)

You can't run the GPU model locally, but you can test the FastAPI app:

1. Set environment variables:
```bash
export MODAL_ENDPOINT_URL="https://your-modal-llm-url"
export TWILIO_ACCOUNT_SID="your_sid"
export TWILIO_AUTH_TOKEN="your_token"
export TWILIO_PHONE_NUMBER="your_number"
```

2. Run locally:
```bash
uvicorn src.main:app --reload
```

3. Test health endpoint:
```bash
curl http://localhost:8000/health
```

## Next Steps

Once everything works:
1. Test with various Spanish messages
2. Monitor costs in Modal dashboard
3. Adjust `temperature` and `max_tokens` in [core.py](src/agent/core.py#L48) if needed
4. Consider upgrading to Llama 3.1 70B if responses need improvement
