import os
import json
import requests
from django.conf import settings

LOCAL_EXPLANATIONS = {
    "product_ai": "Refers to building, developing, or selling proprietary AI software, platforms, or copilots.",
    "internal_ai": "Mentions leveraging AI internally for business operations, productivity, workflows, or support.",
    "research_ai": "Mentions model training, machine learning research, neural architectures, or publishing papers.",
    "governance_ai": "Refers to AI compliance, auditing, responsible AI frameworks, risk management, or policies.",
    "consulting_ai": "Refers to advising clients on AI strategy, implementation, or technical enablement.",
    "marketing_ai": "Matches general marketing claims, buzzwords, or positioning around intelligent automation.",
    "career_ai": "Matches recruitment signals seeking skills in machine learning, PyTorch, or prompt engineering.",
    "technical_ai": "Identified an active technical SDK, API client signature, or infrastructure fingerprint.",
    "behavioral_ai": "Identified active network requests or traffic directed at AI backend endpoints."
}

def generate_evidence_explanations(serialized_evidence):
    """
    Generates explanations for each evidence chunk.
    If a GEMINI_API_KEY is available, we query Gemini to explain the top 8 most significant
    semantic evidence chunks using a single batched JSON query.
    For the remaining chunks, we use predefined local template heuristics.
    """
    # 1. Apply local template fallback explanations to all items
    for item in serialized_evidence:
        cat = item.get("category", "")
        item["explanation"] = LOCAL_EXPLANATIONS.get(cat, "Identified signal of AI adoption or positioning.")
        item["explanation_source"] = "local"

    # 2. Get API key
    api_key = None
    try:
        api_key = getattr(
            settings,
            "GEMINI_API_KEY",
            os.environ.get("GEMINI_API_KEY")
        )
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return serialized_evidence

    # 3. Filter and sort items to explain (only explain semantic and technical items, up to top 8)
    semantic_items = [
        item for item in serialized_evidence 
        if item.get("page_type") in ["semantic", "technical", "organizational"]
    ]
    
    if not semantic_items:
        return serialized_evidence

    # Sort by similarity score descending to prioritize the strongest evidence
    items_to_explain = sorted(
        semantic_items,
        key=lambda x: x.get("similarity", 0),
        reverse=True
    )[:8]

    try:
        # Build batch prompt
        prompt = """You are an expert AI adoption analyst. For each of the following text snippets (extracted from a company's website or technical signatures), explain in one short sentence (max 15 words) why it serves as evidence of AI adoption in the specified category.
Be specific and directly reference the content of the snippet. Keep it professional.

Snippets:
"""
        for idx, item in enumerate(items_to_explain):
            prompt += f"{idx + 1}. [Category: {item['category']}] \"{item['text']}\"\n"

        prompt += """
Provide your response strictly as a JSON array of strings, where each element is the explanation for the corresponding snippet. Do not include markdown formatting or wrapper tags.
Example response:
[
  "The snippet refers to developing a proprietary chatbot helper, which indicates product development.",
  "Hiring for data scientists with PyTorch experience indicates active AI recruiting."
]
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            explanations = json.loads(raw_text)
            
            if isinstance(explanations, list) and len(explanations) == len(items_to_explain):
                for idx, exp in enumerate(explanations):
                    items_to_explain[idx]["explanation"] = exp.strip()
                    items_to_explain[idx]["explanation_source"] = "gemini"

    except Exception as e:
        print(f"[Explanations] Failed to generate AI reasoning: {e}")

    return serialized_evidence
