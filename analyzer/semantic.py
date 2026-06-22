from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


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
    """,

    "career_ai": """
    Hiring for artificial intelligence, machine learning,
    deep learning, data science, NLP, computer vision,
    or LLM engineering positions. Job postings seeking
    skills in PyTorch, TensorFlow, transformers, model training,
    AI research, or prompt engineering.
    """
}


# -------------------------
# LAZY LOADING LOADER
# -------------------------

_model = None
_definition_embeddings = {}

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    return _model

def get_definition_embeddings():
    global _definition_embeddings
    if not _definition_embeddings:
        model = get_model()
        for label, text in EVIDENCE_TYPES.items():
            _definition_embeddings[label] = model.encode(
                text,
                convert_to_tensor=True
            )
    return _definition_embeddings


# -------------------------
# CLASSIFICATION ENGINE
# -------------------------

def analyze_chunks(chunks):

    findings = []
    
    # Filter short chunks early to avoid redundant model passes
    valid_chunks = [c for c in chunks if len(c.strip()) >= 30]
    if not valid_chunks:
        return findings

    try:
        # Load the sentence-transformer model lazily on first run
        model = get_model()
        definition_embeddings = get_definition_embeddings()

        # Batch encode all valid chunks to utilize PyTorch vectorization
        chunk_embeddings = model.encode(
            valid_chunks,
            batch_size=32,
            show_progress_bar=False,
            convert_to_tensor=True
        )
    except Exception as e:
        print(f"[Semantic] Failed to batch encode chunks: {e}")
        return findings

    for i, text in enumerate(valid_chunks):

        try:
            chunk_embedding = chunk_embeddings[i]
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

            # 0.38 is the similarity threshold
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

        except Exception as e:
            print(f"[Semantic] Failed to process chunk {i}: {e}")
            continue

    return findings