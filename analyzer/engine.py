from .crawler import fetch_pages
from .semantic import analyze_chunks
from .fingerprints import detect_fingerprints
from .reasoning import company_reasoning
from .evidence import Evidence, EvidenceGraph
from .summary import generate_summary

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
def analyze_company(url, task=None):

    print(f"Analyzing {url}")

    if task:
        task.update_state(
            state="PROGRESS",
            meta={
                "step": "Crawling website",
                "progress": 15
            }
        )

    pages = fetch_pages(url)

    if task:
        task.update_state(
            state="PROGRESS",
            meta={
                "step": "Extracting website content",
                "progress": 35
            }
        )

    evidence_graph = EvidenceGraph()

    for page in pages:

        html = page["content"]
        scripts = page.get("scripts", [])
        network = page.get("network", [])
        page_url = page["url"]

        clean_text = extract_visible_text(html)

        chunks = chunk_text(clean_text)

        if not chunks:
            continue

        if task:
            task.update_state(
                state="PROGRESS",
                meta={
                    "step": "Running semantic AI analysis",
                    "progress": 55
                }
            )

        # -------- SEMANTIC ANALYSIS --------
        semantic_results = analyze_chunks(chunks)

        for result in semantic_results:

            evidence_graph.add(
                Evidence(
                    url=page_url,

                    page_type="semantic",

                    text=result["text"][:250],

                    similarity=float(result["similarity"]),

                    strength=result["strength"],

                    category=result["category"]
                )
            )

        if task:
            task.update_state(
                state="PROGRESS",
                meta={
                    "step": "Detecting AI technologies",
                    "progress": 75
                }
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
            evidence_graph.add(
                Evidence(
                    url=page_url,
                    page_type="technical",
                    text=f"Detected {tech}",
                    similarity=1.0,
                    strength="strong",
                    category="technical_ai"
                )
            )
    
    if task:
        task.update_state(
            state="PROGRESS",
            meta={
                "step": "Generating intelligence report",
                "progress": 90
            }
        )

    verdict, confidence, role = company_reasoning(
        evidence_graph.all()
    )
    
    summary = generate_summary(
        role,
        confidence,
        {

            "semantic":
                len(evidence_graph.semantic),

            "technical":
                len(evidence_graph.technical),

            "behavioral":
                len(evidence_graph.behavioral),

            "organizational":
                len(evidence_graph.organizational)
        }
    )

    if task:
        task.update_state(
            state="PROGRESS",
            meta={
                "step": "Finalizing results",
                "progress": 100
            }
        )

    return {
        "url": url,
        "verdict": verdict,
        "confidence": confidence,
        "role": role,
        "summary": summary,
        "evidence": evidence_graph.all(),
        "evidence_summary": {

            "semantic":
                len(evidence_graph.semantic),

            "technical":
                len(evidence_graph.technical),

            "behavioral":
                len(evidence_graph.behavioral),

            "organizational":
                len(evidence_graph.organizational)
        }
    }