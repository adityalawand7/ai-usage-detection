from playwright.sync_api import sync_playwright
from urllib.parse import urlparse


MAX_PAGES = 8


# --------------------------------
# DISCOVER INTERNAL LINKS
# --------------------------------

def discover_links(page, base_url):

    anchors = page.eval_on_selector_all(
        "a",
        "elements => elements.map(e => e.href)"
    )

    base_domain = urlparse(base_url).netloc

    filtered = []

    for link in anchors:

        if not link:
            continue

        parsed = urlparse(link)

        if parsed.netloc != base_domain:
            continue

        # skip junk files
        if any(
            link.endswith(ext)
            for ext in [
                ".jpg",
                ".png",
                ".pdf",
                ".zip",
                ".svg"
            ]
        ):
            continue

        filtered.append(link)

    return list(dict.fromkeys(filtered))[:MAX_PAGES]


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

def fetch_pages(base_url):

    pages = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

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
        # OPEN BASE URL
        # --------------------------------

        page.goto(base_url, timeout=30000)

        links = discover_links(page, base_url)

        if base_url not in links:
            links.insert(0, base_url)

        # --------------------------------
        # CRAWL PAGES
        # --------------------------------

        for link in links:

            try:

                print(f"[Crawler] Visiting {link}")

                network_requests.clear()

                page.goto(link, timeout=30000)

                page.wait_for_timeout(3000)

                html = page.content()

                scripts = extract_scripts(page)

                pages.append({

                    "url": link,

                    "content": html,

                    "scripts": scripts,

                    "network": list(set(network_requests))
                })

            except Exception as e:

                print(f"[Crawler] Failed {link}: {e}")

        browser.close()

    return pages