# vLLM Migration Plan: GPU LLM Server + CPU FastAPI/Agent

## Current Architecture Problems

- **Endpoint mismatch**: Custom `/generate_endpoint` vs. `ChatOpenAI` expecting `/v1/chat/completions` → connection/404 errors.
- **Split apps with friction**: CPU FastAPI/Agent calling GPU LLM over HTTP; two cold starts and network hops.
- **Decoupled memory/tools**: Memory and tools run on CPU; model on GPU; harder to tune/scale.

## Target Architecture (recommended)

- **GPU app**: vLLM OpenAI-compatible server exposed at `/v1/chat/completions` via `@modal.web_server`.
- **CPU app**: FastAPI + Agent (LangGraph/tools/memory) using `ChatOpenAI` pointed at the vLLM server URL.
- **OpenAI compatibility** end-to-end; no custom glue.

Why this split?
- Clear separation of concerns; vLLM owns the GPU, FastAPI/tools stay on CPU.
- Keeps your existing Agent code (just point it at `VLLM_SERVER_URL`).
- Follows Modal’s vLLM pattern; avoids embedding FastAPI into the GPU box unless needed.

## GPU vLLM Server (new app)

Example shape (adjust GPU/model as needed):
```python
import modal

app = modal.App("vllm-serve")
MODEL_NAME = "Qwen/Qwen3-8B-FP8"        # use H100-class; for A10G pick a smaller model (e.g., Qwen2.5-3B)
MODEL_REVISION = "220b46e3b2180893580a4454f21f22d3ebb187d3"
FAST_BOOT = True
MINUTES = 60

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.11.2", "huggingface-hub==0.36.0", "flashinfer-python==0.5.2", "aiohttp")
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

@app.function(
    image=vllm_image,
    gpu="H100",  # adjust if changing model
    scaledown_window=15 * MINUTES,
    timeout=10 * MINUTES,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=8000, startup_timeout=10 * MINUTES)
def serve():
    import subprocess

    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        MODEL_NAME,
        "--revision",
        MODEL_REVISION,
        "--served-model-name",
        MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    cmd += ["--enforce-eager" if FAST_BOOT else "--no-enforce-eager"]
    cmd += ["--tensor-parallel-size", "1"]
    print(cmd)
    subprocess.Popen(cmd)  # spawn and return; @web_server keeps the process alive
```

### Local entrypoint for health/smoke test
Add this to the vLLM server file to sanity-check deploys:
```python
import json, aiohttp

@app.local_entrypoint()
async def test(test_timeout=10 * MINUTES, content=None, twice=True):
    url = serve.get_web_url()

    system_prompt = {
        "role": "system",
        "content": "You are a pirate who can't help but drop sly reminders that he went to Harvard.",
    }
    if content is None:
        content = "Explain the singular value decomposition."

    messages = [
        system_prompt,
        {"role": "user", "content": content},
    ]

    async with aiohttp.ClientSession(base_url=url) as session:
        print(f"Running health check for server at {url}")
        async with session.get("/health", timeout=test_timeout - 1 * MINUTES) as resp:
            up = resp.status == 200
        assert up, f"Failed health check for server at {url}"
        print(f"Successful health check for server at {url}")

        print(f"Sending messages to {url}:", *messages, sep="\n\t")
        await _send_request(session, MODEL_NAME, messages)
        if twice:
            messages[0]["content"] = "You are Jar Jar Binks."
            print(f"Sending messages to {url}:", *messages, sep="\n\t")
            await _send_request(session, MODEL_NAME, messages)


async def _send_request(session: aiohttp.ClientSession, model: str, messages: list) -> None:
    payload: dict[str, Any] = {"messages": messages, "model": model, "stream": True}
    headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}

    async with session.post("/v1/chat/completions", json=payload, headers=headers, timeout=1 * MINUTES) as resp:
        async for raw in resp.content:
            resp.raise_for_status()
            line = raw.decode().strip()
            if not line or line == "data: [DONE]":
                continue
            if line.startswith("data: "):
                line = line[len("data: ") :]
            chunk = json.loads(line)
            assert chunk["object"] == "chat.completion.chunk"
            print(chunk["choices"][0]["delta"]["content"], end="")
    print()
```

## CPU FastAPI + Agent

- Keep FastAPI on CPU (current `modal_fastapi.py`).
- In `src/agent/core.py`, configure:
  - `ChatOpenAI(base_url=os.getenv("VLLM_SERVER_URL"), api_key="dummy", model=MODEL_NAME, ...)`.
  - Remove `MODAL_ENDPOINT_URL` once cut over; add `VLLM_SERVER_URL` (the vLLM server URL ending with `/v1`).
- Memory and tools stay unchanged.

## Implementation Steps

1) Create and deploy `modal_vllm_server.py` (as above). Deploy with `modal deploy modal_vllm_server.py`.
2) Update `src/agent/core.py` to point `ChatOpenAI` at `VLLM_SERVER_URL`; drop `MODAL_ENDPOINT_URL`.
3) Ensure FastAPI webhook uses the updated Agent. Redeploy FastAPI app.
4) Add `VLLM_SERVER_URL` to secrets/env; keep Twilio vars. Add `HF_TOKEN` if the model is private.
5) Use the local entrypoint to health-check vLLM and smoke test completions.

## Testing Strategy

- vLLM server: `/health` and `/v1/chat/completions` via local entrypoint or manual request.
- Agent: unit test with mocked `ChatOpenAI`.
- Integration: FastAPI webhook → Agent → vLLM server URL.
- End-to-end: WhatsApp flow + memory + tools.

## Rollback Plan

If migration fails:
- Keep old `modal_llm_app.py`/`modal_fastapi.py` deployed.
- Revert `src/agent/core.py` to use `MODAL_ENDPOINT_URL`.
- Restore `MODAL_ENDPOINT_URL` in secrets/env.

## Notes on GPU/Model Choice

- Qwen3-8B-FP8 expects H100/H200-class GPUs. For A10G, pick a smaller model (e.g., Qwen2.5-3B-Instruct) and adjust the `vllm serve` command accordingly (no FP8).
- Volumes (`huggingface-cache`, `vllm-cache`) are important to avoid repeated weight/JIT downloads.
