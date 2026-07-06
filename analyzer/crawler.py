from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import torch
from sentence_transformers.util import cos_sim
from .semantic import get_model


MAX_PAGES = 18

RELEVANT_CONCEPTS = [
    "Artificial intelligence products, machine learning capabilities, AI features, technology solutions, developers and engineering.",
    "Corporate about us page, company information, executive team, organization background.",
    "Company newsroom, official press announcements, product updates, corporate blogs.",
    "Careers, job listings, open roles, hiring engineering and product team.",
    "Privacy policy, terms of service, user data agreement, legal terms, security policy."
]

IRRELEVANT_CONCEPTS = [
    "Customer support help desk center, search articles, documentation, faq, password reset, help articles.",
    "Sign in, login portal, user settings, registration, subscribe, accounts, dashboard.",
    "Contact us form, address, phone number, sales inquiry.",
    "System status page, site updates, sitemap index, rss feed, accessibility statement."
]

_concept_embeddings = None
_irrelevant_embeddings = None

def get_concept_embeddings():
    global _concept_embeddings, _irrelevant_embeddings
    if _concept_embeddings is None:
        model = get_model()
        _concept_embeddings = model.encode(RELEVANT_CONCEPTS, convert_to_tensor=True)
        _irrelevant_embeddings = model.encode(IRRELEVANT_CONCEPTS, convert_to_tensor=True)
    return _concept_embeddings, _irrelevant_embeddings


# --------------------------------
# DISCOVER INTERNAL LINKS
# --------------------------------

# Platforms that HOST other companies' jobs — scraping their job listings
# would give false signals about the company being analyzed.
JOB_BOARD_DOMAINS = [
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "ziprecruiter.com",
    "monster.com",
    "simplyhired.com",
    "careerbuilder.com",
    "dice.com",
    "wellfound.com",  # AngelList
]

# URL path segments on job boards that lead to OTHER companies' job listings.
# /jobs/ as a prefix blocks ALL category feeds (e.g. /jobs/engineer-jobs, /jobs/search, etc.)
JOB_BOARD_LISTING_PATHS = [
    "/jobs/",       # Blocks ALL /jobs/* sub-pages on job board sites
    "/job/",
    "/job-detail/",
    "/viewjob",
    "/jk=",
    "/listing/",
]


