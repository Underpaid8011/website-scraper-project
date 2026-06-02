"""Website Scraper package."""

from .scraper import collect_urls, main as scraper_main
from .run_scraper import main as run_main

__all__ = ["collect_urls", "scraper_main", "run_main"]
