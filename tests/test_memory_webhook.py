"""Test memory persistence by sending multiple messages to WhatsApp webhook."""

import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()


def get_webhook_url():
    """Get webhook URL from MODAL_ENDPOINT_URL."""
    modal_url = os.getenv("MODAL_ENDPOINT_URL")
    if not modal_url:
        return None
    
    # Extract workspace from MODAL_ENDPOINT_URL
    # Format: https://workspace--app-function.modal.run
    # Convert to: https://workspace--whatsapp-assistant-fastapi-app.modal.run/webhook/whatsapp
    if "--" in modal_url:
        workspace = modal_url.split("--")[0].replace("https://", "")
        return f"https://{workspace}--whatsapp-assistant-fastapi-app.modal.run/webhook/whatsapp"
    return None


def test_memory_via_webhook():
    """Test memory by sending sequential messages."""
    
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("❌ Could not determine webhook URL from MODAL_ENDPOINT_URL")
        return False
    
    test_chat_id = "whatsapp:+1234567890"
    
    print("\n" + "=" * 70)
    print(" 🧠 MEMORY PERSISTENCE TEST - WhatsApp Webhook")
    print("=" * 70)
    print(f"📍 Webhook URL: {webhook_url}")
    print(f"📱 Test Chat ID: {test_chat_id}")
    print("=" * 70 + "\n")
    
    # Message 1: Set context
    print("📤 STEP 1: Setting context")
    print("   Sending: 'Mi nombre es Carlos'")
    print("   Purpose: Establish user name in conversation memory")
    try:
        start = time.time()
        r1 = requests.post(
            webhook_url,
            data={"From": test_chat_id, "Body": "Mi nombre es Carlos", "MessageSid": "test_1"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=180
        )
        duration = time.time() - start
        response1_text = r1.text
        
        print(f"   ✅ Response received (status {r1.status_code}, {duration:.1f}s)")
        
        # Extract message from XML
        import re
        match = re.search(r'<Message>(.+?)</Message>', response1_text, re.DOTALL)
        if match:
            message = match.group(1).strip()
            print(f"   💬 Agent said: \"{message}\"")
        
        # Check for errors in response
        if "error" in response1_text.lower() or "Connection error" in response1_text:
            print("   ❌ ERROR: Response contains error message")
            print(f"   Full response: {response1_text}")
            print("\n   🔧 Troubleshooting:")
            print("      - Check that modal_llm_app.py is deployed and running")
            print("      - Run: uv run modal deploy modal_llm_app.py")
            print("      - Verify MODAL_ENDPOINT_URL in Modal secrets")
            return False
        
        print()
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    time.sleep(2)
    
    # Message 2: Test memory
    print("📤 STEP 2: Testing memory recall")
    print("   Sending: '¿Cómo me llamo?'")
    print("   Purpose: Check if agent remembers the name from Step 1")
    try:
        start = time.time()
        r2 = requests.post(
            webhook_url,
            data={"From": test_chat_id, "Body": "¿Cómo me llamo?", "MessageSid": "test_2"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=180
        )
        duration = time.time() - start
        response_text = r2.text
        
        print(f"   ✅ Response received (status {r2.status_code}, {duration:.1f}s)")
        
        # Extract message from XML
        import re
        match = re.search(r'<Message>(.+?)</Message>', response_text, re.DOTALL)
        if match:
            message = match.group(1).strip()
            print(f"   💬 Agent said: \"{message}\"")
        
        # Check for errors
        if "error" in response_text.lower() or "Connection error" in response_text:
            print("   ❌ ERROR: Response contains error message")
            print(f"   Full response: {response_text}")
            print("\n   🔧 Troubleshooting:")
            print("      - Check that modal_llm_app.py is deployed and running")
            print("      - Run: uv run modal deploy modal_llm_app.py")
            return False
        
        has_carlos = "carlos" in response_text.lower()
        
        print("\n" + "=" * 70)
        if has_carlos:
            print("✅ TEST PASSED: Memory is working!")
            print("   The agent correctly remembered 'Carlos' from the previous message.")
        else:
            print("❌ TEST FAILED: Memory not working")
            print("   The agent did not mention 'Carlos' in its response.")
            print("   Expected response to include the name from Step 1.")
        print("=" * 70)
        
        return has_carlos
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_memory_via_webhook()
    sys.exit(0 if success else 1)