def discover_links(page, base_url):

    # Extract anchors and innerText to form descriptions for AI ranking
    anchors = page.eval_on_selector_all(
        "a",
        """elements => elements.map(e => ({
            href: e.href,
            text: e.innerText || ""
        }))"""
    )

    base_domain = urlparse(base_url).netloc

    root_domain = ".".join(
        base_domain.split(".")[-2:]
    )

    # Check if the site being analyzed IS a job board
    clean_domain = base_domain.replace("www.", "")
    is_job_board_site = any(jb in clean_domain for jb in JOB_BOARD_DOMAINS)

    filtered = []

    for item in anchors:
        link = item["href"]
        text = item["text"].strip()

        if not link or not link.startswith(("http://", "https://")):
            continue

        parsed = urlparse(link)

        ALLOWED_ATS_DOMAINS = [
            "myworkdayjobs.com",
            "greenhouse.io",
            "lever.co",
            "bamboohr.com",
            "recruitee.com",
            "smartrecruiters.com",
            "workable.com",
            "ashbyhq.com"
        ]

        is_internal = root_domain in parsed.netloc
        is_ats = any(ats in parsed.netloc for ats in ALLOWED_ATS_DOMAINS)

        if not is_internal and not is_ats:
            continue

        # If this is a job board (e.g. LinkedIn), skip all career/job pages completely
        if is_job_board_site:
            if any(kw in link.lower() for kw in ["career", "careers", "jobs", "job", "join", "opportunities", "work-with-us"]):
                continue

        # skip junk files
        if any(
            link.endswith(ext)
            for ext in [".jpg", ".png", ".pdf", ".zip", ".svg"]
        ):
            continue

        filtered.append({"href": link, "text": text})

    # Deduplicate keeping the first occurrence
    seen_hrefs = set()
    unique_candidates = []
    for item in filtered:
        h = item["href"]
        if h not in seen_hrefs:
            seen_hrefs.add(h)
            unique_candidates.append(item)

    if not unique_candidates:
        return []

    # AI scoring using SentenceTransformer
    model = get_model()
    rel_embeds, irrel_embeds = get_concept_embeddings()

    descriptions = []
    for item in unique_candidates:
        parsed_link = urlparse(item["href"])
        path = parsed_link.path or "/"
        descriptions.append(f"Path: {path} | Anchor: {item['text']}")

    try:
        desc_embeddings = model.encode(descriptions, convert_to_tensor=True, show_progress_bar=False)
    except Exception as e:
        print(f"[Crawler AI Filter] Error encoding descriptions: {e}")
        # Default fallback: score careers highly and retain some order
        return [(item["href"], 0.5) for item in unique_candidates]

    scored_links = []
    for i, item in enumerate(unique_candidates):
        emb = desc_embeddings[i]

        # Calculate max similarity with concepts
        rel_sims = cos_sim(emb, rel_embeds)
        max_rel_sim = float(rel_sims.max())

        irrel_sims = cos_sim(emb, irrel_embeds)
        max_irrel_sim = float(irrel_sims.max())

        # If it is more relevant than irrelevant and passes minimum threshold
        if max_rel_sim > max_irrel_sim and max_rel_sim > 0.12:
            href = item["href"]
            scored_links.append((href, max_rel_sim))
            
            # Check if this is a career/jobs search page candidate
            href_lower = href.lower()
            if any(kw in href_lower for kw in ["search-results", "/search", "/jobs", "/careers"]):
                if "?" not in href:
                    scored_links.append((href + "?keywords=AI", max_rel_sim))
                    scored_links.append((href + "?q=AI", max_rel_sim))
        else:
            # print(f"[Crawler AI Filter] Discarded link: {item['href']} (rel: {max_rel_sim:.3f}, irrel: {max_irrel_sim:.3f})")
            pass

    return scored_links


# --------------------------------
# EXTRACT SCRIPTS
# --------------------------------

def extract_scripts(page):

    scripts = page.eval_on_selector_all(
        "script",
        """
        elements => elements.map(e => ({
            src: e.src,
            content: e.innerText
        }))
        """
    )

    collected = []

    for script in scripts:

        if script["src"]:
            collected.append(script["src"])

        if script["content"]:
            collected.append(script["content"])

    return collected


# --------------------------------
# MAIN CRAWLER
# --------------------------------

