from .crawler import fetch_pages
from .semantic import analyze_chunks
from .fingerprints import detect_fingerprints
from .reasoning import company_reasoning
from .evidence import Evidence

from bs4 import BeautifulSoup


# --------------------------------
# CLEAN TEXT EXTRACTION
# --------------------------------
def extract_visible_text(html):

    soup = BeautifulSoup(html, "html.parser")

    # remove junk elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "img",
        "footer",
        "nav",
        "header"
    ]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # normalize whitespace
    text = " ".join(text.split())

    return text


# --------------------------------
# CHUNKING
# --------------------------------
def chunk_text(text, size=400):

    return [
        text[i:i+size]
        for i in range(0, len(text), size)
        if len(text[i:i+size].strip()) > 50
    ]


# --------------------------------
# MAIN ENGINE
# --------------------------------
def analyze_company(url):

    print(f"Analyzing {url}")

    pages = fetch_pages(url)

    evidence = []

    for page in pages:

        html = page["content"]
        scripts = page.get("scripts", [])
        network = page.get("network", [])
        page_url = page["url"]

        clean_text = extract_visible_text(html)

        chunks = chunk_text(clean_text)

        if not chunks:
            continue

        # -------- SEMANTIC ANALYSIS --------
        semantic_results = analyze_chunks(chunks)

        for result in semantic_results:

            evidence.append(
                Evidence(
                    url=page_url,

                    page_type="semantic",

                    text=result["text"][:250],

                    similarity=float(result["similarity"]),

                    strength=result["strength"],

                    category=result["category"]
                )
            )

        # -------- FINGERPRINT ANALYSIS --------
        combined_content = (
            html
            + " "
            + " ".join(scripts)
            + " "
            + " ".join(network)
        )

        techs = detect_fingerprints(
            combined_content
        )

        for tech in techs:
            evidence.append(
                Evidence(
                    url=page_url,
                    page_type="technical",
                    text=f"Detected {tech}",
                    similarity=1.0,
                    strength="strong",
                    category="technical_ai"
                )
            )

    verdict, confidence, role = company_reasoning(
        evidence
    )

    return {
        "url": url,
        "verdict": verdict,
        "confidence": confidence,
        "role": role,
        "evidence": evidence
    }