from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


# -------------------------
# LOAD MODEL
# -------------------------

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# -------------------------
# EVIDENCE DEFINITIONS
# -------------------------

EVIDENCE_TYPES = {

    "product_ai": """
    The company develops proprietary AI software,
    AI applications, AI platforms, AI copilots,
    AI assistants, AI agents, machine learning systems,
    or generative AI products used directly by customers.
    The company BUILDS AI technology products.
    """,


    "internal_ai": """
    The company uses AI internally for operations,
    support, analytics, productivity, workflows,
    automation, or employee assistance.
    """,


    "research_ai": """
    The company develops AI models,
    machine learning research,
    foundation models,
    neural networks,
    or publishes AI research.
    """,


    "governance_ai": """
    The company provides AI governance,
    AI compliance,
    AI security,
    AI risk management,
    AI policy,
    responsible AI,
    AI auditing,
    or AI regulatory services.
    """,


    "consulting_ai": """
    The company advises clients about AI adoption,
    AI transformation,
    AI strategy,
    AI readiness,
    AI consulting,
    enterprise AI enablement,
    or AI modernization services.
    """,


    "marketing_ai": """
    Generic or vague references to AI,
    intelligent systems,
    innovation,
    future technology,
    or automation buzzwords.
    """
}


# -------------------------
# PRECOMPUTE EMBEDDINGS
# -------------------------

definition_embeddings = {}

for label, text in EVIDENCE_TYPES.items():

    definition_embeddings[label] = model.encode(
        text,
        convert_to_tensor=True
    )


# -------------------------
# CLASSIFICATION ENGINE
# -------------------------

def analyze_chunks(chunks):

    findings = []

    for text in chunks:

        if len(text.strip()) < 80:
            continue

        try:

            chunk_embedding = model.encode(
                text,
                convert_to_tensor=True
            )

            best_category = None
            best_score = 0

            for category, definition_embedding in definition_embeddings.items():

                similarity = cos_sim(
                    chunk_embedding,
                    definition_embedding
                ).item()

                if similarity > best_score:

                    best_score = similarity
                    best_category = category

            if best_score > 0.38:

                findings.append({

                    "text": text,

                    "similarity": round(best_score, 3),

                    "category": best_category,

                    "strength": (
                        "strong"
                        if best_score > 0.62
                        else "medium"
                    )
                })

        except:
            continue

    return findings