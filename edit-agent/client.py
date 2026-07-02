"""
client.py

Low-level HTTP client for the Ollama API.
Wraps the /api/chat endpoint behind a clean function.
Swapping to a different provider later means changing this file only.
"""

import requests

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"


def complete(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Send a system + user prompt to the local Ollama model and return the response.

    Args:
        system_prompt: The agent's identity, rules, and constraints.
        user_prompt:   The specific task or question for this request.
        model:         The Ollama model name to use.

    Returns:
        The model's response as a plain string.

    Raises:
        requests.HTTPError: If the Ollama API returns a non-2xx status.
        requests.ConnectionError: If Ollama is not running.
    """
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = requests.post(url, json=payload, timeout=120)
    response.raise_for_status()

    return response.json()["message"]["content"]


if __name__ == "__main__":
    # Smoke test — run directly with: python client.py
    reply = complete(
        system_prompt="You are a helpful assistant. Always respond in exactly one sentence.",
        user_prompt="What is an AI agent?",
    )
    print(reply)
