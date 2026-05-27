from collections import Counter


# --------------------------------
# CATEGORY WEIGHTS
# --------------------------------

CATEGORY_WEIGHTS = {

    "product_ai": 8,

    "technical_ai": 14,

    "research_ai": 7,

    "internal_ai": 4,

    "governance_ai": 2,

    "consulting_ai": 2,

    "marketing_ai": 1,
}

# --------------------------------
# ORGANIZATIONAL ROLE INFERENCE
# --------------------------------

def infer_company_role(evidence_list):

    category_counter = Counter()

    for e in evidence_list:
        category_counter[e.category] += 1


    # --------------------------------
    # ROLE LOGIC
    # --------------------------------

    if (
        category_counter["technical_ai"] >= 2
        and category_counter["product_ai"] >= 3
    ):
        return "ai_native"


    if category_counter["product_ai"] >= 3:
        return "ai_product"

    if (
        category_counter["governance_ai"] >= 3
        or category_counter["consulting_ai"] >= 3
    ):
        return "ai_governance"

    if (
        category_counter["internal_ai"] >= 2
        and category_counter["marketing_ai"] <= 3
    ):
        return "ai_enabled"


    # governance / advisory heavy
    governance_keywords = [
        "governance",
        "risk",
        "compliance",
        "security",
        "policy",
        "framework",
        "responsible ai",
    ]

    governance_hits = 0

    for e in evidence_list:

        text = e.text.lower()

        if any(k in text for k in governance_keywords):
            governance_hits += 1

    if governance_hits >= 3:
        return "ai_governance"


    if category_counter["research_ai"] >= 3:
        return "ai_research"


    if category_counter["marketing_ai"] >= 5:
        return "ai_marketing_only"


    return "ai_consumer"

# --------------------------------
# MAIN REASONING ENGINE
# --------------------------------

def company_reasoning(evidence_list):

    if not evidence_list:
        return False, "NO EVIDENCE", "unknown"

    total_score = 0

    category_counter = Counter()

    unique_texts = set()

    strong_evidence = 0

    technical_hits = 0


    # --------------------------------
    # PROCESS EVIDENCE
    # --------------------------------

    for e in evidence_list:

        # deduplicate repeated chunks
        normalized = e.text.lower().strip()[:120]

        if normalized in unique_texts:
            continue

        unique_texts.add(normalized)

        category_counter[e.category] += 1

        base = CATEGORY_WEIGHTS.get(
            e.category,
            1
        )

        # strength multiplier
        if e.strength == "strong":
            base *= 1.8
            strong_evidence += 1

        elif e.strength == "medium":
            base *= 1.2

        total_score += base

        # technical evidence tracking
        if e.category == "technical_ai":
            technical_hits += 1


    # --------------------------------
    # CONFIDENCE BOOSTS
    # --------------------------------

    # multiple evidence types
    if len(category_counter) >= 3:
        total_score += 8

    elif len(category_counter) >= 2:
        total_score += 4


    # technical confirmation
    if technical_hits >= 2:
        total_score += 10

    elif technical_hits == 1:
        total_score += 5


    # many strong evidences
    if strong_evidence >= 4:
        total_score += 6


    # --------------------------------
    # FALSE POSITIVE PENALTIES
    # --------------------------------

    # only vague marketing fluff
    if (
        category_counter.get("marketing_ai", 0) >= 4
        and len(category_counter) == 1
    ):
        total_score -= 10


    # too little diversity
    if len(category_counter) == 1:
        total_score -= 3

    role = infer_company_role(evidence_list)

    # --------------------------------
    # FINAL VERDICT
    # --------------------------------

    if total_score >= 40:
        return True, "HIGH CONFIDENCE", role

    elif total_score >= 20:
        return True, "MEDIUM CONFIDENCE", role

    elif total_score >= 8:
        return True, "LOW CONFIDENCE", role

    return False, "NO EVIDENCE", "unknown"