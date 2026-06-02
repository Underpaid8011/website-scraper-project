#!/usr/bin/env python3
"""Extract saved URLs with Trafilatura while showing a tqdm progress bar."""

import argparse
import concurrent.futures
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

import trafilatura
from tqdm import tqdm

DEFAULT_INPUT_FILE = "urls.txt"
DEFAULT_OUTPUT_DIR = "extracted_pages"
DEFAULT_NO_COMMENTS = False
DEFAULT_NO_TABLES = False

INVALID_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(url: str) -> str:
    """Create a safe filename from a URL."""
    parsed = urlparse(url)
    parts = [parsed.netloc]
    if parsed.path and parsed.path != "/":
        parts.append(parsed.path.strip("/"))
    if parsed.query:
        parts.append(hashlib.sha256(parsed.query.encode("utf-8")).hexdigest()[:8])

    raw_name = "_".join(parts)
    raw_name = INVALID_FILENAME_CHARS.sub("_", raw_name)
    raw_name = raw_name.strip("._-")
    if not raw_name:
        raw_name = hashlib.sha256(url.encode("utf-8")).hexdigest()
    if len(raw_name) > 180:
        raw_name = raw_name[:180]
    return f"{raw_name}.txt"


def extract_page(url: str, output_dir: Path, no_comments: bool, no_tables: bool) -> bool:
    try:
        html = trafilatura.fetch_url(url)
        if html is None:
            return False

        text = trafilatura.extract(
            html,
            url=url,
            output_format="txt",
            include_comments=not no_comments,
            include_tables=not no_tables,
        )
        if not text:
            return False

        output_path = output_dir / sanitize_filename(url)
        output_path.write_text(text, encoding="utf-8")
        return True
    except Exception:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Use Trafilatura to extract text from URLs with a tqdm progress bar."
    )
    parser.add_argument(
        "--input-file",
        default=DEFAULT_INPUT_FILE,
        help="File containing one URL per line.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where extracted text files will be written.",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of worker threads to use for fetching and extracting pages.",
    )
    parser.add_argument(
        "--dedupe",
        action="store_true",
        help="Remove duplicate URLs before extraction.",
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        default=DEFAULT_NO_COMMENTS,
        help="Drop comments from extracted pages.",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        default=DEFAULT_NO_TABLES,
        help="Drop tables from extracted pages.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    urls = [line.strip() for line in Path(args.input_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not urls:
        raise SystemExit(f"No URLs found in {args.input_file}")

    initial_count = len(urls)
    if args.dedupe:
        urls = list(dict.fromkeys(urls))
    print(f"Found {initial_count} URLs, extracting {len(urls)} unique pages.")

    success = 0
    failures = 0

    if args.parallel <= 1:
        for url in tqdm(urls, desc="Extracting pages", unit="page"):
            if extract_page(url, output_dir, args.no_comments, args.no_tables):
                success += 1
            else:
                failures += 1
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
            future_to_url = {
                executor.submit(extract_page, url, output_dir, args.no_comments, args.no_tables): url
                for url in urls
            }
            for future in tqdm(
                concurrent.futures.as_completed(future_to_url),
                total=len(urls),
                desc="Extracting pages",
                unit="page",
            ):
                if future.result():
                    success += 1
                else:
                    failures += 1

    print(f"\nDone — extracted {success} pages, {failures} failures.")
    print(f"Wrote pages to {output_dir}")


if __name__ == "__main__":
    main()