def fetch_pages(base_url, task=None):

    pages = []

    with sync_playwright() as p:

        browser = p.firefox.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()

        # --------------------------------
        # COLLECT NETWORK REQUESTS
        # --------------------------------

        network_requests = []

        def capture_request(request):

            url = request.url.lower()

            resource_type = request.resource_type

            # focus on APIs / XHR / fetch
            if resource_type in [
                "xhr",
                "fetch",
                "websocket"
            ]:

                network_requests.append(url)

        page.on(
            "request",
            capture_request
        )

        # --------------------------------
        # BLOCK HEAVY ASSETS
        # --------------------------------

        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in [
                "image",
                "font",
                "media"
            ]
            else route.continue_()
        )

        # --------------------------------
        # DYNAMIC LINK QUEUE INITIALIZATION
        # --------------------------------
        to_visit = [(base_url, 1.0)]
        visited = set()
        crawled_count = 0
        legal_crawled_count = 0

        # Guesses for career pages
        career_candidates = [
            "/careers",
            "/career",
            "/jobs",
            "/join-us",
            "/careers.html",
            "/about/careers",
        ]

        # Proactively guess common subdomains (e.g. jobs.example.com, careers.example.com)
        base_domain = urlparse(base_url).netloc
        clean_domain = base_domain.replace("www.", "")
        is_job_board_site = any(jb in clean_domain for jb in JOB_BOARD_DOMAINS)

        if not is_job_board_site:
            subdomain_candidates = [
                f"https://jobs.{clean_domain}",
                f"https://careers.{clean_domain}"
            ]

            # Add guessed paths/subdomains to to_visit right away
            career_links = []
            for path in career_candidates:
                career_links.append(base_url.rstrip("/") + path)
            for candidate in subdomain_candidates:
                career_links.append(candidate)

            # Seed search queries for Phenom, Workday, etc.
            search_queries = [
                "/careers?keywords=AI",
                "/careers?q=AI",
                "/jobs?q=AI",
                "/jobs?keywords=AI",
                "/us/en/search-results?keywords=AI",
                "/search-results?keywords=AI"
            ]
            for path in search_queries:
                career_links.append(base_url.rstrip("/") + path)

            # Also seed subdomain search query versions
            for candidate in subdomain_candidates:
                career_links.append(candidate.rstrip("/") + "/jobs?q=AI")
                career_links.append(candidate.rstrip("/") + "/careers?keywords=AI")
                career_links.append(candidate.rstrip("/") + "/us/en/search-results?keywords=AI")

            for cl in career_links:
                if not any(x[0] == cl for x in to_visit):
                    to_visit.append((cl, 0.85)) # Seed guessed careers with high priority

        # --------------------------------
        # CRAWL LOOP
        # --------------------------------
        while to_visit and crawled_count < MAX_PAGES:
            # Sort the queue dynamically by relevance score descending
            to_visit.sort(key=lambda x: x[1], reverse=True)
            link, current_score = to_visit.pop(0)

            if link in visited:
                continue

            # Skip the careers/jobs page on job board platforms entirely
            if is_job_board_site:
                if any(kw in link.lower() for kw in ["career", "careers", "jobs", "job", "join", "opportunities", "work-with-us"]):
                    print(f"[Crawler] Skipping careers/job link on job board: {link}")
                    visited.add(link)
                    continue

            # Cap legal/privacy/terms page crawling to a maximum of 1 page
            is_legal = any(word in link.lower() for word in ["privacy", "terms", "legal"])
            if is_legal:
                if legal_crawled_count >= 1:
                    print(f"[Crawler] Skipping legal/privacy page crawl (capped): {link}")
                    visited.add(link)
                    continue
                legal_crawled_count += 1
                print(f"[Crawler] Accessing legal/privacy page: {link}")

            visited.add(link)

            try:
                if task:
                    progress = 15 + int((crawled_count / MAX_PAGES) * 20)
                    task.update_state(
                        state="PROGRESS",
                        meta={
                            "step": f"Crawling website (page {crawled_count+1} of {MAX_PAGES})",
                            "progress": progress
                        }
                    )

                print(f"[Crawler] Visiting {link}")
                network_requests.clear()

                try:
                    # Allow slightly longer load timeout for dynamic career pages
                    page.goto(link, timeout=30000, wait_until="domcontentloaded")
                except Exception as e:
                    err_msg = str(e).lower()
                    if "interrupted" in err_msg or "redirect" in err_msg or "navigating" in err_msg:
                        print(f"[Crawler] Navigation redirected or interrupted for {link}. Proceeding on: {page.url}")
                    else:
                        raise e

                # Determine if page is a career landing page (but not a job detail page)
                parsed_link = urlparse(link)
                is_ats_domain = any(ats in parsed_link.netloc for ats in ["myworkdayjobs.com", "greenhouse.io", "lever.co", "ashbyhq.com"])
                is_detail = is_ats_domain or (
                    any(p in parsed_link.path.lower() for p in ["/job/R-", "/jobs/R-", "/job/", "/jobs/", "/vacancy/", "/opening/"])
                    and not any(p == parsed_link.path.lower().rstrip("/") for p in ["/job", "/jobs", "/careers", "/career"])
                )

                # Skip error pages / chrome-error immediately
                current_url = page.url
                if "chrome-error://" in current_url or "about:blank" in current_url:
                    print(f"[Crawler] Skipping error page for {link}")
                    continue

                # Detect 404 pages quickly by checking title/heading text
                try:
                    page_title = page.title()
                    if "404" in page_title or "not found" in page_title.lower() or "error" in page_title.lower():
                        print(f"[Crawler] Skipping 404/error page: {link} (title: {page_title})")
                        continue
                except Exception:
                    pass

                is_career_landing = not is_job_board_site and any(word in link.lower() for word in ["career", "job", "join"]) and not is_detail

                if is_career_landing:
                    try:
                        # Wait for any JS framework loading
                        page.wait_for_timeout(3000)

                        search_selectors = [
                            "input[id*='typehead' i]",
                            "input[placeholder*='search' i]",
                            "input[placeholder*='job' i]",
                            "input[placeholder*='keyword' i]",
                            "input[id*='search' i]",
                            "input[name*='keyword' i]",
                            "input[class*='search' i]",
                            "input[type='search']"
                        ]

                        input_element = None
                        for selector in search_selectors:
                            el = page.locator(selector).first
                            try:
                                el.wait_for(state="visible", timeout=5000)
                                if el.is_enabled():
                                    input_element = el
                                    break
                            except Exception:
                                continue

                        if input_element:
                            print(f"[Crawler Automation] Found search input on {link}. Searching for 'AI'...")
                            input_element.click()
                            # Select all and delete to clear existing text, then type with delay to trigger framework bindings
                            page.keyboard.press("Control+A")
                            page.keyboard.press("Backspace")
                            page.keyboard.type("AI", delay=150)

                            # Look for the search button and click it to submit
                            submit_selectors = [
                                "button[id*='search' i]",
                                "button[class*='search' i]",
                                "button[aria-label*='search' i]",
                                "a[class*='search' i]",
                                "input[type='submit']",
                                "#ph-search-backdrop",
                                "button[type='submit']"
                            ]

                            for sel in submit_selectors:
                                btn = page.locator(sel).first
                                try:
                                    btn.wait_for(state="visible", timeout=1500)
                                    if btn.is_enabled():
                                        btn.click()
                                        print(f"[Crawler Automation] Clicked submit button: {sel}")
                                        page.wait_for_timeout(1000)
                                        break
                                except Exception:
                                    continue

                            # Always press Enter to ensure submit triggers on frameworks that require it
                            page.keyboard.press("Enter")
                            print("[Crawler Automation] Pressed Enter to submit search")

                            # Wait for dynamic query results to populate
                            page.wait_for_timeout(10000)
                        else:
                            page.wait_for_timeout(3000)
                    except Exception as err:
                        print(f"[Crawler Automation] Failed to automate search on {link}: {err}")
                        page.wait_for_timeout(3000)
                else:
                    page.wait_for_timeout(500)

                html = page.content()
                scripts = extract_scripts(page)

                # Also capture fully rendered visible text (catches SPA/Workday job listings)
                try:
                    rendered_text = page.inner_text("body")
                except Exception:
                    rendered_text = ""

                pages.append({
                    "url": link,
                    "content": html,
                    "rendered_text": rendered_text,
                    "scripts": scripts,
                    "network": list(set(network_requests))
                })
                crawled_count += 1

                # Dynamic link discovery: find and add links from current page to to_visit
                discovered = discover_links(page, base_url)
                for dl, score in discovered:
                    if dl in visited:
                        continue
                    existing_idx = next((i for i, x in enumerate(to_visit) if x[0] == dl), None)
                    if existing_idx is not None:
                        # Keep the highest relevance score
                        if score > to_visit[existing_idx][1]:
                            to_visit[existing_idx] = (dl, score)
                    else:
                        to_visit.append((dl, score))

            except Exception as e:
                print(f"[Crawler] Failed {link}: {e}")

        browser.close()

    return pages