from playwright.sync_api import sync_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

MAX_PAGES = 8

AI_KEYWORDS = [
    "ai",
    "artificial",
    "intelligence",
    "machine-learning",
    "ml",
    "copilot",
    "automation",
    "platform",
    "developer",
    "docs",
    "api",
    "product",
    "technology",
]


def is_internal(base, link):
    return urlparse(link).netloc == urlparse(base).netloc


def score_link(link):
    link_lower = link.lower()
    return sum(1 for k in AI_KEYWORDS if k in link_lower)


def fetch_pages(base_url):

    visited = set()
    pages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.route(
            "**/*",
            lambda route: route.abort()
            if route.request.resource_type in ["image", "font", "media"]
            else route.continue_()
        )

        print(f"[Crawler] Visiting {base_url}")
        page.goto(base_url, timeout=30000)

        html = page.content()

        pages.append({
            "url": base_url,
            "content": html
        })

        visited.add(base_url)

        # -------- Extract Links --------
        soup = BeautifulSoup(html, "html.parser")

        links = set()

        for a in soup.find_all("a", href=True):
            link = urljoin(base_url, a["href"])

            if is_internal(base_url, link):
                links.add(link.split("#")[0])

        # -------- Score Links --------
        ranked_links = sorted(
            links,
            key=score_link,
            reverse=True
        )

        # -------- Crawl Top Links --------
        for link in ranked_links[:MAX_PAGES]:

            if link in visited:
                continue

            try:
                print(f"[Crawler] Visiting {link}")
                page.goto(link, timeout=20000)

                pages.append({
                    "url": link,
                    "content": page.content()
                })

                visited.add(link)

            except:
                pass

        browser.close()

    return pages