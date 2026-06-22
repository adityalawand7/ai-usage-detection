from .crawler import fetch_pages
from .semantic import analyze_chunks
from .fingerprints import detect_fingerprints
from .reasoning import company_reasoning
from .evidence import Evidence, EvidenceGraph
from .summary import generate_summary
from .ai_categories import AI_CATEGORIES

import re
from bs4 import BeautifulSoup


# --------------------------------
# DOM-AWARE CONTENT EXTRACTION
# --------------------------------
def extract_dom_chunks(html, min_length=40, max_length=500):
    soup = BeautifulSoup(html, "html.parser")

    # remove noise elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "img",
        "footer",
        "nav",
        "header",
        "form"
    ]):
        tag.decompose()

    chunks = []

    # extract natural content block tags
    content_tags = soup.find_all([
        "p", "h1", "h2", "h3", "h4", "h5", "h6",
        "li", "blockquote", "td", "pre"
    ])

    current_chunk = ""
    sentence_endings = re.compile(
        r'(?<!\b(?:eg|ie|vs|co)\.)(?<!\b(?:ltd|inc)\.)(?<!\bcorp\.)(?<=[.!?])\s+'
    )

    for tag in content_tags:
        text = " ".join(tag.get_text().split()).strip()
        if not text:
            continue

        # If a single element is too long, split it by sentence boundaries
        if len(text) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            sentences = sentence_endings.split(text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) >= min_length:
                    chunks.append(sentence)
            continue

        # Build chunks up to max_length using HTML layout boundaries
        if len(current_chunk) + len(text) > max_length:
            if len(current_chunk) >= min_length:
                chunks.append(current_chunk)
            current_chunk = text
        else:
            current_chunk = (
                f"{current_chunk} | {text}"
                if current_chunk
                else text
            )

    if current_chunk and len(current_chunk) >= min_length:
        chunks.append(current_chunk)

    return chunks


# --------------------------------
# CAPABILITY DETECTION
# --------------------------------
def detect_capabilities(evidence_list, combined_content):
    detected = set()
    combined_lower = combined_content.lower()

    # Match predefined category patterns in text/code content
    for category, keywords in AI_CATEGORIES.items():
        for kw in keywords:
            if kw in combined_lower:
                detected.add(category)
                break

    # Match in individual evidence text
    for e in evidence_list:
        text_lower = e.text.lower()
        for category, keywords in AI_CATEGORIES.items():
            for kw in keywords:
                if kw in text_lower:
                    detected.add(category)
                    break

    return list(detected)


# Keywords that MUST appear in a chunk for career_ai classification.
# Prevents generic careers page boilerplate (benefits, equal opportunity, etc.)
# from being falsely flagged as AI hiring evidence.
CAREER_AI_REQUIRED_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "neural network", "data science", "nlp", "natural language",
    "computer vision", "llm", "large language", "generative ai",
    "pytorch", "tensorflow", "transformers", "model training",
    "prompt engineering", "ai engineer", "ml engineer",
    "ai researcher", "ml researcher", "ai architect",
    "reinforcement learning", "embeddings", "vector database",
    "foundation model", "fine-tun", "hugging face", "rag",
]

# Job board platforms that HOST other companies' listings.
# Career evidence from these sites needs extra validation.
JOB_BOARD_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "wellfound.com",
]

