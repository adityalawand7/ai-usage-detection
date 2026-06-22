from playwright.sync_api import sync_playwright
from urllib.parse import urlparse


MAX_PAGES = 12


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

    anchors = page.eval_on_selector_all(
        "a",
        "elements => elements.map(e => e.href)"
    )

    base_domain = urlparse(base_url).netloc

    root_domain = ".".join(
        base_domain.split(".")[-2:]
    )

    # Check if the site being analyzed IS a job board
    clean_domain = base_domain.replace("www.", "")
    is_job_board_site = any(jb in clean_domain for jb in JOB_BOARD_DOMAINS)

    filtered = []

    for link in anchors:

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

        # --------------------------------
        # BAD URL FILTERS
        # --------------------------------

        BAD_PATTERNS = [
            "search?",
            "setprefs",
            "accounts.google",
            "maps.google",
            "policies.google",
            "/preferences",
            "/advanced_search",
            "support.google",
            "privacy",
            "terms",
            "signin",
            "login",
        ]

        # skip noisy pages, but keep essential career pages even if they contain 'search'
        if any(bad in link.lower() for bad in BAD_PATTERNS):
            is_essential_career = any(word in link.lower() for word in ["job", "career", "opening"])
            is_blocked_anyway = any(blocked in link.lower() for blocked in ["login", "signin", "privacy", "terms", "google"])
            if not is_essential_career or is_blocked_anyway:
                continue

        filtered.append(link)

    IMPORTANT_PATTERNS = [
        "ai",
        "artificial-intelligence",
        "machine-learning",
        "product",
        "platform",
        "solution",
        "career",
        "careers",
        "job",
        "jobs",
        "join-us",
        "join",
        "work-with-us",
        "opportunities",
    ]
    unique_links = list(
        dict.fromkeys(filtered)
    )

    priority_links = []
    other_links = []

    for link in unique_links:
        if any(pattern in link.lower() for pattern in IMPORTANT_PATTERNS):
            priority_links.append(link)
        else:
            other_links.append(link)

    return (
        priority_links
        + other_links
    )[:MAX_PAGES]


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

        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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
        to_visit = [base_url]
        visited = set()
        crawled_count = 0

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

            for cl in career_links:
                if cl not in to_visit:
                    to_visit.append(cl)

        def prioritize_queue(queue, visited_set):
            """Sort queue to crawl job details, career listing pages first."""
            job_details = []
            career_landings = []
            ai_pages = []
            others = []

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

            for item in queue:
                if item in visited_set:
                    continue
                parsed = urlparse(item)
                item_lower = item.lower()

                # Check if it is an external ATS job or internal job detail
                is_ats = any(ats in parsed.netloc for ats in ALLOWED_ATS_DOMAINS)
                is_job_detail = is_ats or (
                    any(p in parsed.path.lower() for p in ["/job/R-", "/jobs/R-", "/job/", "/jobs/", "/vacancy/", "/opening/"])
                    and not any(p == parsed.path.lower().rstrip("/") for p in ["/job", "/jobs", "/careers", "/career"])
                )

                if is_job_detail:
                    job_details.append(item)
                elif any(word in item_lower for word in ["career", "jobs", "join"]):
                    career_landings.append(item)
                elif any(word in item_lower for word in ["ai", "artificial-intelligence", "machine-learning"]):
                    ai_pages.append(item)
                else:
                    others.append(item)

            # Recombine and keep unique elements while preserving order
            seen = set()
            result = []
            for item in (job_details + career_landings + ai_pages + others):
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result

        # --------------------------------
        # CRAWL LOOP
        # --------------------------------
        while to_visit and crawled_count < MAX_PAGES:
            to_visit = prioritize_queue(to_visit, visited)
            if not to_visit:
                break

            link = to_visit.pop(0)
            if link in visited:
                continue

            # Skip the careers/jobs page on job board platforms entirely
            if is_job_board_site:
                if any(kw in link.lower() for kw in ["career", "careers", "jobs", "job", "join", "opportunities", "work-with-us"]):
                    print(f"[Crawler] Skipping careers/job link on job board: {link}")
                    visited.add(link)
                    continue

            visited.add(link)

            try:
                if task:
                    progress = 15 + int((crawled_count / MAX_PAGES) * 20)
                    task.update_state(
                        state="PROGRESS",
                        meta={
                            "step": f"Crawling website: page {crawled_count+1} of {MAX_PAGES} ({urlparse(link).path or '/'})",
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
                            input_element.fill("AI")

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

                            clicked_submit = False
                            for sel in submit_selectors:
                                btn = page.locator(sel).first
                                try:
                                    btn.wait_for(state="visible", timeout=1500)
                                    if btn.is_enabled():
                                        btn.click()
                                        clicked_submit = True
                                        print(f"[Crawler Automation] Clicked submit button: {sel}")
                                        break
                                except Exception:
                                    continue

                            if not clicked_submit:
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
                for dl in discovered:
                    if dl in visited or dl in to_visit:
                        continue
                    to_visit.append(dl)

            except Exception as e:
                print(f"[Crawler] Failed {link}: {e}")

        browser.close()

    return pages