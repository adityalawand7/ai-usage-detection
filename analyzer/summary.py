import os
import json
import logging
import requests
from django.conf import settings

logger = logging.getLogger("analyzer.summary")


def generate_summary(role, confidence, evidence_summary, evidence_list=None):

    api_key = None
    try:
        api_key = getattr(
            settings,
            "GEMINI_API_KEY",
            os.environ.get("GEMINI_API_KEY")
        )
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY")

    # If API key is available, query Gemini API for a premium custom summary
    if api_key and evidence_list:
        try:
            top_evidence = sorted(
                [e for e in evidence_list if e.page_type == "semantic"],
                key=lambda x: x.similarity,
                reverse=True
            )[:5]

            evidence_text = "\n".join([
                f"- [{e.category}]: {e.text}"
                for e in top_evidence
            ])

            techs = list(set([
                e.text
                for e in evidence_list
                if e.page_type == "technical"
            ]))

            tech_evidence = ", ".join(techs)

            prompt = f"""
You are an expert AI adoption analyst. Analyze this company's AI usage and generate a concise, professional executive summary (2-3 sentences max).
Role Classification: {role}
Confidence level: {confidence}

Semantic evidence detected:
{evidence_text}

Technical integrations detected:
{tech_evidence}

Provide ONLY the executive summary text, without any introductory phrases or markdown tags.
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
                ]
            }

            logger.warning("[Summary] Querying Gemini API for executive summary...")
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30
            )
            logger.warning(f"[Summary] API Response Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                summary_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                if summary_text:
                    logger.warning(f"[Summary] Succeeded! Summary generated: {summary_text[:80]}...")
                    return summary_text
            else:
                logger.warning(f"[Summary] API failed with status code {response.status_code}: {response.text}")

        except Exception as e:
            logger.warning(f"[Summary] API exception: {e}")

    # --------------------------------
    # HEURISTIC FALLBACK
    # --------------------------------

    semantic = evidence_summary.get("semantic", 0)
    technical = evidence_summary.get("technical", 0)
    behavioral = evidence_summary.get("behavioral", 0)
    organizational = evidence_summary.get("organizational", 0)

    if role == "ai_native":
        return (
            "This organization appears to be deeply AI-native, "
            "with strong evidence of technical AI integrations, "
            "AI-driven products, and operational AI usage."
        )

    elif role == "ai_product":
        return (
            "This organization appears to actively build or deliver "
            "AI-powered products and services."
        )

    elif role == "ai_governance":
        return (
            "This organization primarily appears focused on "
            "AI governance, advisory, compliance, or consulting services "
            "rather than native AI product development."
        )

    elif role == "ai_enabled":
        return (
            "This organization appears to use AI internally "
            "to enhance operations, workflows, or customer experiences."
        )

    elif role == "ai_marketing_only":
        return (
            "AI-related language was detected, but evidence suggests "
            "primarily marketing-oriented AI positioning."
        )

    return (
        "Limited AI evidence was detected across the analyzed pages."
    )