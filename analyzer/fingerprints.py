AI_TECH_PATTERNS = {

    "openai": [
        "openai",
        "api.openai.com",
        "chatgpt",
        "gpt-4",
        "gpt-3.5"
    ],

    "anthropic": [
        "anthropic",
        "claude"
    ],

    "google_ai": [
        "gemini",
        "vertexai",
        "generativeai"
    ],

    "huggingface": [
        "huggingface",
        "transformers"
    ],

    "langchain": [
        "langchain"
    ],

    "llamaindex": [
        "llamaindex"
    ],

    "vercel_ai_sdk": [
        "ai-sdk",
        "@ai-sdk",
        "vercel ai"
    ],

    "inference_api": [
        "/chat/completions",
        "/completions",
        "/embeddings",
        "/inference",
        "/ai/",
        "/copilot",
        "/assistant",
        "/agents"
    ]
}


# --------------------------------
# DETECT AI FINGERPRINTS
# --------------------------------

def detect_fingerprints(content):

    findings = []

    content = content.lower()

    for tech, patterns in AI_TECH_PATTERNS.items():

        if any(
            pattern.lower() in content
            for pattern in patterns
        ):
            findings.append(tech)

    return findings