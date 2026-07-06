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

    "career_ai": 10
}

# --------------------------------
# ORGANIZATIONAL ROLE INFERENCE
# --------------------------------

def infer_company_role(evidence_list):

    category_counter = Counter()

    for e in evidence_list:
        category_counter[e.category] += 1

    total_hits = sum(category_counter.values())
    if total_hits == 0:
        return "unknown"

    # 1. AI-Native: Must have actual technical signatures and product mentions
    if category_counter["technical_ai"] >= 1 and category_counter["product_ai"] >= 2:
        return "ai_native"

    # 2. AI Governance & Advisory: Primary focus is advisory, consulting, or governance
    advisory_hits = category_counter["governance_ai"] + category_counter["consulting_ai"]
    if advisory_hits >= 2 and advisory_hits >= category_counter["product_ai"]:
        return "ai_governance"

    # 3. AI Product: Main focus is product, but doesn't have native technical signatures yet
    if category_counter["product_ai"] >= 3 and category_counter["product_ai"] > advisory_hits:
        return "ai_product"

    # 4. AI-Enabled: Heavy internal usage or active hiring
    if category_counter["internal_ai"] >= 2 or category_counter["career_ai"] >= 2:
        return "ai_enabled"

    # 5. AI Research: Heavy research focus
    if category_counter["research_ai"] >= 2 and category_counter["research_ai"] >= category_counter["product_ai"]:
        return "ai_research"

    # 6. AI Marketing Presence: Mostly marketing fluff, very few other signals
    if category_counter["marketing_ai"] >= 3 and category_counter["marketing_ai"] > (total_hits - category_counter["marketing_ai"]):
        return "ai_marketing_only"

    # Fallback to consumer
    return "ai_consumer"

# --------------------------------
# MAIN REASONING ENGINE
# --------------------------------

def company_reasoning(evidence_list):

    if not evidence_list:
        return False, "NO EVIDENCE", "unknown", 0, {}

    total_score = 0

    category_counter = Counter()

    category_scores = Counter()

    unique_texts = set()

    strong_evidence = 0

    technical_hits = 0

    score_breakdown = {

        "base_score": 0,

        "diversity_bonus": 0,

        "technical_bonus": 0,

        "strong_evidence_bonus": 0,

        "penalties": 0
    }


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

        category_scores[e.category] += base


        # technical evidence tracking
        if e.category == "technical_ai":
            technical_hits += 1


    # --------------------------------
    # CATEGORY CAPS
    # --------------------------------

    category_scores["technical_ai"] = min(
        category_scores["technical_ai"],
        40
    )

    category_scores["product_ai"] = min(
        category_scores["product_ai"],
        40
    )

    category_scores["research_ai"] = min(
        category_scores["research_ai"],
        20
    )

    category_scores["career_ai"] = min(
        category_scores["career_ai"],
        25
    )

    category_scores["internal_ai"] = min(
        category_scores["internal_ai"],
        15
    )

    category_scores["governance_ai"] = min(
        category_scores["governance_ai"],
        15
    )

    category_scores["consulting_ai"] = min(
        category_scores["consulting_ai"],
        15
    )

    category_scores["marketing_ai"] = min(
        category_scores["marketing_ai"],
        10
    )

    total_score = sum(
        category_scores.values()
    )

    score_breakdown["base_score"] = round(
        total_score,
        1
    )

    score_breakdown["category_scores"] = dict(
        category_scores
    )

    # --------------------------------
    # CONFIDENCE BOOSTS
    # --------------------------------

    # multiple evidence types
    if len(category_counter) >= 4:

        total_score += 12

        score_breakdown["diversity_bonus"] += 12

    elif len(category_counter) >= 3:

        total_score += 8

        score_breakdown["diversity_bonus"] += 8

    elif len(category_counter) >= 2:

        total_score += 4

        score_breakdown["diversity_bonus"] += 4


    # technical confirmation
    if technical_hits >= 2:

        total_score += 10

        score_breakdown["technical_bonus"] += 10

    elif technical_hits == 1:

        total_score += 5

        score_breakdown["technical_bonus"] += 5


    # many strong evidences
    if strong_evidence >= 4:

        total_score += 6

        score_breakdown["strong_evidence_bonus"] += 6


    # --------------------------------
    # FALSE POSITIVE PENALTIES
    # --------------------------------

    # only vague marketing fluff
    if (

        category_counter.get("marketing_ai", 0) >= 4

        and technical_hits == 0

    ):

        total_score -= 15

        score_breakdown["penalties"] -= 15

    governance_hits = (

        category_counter["governance_ai"]

        + category_counter["consulting_ai"]
    )

    if governance_hits >= 5 and technical_hits == 0:

        total_score -= 12

        score_breakdown["penalties"] -= 12

    elif governance_hits >= 3 and technical_hits == 0:

        total_score -= 6

        score_breakdown["penalties"] -= 6

    # too little diversity
    if len(category_counter) == 1:

        total_score -= 3

        score_breakdown["penalties"] -= 3

    role = infer_company_role(evidence_list)

    # --------------------------------
    # FINAL VERDICT
    # --------------------------------

    if total_score >= 70 and technical_hits >= 1:

        return (
            True,
            "HIGH CONFIDENCE",
            role,
            total_score,
            score_breakdown
        )

    elif total_score >= 40:

        return (
            True,
            "MEDIUM CONFIDENCE",
            role,
            total_score,
            score_breakdown
        )

    elif total_score >= 8:

        return (
            True,
            "LOW CONFIDENCE",
            role,
            total_score,
            score_breakdown
        )

    return (
        False,
        "NO EVIDENCE",
        "unknown",
        total_score,
        score_breakdown
    )