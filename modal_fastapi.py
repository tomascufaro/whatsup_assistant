"""
Modal deployment for FastAPI WhatsApp webhook handler.
"""

import modal
from pathlib import Path

app = modal.App("whatsapp-assistant")

# Create persistent volume for memory storage
volume = modal.Volume.from_name("memory-storage", create_if_missing=True)

# Define image with dependencies and local src directory
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "twilio>=8.10.0",
        "httpx>=0.25.0",
        "python-multipart>=0.0.6",
        "langchain>=0.1.0",
        "langchain-openai>=0.1.0",
        "langchainhub>=0.1.14",
        "langgraph>=0.1.0",
        "pandas>=2.1.3",
        "pydantic>=2.5.0",
    )
    .add_local_dir(
        Path(__file__).parent / "src",
        remote_path="/root/src"
    )
)

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("whatsapp-secrets")],
    volumes={"/data/memory": volume},
    timeout=180,  # 3 minute timeout (enough for cold start + LLM response)
)
@modal.asgi_app()
def fastapi_app():
    """Deploy FastAPI app on Modal."""
    import sys

    print("Starting FastAPI app deployment...")
    print(f"Python path: {sys.path}")

    # Add src directory to Python path
    sys.path.insert(0, "/root/src")
    print(f"Updated Python path: {sys.path}")

    try:
        from main import app as fastapi_app
        print("Successfully imported FastAPI app")
        return fastapi_app
    except Exception as e:
        print(f"ERROR: Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        raise
