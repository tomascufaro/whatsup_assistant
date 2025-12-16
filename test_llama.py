"""
Test the deployed Llama model using HTTP endpoint.
Run with: uv run python test_llama.py

Note: First request may take 1-2 minutes (cold start - loading model into GPU).
"""

import requests

# Your deployed endpoint URL
ENDPOINT_URL = "https://tomascufaro--llama-8b-spanish-generate-endpoint.modal.run"


def test_model():
    """Test the deployed Llama model."""
    print("Testing deployed Llama 3.1 8B model...")
    print("Note: First request may take 1-2 minutes (cold start)")
    print("-" * 50)

    test_cases = [
        {
            "messages": [
                {"role": "system", "content": "Eres un asistente útil."},
                {"role": "user", "content": "Hola, ¿cómo estás?"}
            ],
            "description": "Simple greeting"
        },
        {
            "messages": [
                {"role": "system", "content": "Eres un asistente secretarial para un negocio."},
                {"role": "user", "content": "Necesito agendar una reunión para mañana a las 3pm"}
            ],
            "description": "Secretary task"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"User: {test_case['messages'][-1]['content']}")
        print("Waiting for response...")

        try:
            response = requests.post(
                ENDPOINT_URL,
                json={
                    "messages": test_case["messages"],
                    "max_tokens": 200,
                    "temperature": 0.7
                },
                timeout=180  # 3 minutes for cold start
            )
            response.raise_for_status()
            result = response.json()

            assistant_response = result["choices"][0]["message"]["content"]
            print(f"Assistant: {assistant_response}")

        except requests.exceptions.Timeout:
            print("Error: Request timed out. The model might still be loading.")
            print("Try again in a minute.")
        except Exception as e:
            print(f"Error: {e}")
            if 'response' in locals():
                print(f"Status: {response.status_code}")
                print(f"Response: {response.text[:500]}")

        print("-" * 50)


if __name__ == "__main__":
    test_model()
