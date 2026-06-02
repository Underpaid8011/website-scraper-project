import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

base_url = 'https://lsc.cornell.edu/how-to-study/'  # Change this to your target site
domain = urlparse(base_url).netloc
visited = set()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": base_url,
}

try:
    response = requests.get(base_url, headers=headers, timeout=15)
    response.raise_for_status()
except requests.Timeout:
    print(f"Error: request timed out for {base_url}")
    exit(1)
except requests.ConnectionError as e:
    print(f"Error: connection failed: {e}")
    exit(1)
except requests.HTTPError as e:
    print(f"Error: HTTP error {response.status_code}: {e}")
    exit(1)

text_preview = response.text[:600].lower()
if "access denied" in text_preview or "captcha" in text_preview or "not authorized" in text_preview:
    print("Warning: the page looks like a block page or bot protection.")
    exit(1)

soup = BeautifulSoup(response.text, 'html.parser')

with open('urls.txt', 'w') as f:
    for link in soup.find_all('a', href=True):
        full_url = urljoin(base_url, link['href'])
        if domain in full_url and full_url not in visited:
            f.write(full_url + '\n')
            visited.add(full_url)

print(f"Wrote {len(visited)} URLs to urls.txt")