"""
Modal app to serve vLLM in OpenAI-compatible mode (chat completions only, tools off for now).
Uses a tool-capable instruct model (Mistral 7B) so we can enable tools later.
"""

import json
import subprocess
from typing import Any

import modal

app = modal.App("vllm-serve")

# Model / hardware (tool-capable model; tools disabled client-side for now)
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
MODEL_REVISION = None  # set to a specific hash if you want to pin
GPU_TYPE = "H100"  # adjust if you pick a smaller model/GPU

# Tuning
FAST_BOOT = True
MINUTES = 60

# Caches
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

# Image with vLLM deps
vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.11.2",
        "huggingface-hub==0.36.0",
        "flashinfer-python==0.5.2",
        "aiohttp",  # used by local entrypoint test
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)


@app.function(
    image=vllm_image,
    gpu=GPU_TYPE,
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
    """Launch vLLM OpenAI-compatible server."""
    cmd = [
        "vllm",
        "serve",
        "--uvicorn-log-level=info",
        MODEL_NAME,
    ]
    if MODEL_REVISION:
        cmd += ["--revision", MODEL_REVISION]
    cmd += [
        "--served-model-name",
        MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
    cmd += ["--enforce-eager" if FAST_BOOT else "--no-enforce-eager"]
    cmd += ["--tensor-parallel-size", "1"]
    print("Starting vLLM server:", cmd)
    subprocess.Popen(cmd)


# ---- Local smoke test helpers ----


@app.local_entrypoint()
async def test(test_timeout: int = 10 * MINUTES, content: str | None = None, twice: bool = True):
    """Health + basic completion smoke test against the deployed server."""
    import aiohttp  # noqa: WPS433

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


async def _send_request(session: Any, model: str, messages: list) -> None:
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