# Regex: detects chunks that are job listings FOR OTHER COMPANIES
# e.g. "Senior AI Engineer at Google", "ML Lead at OpenAI 1 day ago"
_OTHER_COMPANY_JOB_PATTERN = re.compile(
    r'\b(?:at|@)\s+[A-Z][\w\s&,\.]+(?:\d+\s+(?:day|hour|week|month)s?\s+ago|\||$)',
    re.IGNORECASE
)


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

    pages = fetch_pages(url, task=task)

    if task:
        task.update_state(
            state="PROGRESS",
            meta={
                "step": "Extracting website content",
                "progress": 35
            }
        )

    evidence_graph = EvidenceGraph()
    global_seen_chunks = set()

    for page in pages:
        html = page["content"]
        scripts = page.get("scripts", [])
        network = page.get("network", [])
        page_url = page["url"]
        rendered_text = page.get("rendered_text", "")

        # DOM-aware structural extraction
        chunks = extract_dom_chunks(html)

        # Supplement with rendered text chunks if DOM is sparse (e.g. Workday SPA portals)
        if rendered_text and len(chunks) < 5:
            # Split rendered text into natural line-based chunks
            lines = [l.strip() for l in rendered_text.split("\n") if l.strip()]
            # Combine lines into groups of up to 400 chars
            current = ""
            for line in lines:
                if len(current) + len(line) > 400:
                    if len(current) >= 30:
                        chunks.append(current)
                    current = line
                else:
                    current = f"{current} | {line}" if current else line
            if current and len(current) >= 30:
                chunks.append(current)

        # Filter duplicates globally to bypass nav, footers, headers
        unique_chunks = []
        for chunk in chunks:
            normalized = chunk.lower().strip()
            if normalized not in global_seen_chunks:
                global_seen_chunks.add(normalized)
                unique_chunks.append(chunk)

        if not unique_chunks:
            continue

        if task:
            task.update_state(
                state="PROGRESS",
                meta={
                    "step": f"Running semantic AI analysis ({page_url})",
                    "progress": 55
                }
            )

        # -------- SEMANTIC ANALYSIS --------
        semantic_results = analyze_chunks(unique_chunks)

        # Is this page from a job board platform?
        is_job_board_page = any(jb in page_url for jb in JOB_BOARD_DOMAINS)

        for result in semantic_results:
            category = result["category"]
            text_lower = result["text"].lower()

            # career_ai requires both a higher similarity AND an actual AI keyword
            if category == "career_ai":
                if result["similarity"] < 0.50:
                    continue
                if not any(kw in text_lower for kw in CAREER_AI_REQUIRED_KEYWORDS):
                    continue

                # On job board pages, reject chunks that look like listings
                # for OTHER companies (e.g. "AI Engineer at Google 2 days ago")
                if is_job_board_page and _OTHER_COMPANY_JOB_PATTERN.search(result["text"]):
                    print(f"[Engine] Skipping third-party job listing on job board: {result['text'][:80]}")
                    continue

            evidence_graph.add(
                Evidence(
                    url=page_url,
                    page_type="semantic",
                    text=result["text"],
                    similarity=float(result["similarity"]),
                    strength=result["strength"],
                    category=category
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

        techs = detect_fingerprints(combined_content)

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

    # Perform scoring reasoning
    (
        verdict,
        confidence,
        role,
        total_score,
        score_breakdown
    ) = company_reasoning(evidence_graph.all())
    
    # Generate executive summary
    summary = generate_summary(
        role,
        confidence,
        {
            "semantic": len(evidence_graph.semantic),
            "technical": len(evidence_graph.technical),
            "behavioral": len(evidence_graph.behavioral),
            "organizational": len(evidence_graph.organizational)
        },
        evidence_list=evidence_graph.all()
    )

    # Compile aggregated text contents for capability tag detection
    # Compile aggregated clean text content for capability tag detection
    all_clean_content = " | ".join(list(global_seen_chunks))

    capabilities = detect_capabilities(
        evidence_graph.all(),
        all_clean_content
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
        "total_score": total_score,
        "score_breakdown": score_breakdown,
        "evidence": evidence_graph.all(),
        "maturity_score": min(round(total_score), 100),
        "evidence_summary": {
            "semantic": len(evidence_graph.semantic),
            "technical": len(evidence_graph.technical),
            "behavioral": len(evidence_graph.behavioral),
            "organizational": len(evidence_graph.organizational)
        },
        "capabilities": capabilities
    }