import argparse
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_BASE_URL = 'https://lsc.cornell.edu/how-to-study/'

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def collect_urls(base_url, output_file="urls.txt"):
    domain = urlparse(base_url).netloc
    visited = set()

    try:
        response = requests.get(base_url, headers={**headers, "Referer": base_url}, timeout=15)
        response.raise_for_status()
    except requests.Timeout:
        print(f"Error: request timed out for {base_url}")
        sys.exit(1)
    except requests.ConnectionError as e:
        print(f"Error: connection failed: {e}")
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"Error: HTTP error {response.status_code}: {e}")
        sys.exit(1)

    text_preview = response.text[:600].lower()
    if "access denied" in text_preview or "captcha" in text_preview or "not authorized" in text_preview:
        print("Warning: the page looks like a block page or bot protection.")
        sys.exit(1)

    soup = BeautifulSoup(response.text, 'html.parser')

    with open(output_file, 'w', encoding='utf-8') as f:
        for link in soup.find_all('a', href=True):
            full_url = urljoin(base_url, link['href'])
            if domain in full_url and full_url not in visited:
                f.write(full_url + '\n')
                visited.add(full_url)

    return len(visited)


def main():
    parser = argparse.ArgumentParser(description="Extract internal links from a target page and write them to urls.txt")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Target page to scrape")
    parser.add_argument("--output-file", default="urls.txt", help="Output file for the extracted URLs")
    args = parser.parse_args()

    count = collect_urls(args.base_url, args.output_file)
    print(f"Wrote {count} URLs to {args.output_file}")


if __name__ == "__main__":
    main()
