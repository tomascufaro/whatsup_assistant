"""
Modal deployment for Qwen2.5-3B model serving.
This creates an API endpoint that serves the Qwen model for Spanish ReAct agent.
"""

import modal

# Create Modal app for LLM
app = modal.App("whatsup-llm")

# Define image with vLLM for fast inference
llm_image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "vllm==0.6.3",
)

# Model configuration - Using Qwen2.5-3B for ReAct agent (open model, good Spanish support, faster cold start)
MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"
GPU_CONFIG = "A10G"  # A10G works well for 3B models


@app.cls(
    image=llm_image,
    gpu=GPU_CONFIG,
    timeout=60 * 10,  # 10 minutes
    scaledown_window=60 * 5,  # 5 minutes idle before shutdown
    retries=0,  # Stop on error, don't retry forever
)
@modal.concurrent(max_inputs=10)
class LLMModel:
    """Generic LLM model served with vLLM - supports Qwen and other models."""

    @modal.enter()
    def load_model(self):
        """Load model on container startup."""
        from vllm import LLM
        import os

        # Set CUDA environment variables for better error reporting
        os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

        self.llm = LLM(
            model=MODEL_NAME,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.85,  # Reduced from 0.90 to avoid CUDA errors
            max_model_len=4096,  # Limit context length to reduce memory usage
            trust_remote_code=True,  # Required for Qwen models
        )
        self.tokenizer = self.llm.get_tokenizer()

    @modal.method()
    def generate(self, messages: list[dict], max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Generate response from messages."""
        from vllm import SamplingParams

        # Format messages into prompt (Qwen2.5 chat format)
        prompt = self._format_chat_prompt(messages)

        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
        )

        result = self.llm.generate(prompt, sampling_params)
        return result[0].outputs[0].text

    def _format_chat_prompt(self, messages: list[dict]) -> str:
        """Format messages into Qwen2.5 chat prompt format."""
        # Use Qwen2.5 chat template (tokenizer is already loaded)
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return prompt


@app.function(image=llm_image)
@modal.web_endpoint(method="POST")
async def generate_endpoint(request_body: dict) -> dict:
    """
    HTTP endpoint for generating responses.
    Compatible with OpenAI-style API format.
    
    Note: Modal's web_endpoint automatically parses JSON when using dict type hint.
    """
    messages = request_body.get("messages", [])
    max_tokens = request_body.get("max_tokens", 500)
    temperature = request_body.get("temperature", 0.7)

    model = LLMModel()
    response_text = model.generate.remote(messages, max_tokens, temperature)

    # Return OpenAI-compatible format
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "index": 0,
                "finish_reason": "stop"
            }
        ],
        "model": MODEL_NAME,
    }
