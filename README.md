# Website Scraper

This repository contains a Python scraper that extracts internal links from a target page and a workflow for extracting text from those pages using Trafilatura.

## What it does

- `scraper.py` fetches the page configured in `base_url`
- it extracts internal links and writes them to `urls.txt`
- you can then run Trafilatura to download and extract text from each URL

## Setup

Install Python dependencies:

```bash
python3 -m pip install requests beautifulsoup4
```

Install Trafilatura separately for text extraction:

```bash
python3 -m pip install trafilatura
```

### Install as a package

Create and activate a virtual environment, then install the project locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

After installation, use the package console scripts:

```bash
website-scraper --base-url https://example.com/path
```

or:

```bash
website-scraper-background
```

## Run the scraper

Edit `scraper.py` and set `base_url` to the page you want to crawl, or use the new launcher below.

Run the scraper directly:

```bash
python3 scraper.py --base-url https://example.com/path
```

That creates `urls.txt` with the unique internal links found on the page.

## Run the scraper in the background

Use `run_scraper.py` to prompt for a website and start the scraper as a background job:

```bash
python3 run_scraper.py
```

It will ask for the desired website URL and then launch the scrape in the background, appending output to `scrape.log`.

## Extract text with Trafilatura

Once `urls.txt` is ready, run:

```bash
trafilatura -i urls.txt -o extracted_pages
```

This downloads and extracts text for each URL into the `extracted_pages/` folder.

For visible progress and a single worker:

```bash
trafilatura --parallel 1 -v -i urls.txt -o extracted_pages
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
