def generate_summary(role, confidence, evidence_summary):

    semantic = evidence_summary["semantic"]

    technical = evidence_summary["technical"]

    behavioral = evidence_summary["behavioral"]

    organizational = evidence_summary["organizational"]


    # --------------------------------
    # ROLE-BASED SUMMARIES
    # --------------------------------

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