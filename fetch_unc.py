"""fetch_unc.py

Uses a real Chromium browser (via Playwright) to load a page and extract
internal links into urls.txt. Use this instead of scraper.py for sites
that block plain HTTP requests (e.g. Cloudflare, WAF-protected sites).

Usage:
    python3 fetch_unc.py
    python3 fetch_unc.py --base-url https://example.com/page/

Requirements:
    pip install playwright beautifulsoup4 tqdm
    playwright install chromium
"""

import argparse
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tqdm import tqdm

# ── defaults ──────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "https://learningcenter.unc.edu/tips-and-tools/the-study-cycle/"
DEFAULT_OUTPUT   = "urls.txt"
DEFAULT_PARALLEL = 4  # trafilatura parallel workers suggested in next-step hint


def fetch_page_html(url: str) -> str:
    """Launch a headless Chromium browser, load the page, and return its HTML.

    Using a real browser means the request passes TLS fingerprinting and
    JavaScript challenges that block plain requests.Session() calls.
    """
    print(f"Launching headless browser for: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # wait_until="networkidle" ensures JS-rendered content is fully loaded
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()

    print("Page loaded successfully.")
    return html


def extract_internal_links(html: str, base_url: str) -> list[str]:
    """Parse HTML and return a deduplicated list of internal links.

    A link is considered internal if it shares the same domain as base_url.
    """
    domain      = urlparse(base_url).netloc
    soup        = BeautifulSoup(html, "html.parser")
    all_anchors = soup.find_all("a", href=True)

    seen  = set()
    links = []

    # tqdm wraps the loop and draws a progress bar in the terminal
    for anchor in tqdm(all_anchors, desc="Scanning links", unit="link"):
        full_url = urljoin(base_url, anchor["href"])

        # keep only links that belong to the same domain and haven't been seen
        if domain in full_url and full_url not in seen:
            links.append(full_url)
            seen.add(full_url)

    return links


def deduplicate_and_sort(links: list[str]) -> list[str]:
    """Sort and deduplicate the link list.

    Deduplication already happens during extraction, but this catches any
    edge cases (e.g. trailing-slash variants) and sorts for consistent output.
    Fewer unique URLs = less work for trafilatura.
    """
    deduped = sorted(set(links))
    removed = len(links) - len(deduped)
    if removed:
        print(f"Removed {removed} duplicate URL(s) during sort.")
    return deduped


def write_urls(links: list[str], output_file: str) -> None:
    """Write each URL on its own line to the output file."""
    with open(output_file, "w", encoding="utf-8") as f:
        for url in tqdm(links, desc="Writing urls.txt", unit="url"):
            f.write(url + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a page via headless browser and extract internal links."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="URL of the page to scrape (default: UNC study cycle page)",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT,
        help="File to write extracted URLs to (default: urls.txt)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=DEFAULT_PARALLEL,
        help="Number of parallel workers to suggest for trafilatura (default: 4)",
    )
    args = parser.parse_args()

    # Step 1: load the page with a real browser
    html = fetch_page_html(args.base_url)

    # Step 2: pull out all internal links
    links = extract_internal_links(html, args.base_url)

    # Step 3: deduplicate and sort before writing — fewer URLs = faster trafilatura
    links = deduplicate_and_sort(links)

    # Step 4: save to urls.txt (or custom output file)
    write_urls(links, args.output_file)

    print(f"\nDone — wrote {len(links)} URLs to {args.output_file}")
    print("\nNext steps:")
    print(f"  trafilatura --parallel {args.parallel} --no-comments --no-tables -i {args.output_file} -o extracted_pages")
    print(f"  cat extracted_pages/* > complete_website.txt")


if __name__ == "__main__":
    main()
