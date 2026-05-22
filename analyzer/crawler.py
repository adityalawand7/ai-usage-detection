from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse


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

    # unique links
    return list(dict.fromkeys(filtered))[:MAX_PAGES]


# --------------------------------
# EXTRACT JS
# --------------------------------

def extract_scripts(page, base_url):

    scripts = page.eval_on_selector_all(
        "script",
        """
        elements => elements.map(e => ({
            src: e.src,
            content: e.innerText
        }))
        """
    )

    js_content = []

    for script in scripts:

        # inline JS
        if script["content"]:
            js_content.append(script["content"])

        # external JS URL
        if script["src"]:
            js_content.append(script["src"])

    return js_content


# --------------------------------
# MAIN CRAWLER
# --------------------------------

def fetch_pages(base_url):

    pages = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        # block heavy assets
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

        # open homepage
        page.goto(base_url, timeout=30000)

        links = discover_links(page, base_url)

        if base_url not in links:
            links.insert(0, base_url)

        # crawl discovered pages
        for link in links:

            try:

                print(f"[Crawler] Visiting {link}")

                page.goto(link, timeout=30000)

                html = page.content()

                scripts = extract_scripts(
                    page,
                    base_url
                )

                pages.append({
                    "url": link,
                    "content": html,
                    "scripts": scripts
                })

            except Exception as e:

                print(f"[Crawler] Failed {link}: {e}")

        browser.close()

    return pages