AI_FINGERPRINTS = {
    "openai": "OpenAI",
    "gpt-4": "OpenAI",
    "anthropic": "Anthropic",
    "claude": "Anthropic",
    "huggingface": "Hugging Face",
    "replicate.com": "Replicate",
    "api.openai.com": "OpenAI API",
    "langchain": "LangChain",
    "llama": "Meta LLaMA",
}


def detect_fingerprints(content):

    detected = []

    content_lower = content.lower()

    for key, provider in AI_FINGERPRINTS.items():
        if key in content_lower:
            detected.append(provider)

    return list(set(detected))