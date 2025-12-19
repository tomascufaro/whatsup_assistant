"""
Memory test for the FastAPI WhatsApp webhook.
Sends two messages from the same chat_id and checks the agent recalls prior context.

Usage:
    uv run python -m tests.test_agent_memory_webhook

Env:
    WEBHOOK_URL (preferred) or FASTAPI_WEBHOOK_URL or WHATSAPP_WEBHOOK_URL
"""

import os
import re
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()


def resolve_webhook_url() -> str | None:
    """Resolve webhook URL from env; no hardcoded defaults."""
    return (
        os.getenv("WEBHOOK_URL")
        or os.getenv("FASTAPI_WEBHOOK_URL")
        or os.getenv("WHATSAPP_WEBHOOK_URL")
    )


def test_agent_memory_webhook() -> bool:
    webhook_url = resolve_webhook_url()
    if not webhook_url:
        print("❌ FASTAPI_WEBHOOK_URL / WHATSAPP_WEBHOOK_URL / WEBHOOK_URL not set; cannot run test.")
        return False

    test_chat_id = "whatsapp:+1234567890"

    print("\n" + "=" * 70)
    print("🧠 MEMORY TEST - FastAPI Webhook Endpoint")
    print("=" * 70)
    print(f"📍 Webhook URL: {webhook_url}")
    print(f"📱 Test Chat ID: {test_chat_id}")
    print("=" * 70)

    # Message 1: Set context
    print("\n📤 STEP 1: Setting context")
    print("   Sending: 'Mi nombre es Carlos'")
    try:
        start = time.time()
        r1 = requests.post(
            webhook_url,
            data={"From": test_chat_id, "Body": "Mi nombre es Carlos", "MessageSid": "test_1"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=180,
        )
        duration = time.time() - start
        print(f"   ✅ Response received (status {r1.status_code}, {duration:.1f}s)")

        # Extract message from TwiML XML
        match = re.search(r"<Message>(.+?)</Message>", r1.text, re.DOTALL)
        if match:
            message = match.group(1).strip()
            print(f'   💬 Agent said: "{message}"')

        if "error" in r1.text.lower():
            print("   ❌ ERROR: Response contains error message")
            return False

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    time.sleep(2)

    # Message 2: Test memory
    print("\n📤 STEP 2: Testing memory recall")
    print("   Sending: '¿Cómo me llamo?'")
    try:
        start = time.time()
        r2 = requests.post(
            webhook_url,
            data={"From": test_chat_id, "Body": "¿Cómo me llamo?", "MessageSid": "test_2"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=180,
        )
        duration = time.time() - start
        print(f"   ✅ Response received (status {r2.status_code}, {duration:.1f}s)")

        # Extract message from TwiML XML
        match = re.search(r"<Message>(.+?)</Message>", r2.text, re.DOTALL)
        if match:
            message = match.group(1).strip()
            print(f'   💬 Agent said: "{message}"')
        else:
            print("   ⚠️  Could not parse TwiML response")

        if "error" in r2.text.lower():
            print("   ❌ ERROR: Response contains error message")
            return False

        # Check if memory worked
        has_carlos = "carlos" in r2.text.lower()

        print("\n" + "=" * 70)
        if has_carlos:
            print("✅ MEMORY TEST PASSED!")
            print("   The agent correctly remembered 'Carlos' from the previous message.")
        else:
            print("❌ MEMORY TEST FAILED")
            print("   The agent did not mention 'Carlos' in its response.")
        print("=" * 70)

        return has_carlos

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_agent_memory_webhook()
    sys.exit(0 if success else 1)
