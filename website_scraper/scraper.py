"""Extract internal links from a target page and write them to urls.txt.

This module is used by the package entry point `website-scraper`.
"""

import argparse
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry

DEFAULT_BASE_URL = None
DEFAULT_TIMEOUT = 15
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1
DEFAULT_VERBOSE = False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "DNT": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
}

FALLBACK_USER_AGENTS = [
    HEADERS["User-Agent"],
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
    ),
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


def make_session(
    user_agent: str | None = None,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
) -> requests.Session:
    """Create a requests Session with browser-like headers and automatic retries."""
    session = requests.Session()
    session.trust_env = False

    merged_headers = {**HEADERS}
    if user_agent:
        merged_headers["User-Agent"] = user_agent
    session.headers.update(merged_headers)

    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        raise_on_status=False,
        raise_on_redirect=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def try_with_fallback_user_agent(
    base_url: str,
    timeout: int,
    retries: int,
    backoff: float,
    verbose: bool = False,
) -> requests.Response | None:
    """Try fallback User-Agents until one succeeds (non-403)."""
    for user_agent in tqdm(FALLBACK_USER_AGENTS, desc="Trying user agents", unit="agent"):
        if verbose:
            print(f"  → trying: {user_agent[:60]}...")

        session = make_session(user_agent=user_agent, retries=retries, backoff=backoff)
        session.headers.update({"Referer": base_url})

        try:
            response = session.get(base_url, timeout=timeout)
            if response.status_code == 403:
                if verbose:
                    print("  ✗ blocked (403)")
                continue

            response.raise_for_status()
            if verbose:
                print(f"  ✓ success (status {response.status_code})")
            return response

        except requests.HTTPError:
            if verbose:
                print("  ✗ HTTP error")
            continue
        except requests.RequestException as e:
            if verbose:
                print(f"  ✗ request error: {e}")
            continue

    return None


def collect_urls(
    base_url: str,
    output_file: str = "urls.txt",
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    user_agent: str | None = None,
    verbose: bool = DEFAULT_VERBOSE,
) -> int:
    """Fetch the target page, extract internal links, and save them to a file."""
    domain = urlparse(base_url).netloc
    session = make_session(user_agent=user_agent, retries=retries, backoff=backoff)

    if verbose:
        print(f"Requesting {base_url}")
        print(f"  timeout={timeout}s  retries={retries}  backoff={backoff}")
        if user_agent:
            print(f"  User-Agent override: {user_agent}")

    response = None
    try:
        session.headers.update({"Referer": base_url})
        response = session.get(base_url, timeout=timeout)
        response.raise_for_status()

    except requests.HTTPError as e:
        if response is not None and response.status_code == 403 and not user_agent:
            print("Initial request blocked (403) — trying fallback user agents...")
            response = try_with_fallback_user_agent(base_url, timeout, retries, backoff, verbose)
            if response is None:
                print("\nError: all user agents blocked.")
                print("Hint: the site may use Cloudflare or TLS fingerprinting.")
                print("      Try fetch_unc.py (Playwright) instead.")
                sys.exit(1)
        else:
            status = response.status_code if response is not None else "unknown"
            print(f"Error: HTTP {status}: {e}")
            sys.exit(1)

    except requests.Timeout:
        print(f"Error: request timed out after {timeout}s")
        sys.exit(1)
    except requests.ConnectionError as e:
        print(f"Error: connection failed: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error: request failed: {e}")
        sys.exit(1)

    preview = response.text[:600].lower()
    if any(phrase in preview for phrase in ("access denied", "captcha", "not authorized")):
        print("Warning: response looks like a bot-block page (access denied / captcha).")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")
    all_anchors = soup.find_all("a", href=True)
    visited = set()

    with open(output_file, "w", encoding="utf-8") as f:
        for anchor in tqdm(all_anchors, desc="Extracting links", unit="link"):
            full_url = urljoin(base_url, anchor["href"])
            if urlparse(full_url).netloc == domain and full_url not in visited:
                f.write(full_url + "\n")
                visited.add(full_url)

    return len(visited)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract internal links from a target page and write them to urls.txt."
    )
    parser.add_argument("--base-url", required=True, help="Target page to scrape")
    parser.add_argument("--output-file", default="urls.txt", help="Output file for extracted URLs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_RETRIES, help="Retry attempts for transient failures")
    parser.add_argument("--backoff", type=float, default=DEFAULT_BACKOFF, help="Backoff factor between retries")
    parser.add_argument("--user-agent", help="Override the default User-Agent header")
    parser.add_argument("--verbose", action="store_true", help="Print detailed diagnostics")
    args = parser.parse_args()

    count = collect_urls(
        args.base_url,
        args.output_file,
        timeout=args.timeout,
        retries=args.max_retries,
        backoff=args.backoff,
        user_agent=args.user_agent,
        verbose=args.verbose,
    )
    print(f"\nDone — wrote {count} URLs to {args.output_file}")
    print("Next step: trafilatura --parallel 1 -v -i urls.txt -o extracted_pages")


if __name__ == "__main__":
    main()
