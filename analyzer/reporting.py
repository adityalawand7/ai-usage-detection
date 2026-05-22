def generate_report(result):

    lines = []

    lines.append("=" * 60)
    lines.append(f"Company: {result['url']}")
    lines.append("=" * 60)

    lines.append(f"\nAI Usage Detected: {result['verdict']}")
    lines.append(f"Confidence: {result['confidence']}")

    evidence = result["evidence"]

    if not evidence:
        lines.append("\nNo evidence found.")
        return "\n".join(lines)

    lines.append("\nTop Evidence:\n")

    # sort by similarity
    sorted_evidence = sorted(
        evidence,
        key=lambda x: x.similarity,
        reverse=True
    )

    for i, e in enumerate(sorted_evidence[:8], start=1):

        lines.append("-" * 60)
        lines.append(f"[{i}] Type: {e.category}")
        lines.append(f"URL: {e.url}")
        lines.append(f"Confidence Score: {round(e.similarity, 3)}")
        lines.append(f"Evidence:")
        lines.append(e.text[:300])
        lines.append("")

    return "\n".join(lines)