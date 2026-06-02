"""
General-purpose educational article/blog scraper
Extracts headings, paragraphs, and list items from articles and saves them to a text file.

Usage:
    python article_scraper.py <url> [output_file]

Examples:
    python article_scraper.py https://example.com/article
    python article_scraper.py https://example.com/article my_notes.txt
"""

import sys
import re
from datetime import datetime
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Missing dependencies. Install them with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


# Tags that typically contain educational content in articles
CONTENT_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]

# Tags/classes commonly used for non-content areas to skip
NOISE_SELECTORS = [
    "nav", "header", "footer", "aside",
    ".sidebar", ".advertisement", ".ad", ".cookie",
    ".comment", ".related", ".newsletter", ".popup",
    "[class*='social']", "[class*='share']", "[class*='promo']",
]


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a webpage and return a BeautifulSoup object."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to {url}. Check the URL and your internet connection.")
    except requests.exceptions.Timeout:
        print("Request timed out. The site may be slow or unreachable.")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None


def remove_noise(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove non-content elements (nav, footer, ads, etc.)."""
    for selector in NOISE_SELECTORS:
        for element in soup.select(selector):
            element.decompose()
    return soup


def find_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Try to isolate the main article content area."""
    # Common article container selectors, in priority order
    candidates = [
        "article",
        "main",
        "[role='main']",
        ".post-content", ".entry-content", ".article-content",
        ".article-body", ".post-body", ".content-body",
        "#content", "#main-content", "#article",
    ]
    for selector in candidates:
        element = soup.select_one(selector)
        if element:
            return element
    # Fall back to the full body
    return soup.find("body") or soup


def extract_points(content) -> list[dict]:
    """
    Extract educational points from the content area.
    Returns a list of dicts with 'type' and 'text' keys.
    """
    points = []
    seen = set()  # Deduplicate

    for tag in content.find_all(CONTENT_TAGS):
        text = tag.get_text(separator=" ", strip=True)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Skip empty, duplicate, or very short strings
        if not text or len(text) < 20 or text in seen:
            continue

        # Skip lines that look like nav/UI (very short + no sentence structure)
        if len(text) < 40 and not any(c in text for c in ".!?,"):
            # Allow headings through even if short
            if tag.name not in ("h1", "h2", "h3", "h4", "h5", "h6"):
                continue

        seen.add(text)
        points.append({"type": tag.name, "text": text})

    return points


def format_output(url: str, points: list[dict]) -> str:
    """Format extracted points into a readable text file."""
    lines = []
    domain = urlparse(url).netloc
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("=" * 70)
    lines.append("EDUCATIONAL POINTS EXTRACTED")
    lines.append("=" * 70)
    lines.append(f"Source : {url}")
    lines.append(f"Domain : {domain}")
    lines.append(f"Scraped: {timestamp}")
    lines.append(f"Points : {len(points)}")
    lines.append("=" * 70)
    lines.append("")

    current_section = None

    for point in points:
        tag = point["type"]
        text = point["text"]

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            indent = "  " * (level - 1)
            lines.append("")
            lines.append(f"{indent}{'#' * level} {text}")
            lines.append("")
            current_section = text
        elif tag == "li":
            lines.append(f"  • {text}")
        else:  # p
            lines.append(text)
            lines.append("")

    lines.append("")
    lines.append("-" * 70)
    lines.append(f"End of extraction — {len(points)} points captured from {domain}")

    return "\n".join(lines)


def scrape(url: str, output_file: str) -> None:
    """Main scraping pipeline."""
    print(f"Fetching: {url}")
    soup = fetch_page(url)
    if not soup:
        sys.exit(1)

    print("Removing noise (ads, navbars, footers)...")
    soup = remove_noise(soup)

    print("Locating main content...")
    content = find_main_content(soup)

    print("Extracting educational points...")
    points = extract_points(content)

    if not points:
        print("No content found. The site may block scrapers or use JavaScript rendering.")
        sys.exit(1)

    print(f"Found {len(points)} points.")

    output = format_output(url, points)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Saved to: {output_file}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = sys.argv[1]

    # Auto-generate output filename from domain + timestamp if not provided
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        domain = urlparse(url).netloc.replace("www.", "").replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{domain}_{timestamp}.txt"

    scrape(url, output_file)


if __name__ == "__main__":
    main()