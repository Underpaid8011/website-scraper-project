# Website Scraper

This repository contains a Python scraper that extracts internal links from a target page and a workflow for extracting text from those pages using Trafilatura.

## What it does

- `scraper.py` fetches the page configured in `base_url`
- it extracts internal links and writes them to `urls.txt`
- you can then run Trafilatura to download and extract text from each URL

## Setup

Create and activate a virtual environment inside the project directory, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
```

If you only want the runtime dependencies without editable install, install them directly:

```bash
python3 -m pip install requests beautifulsoup4 tqdm
```

Install Trafilatura separately for text extraction:

```bash
python3 -m pip install trafilatura
```

If you want browser-based scraping for JS-heavy sites, install Playwright:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

Use `fetch_unc.py` for pages that block plain HTTP requests or require JavaScript rendering:

```bash
python3 fetch_unc.py --base-url https://example.com/path
```

## Run the scraper

You can run the scraper directly from the project directory with Python. `--base-url` is required:

```bash
python3 scraper.py --base-url https://example.com/path
```

If you installed the project in editable mode, you can also use the console script:

```bash
website-scraper --base-url https://example.com/path
```

Both commands create `urls.txt` with the unique internal links found on the page.

The scraper now retries transient failures and supports additional options:

```bash
python3 scraper.py --base-url https://example.com/path --timeout 20 --max-retries 5 --backoff 1.0
```

If a site still returns `403 Forbidden`, try a manual User-Agent override:

```bash
python3 scraper.py --base-url https://example.com/path --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
```

For diagnostics, enable verbose output to see retry and fallback attempts:

```bash
python3 scraper.py --base-url https://example.com/path --verbose
```

If the site still blocks plain requests, use the browser-based scraper instead:

```bash
python3 fetch_unc.py --base-url https://example.com/path
```

## Run the scraper in the background

Use `run_scraper.py` to prompt for a website and start the scraper as a background job:

```bash
python3 run_scraper.py
```

It will ask for the desired website URL and then launch the scrape in the background, appending output to `scrape.log`.

To check whether a scraper process is still running, use one of these commands:

```bash
pgrep -af scraper.py
```

or

```bash
ps -ef | grep '[s]craper.py'
```

## Extract text with Trafilatura

Before extracting, check how many URLs you have and remove duplicates.

```bash
wc -l urls.txt
head -20 urls.txt
sort -u urls.txt -o urls.txt
```

If you want to preserve original ordering while removing duplicates:

```bash
python3 - <<'PY'
from pathlib import Path
urls = Path('urls.txt').read_text().splitlines()
unique = list(dict.fromkeys(urls))
Path('urls.txt').write_text('\n'.join(unique) + '\n')
PY
```

Once `urls.txt` is ready, you can either use the standard Trafilatura CLI or the tqdm wrapper.

Standard CLI:

```bash
trafilatura -i urls.txt -o extracted_pages
```

With tqdm progress tracking and optional parallel extraction:

```bash
python3 run_trafilatura.py --input-file urls.txt --output-dir extracted_pages --parallel 4
```

To skip optional slow parsing and speed extraction further:

```bash
python3 run_trafilatura.py --input-file urls.txt --output-dir extracted_pages --parallel 4 --no-comments --no-tables
```

This downloads and extracts text for each URL into the `extracted_pages/` folder.

For visible progress with the CLI, use:

```bash
trafilatura --parallel 4 --no-comments --no-tables -v -i urls.txt -o extracted_pages
```

## Combine extracted text

After Trafilatura finishes, combine all extracted files into one text file:

```bash
cat extracted_pages/* > complete_website.txt
```

## Notes

- The scraper uses a browser-like `User-Agent` header to avoid simple blocking.
- To scrape a different page, edit the `base_url` value at the top of `scraper.py` and rerun.
- Generated files such as `urls.txt`, `complete_website.txt`, and `extracted_pages/` are ignored by `.gitignore`.
- If a page is blocked, `scraper.py` will print an error and stop.
- If Trafilatura is interrupted with `Ctrl+C`, rerun the same command to continue.
