#!/usr/bin/env python3
import argparse
import datetime
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_URL = "https://lsc.cornell.edu/how-to-study/"
DEFAULT_LOG = Path("scrape.log")


def prompt_url(default):
    reply = input(f"Enter website URL to scrape [{default}]: ").strip()
    return reply or default


def start_detached_process(command, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n[{timestamp}] Starting background scrape:\n")
        log.write(" ".join(shlex.quote(str(c)) for c in command) + "\n")

    log_fp = log_path.open("a", encoding="utf-8")
    subprocess.Popen(
        command,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )

    print(f"Background scrape started. Logs are appended to {log_path.resolve()}")
    print("You can close this terminal; the scraper will continue running in the background.")


def build_command(base_url):
    return [sys.executable, "-u", "-m", "website_scraper.scraper", "--base-url", base_url]


def main():
    parser = argparse.ArgumentParser(description="Prompt for a website and run the scraper in the background.")
    parser.add_argument("--base-url", help="Target page to scrape. If omitted, you will be prompted.")
    parser.add_argument("--log-file", default=str(DEFAULT_LOG), help="Path to the background log file.")
    parser.add_argument("--background", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.background:
        base_url = args.base_url or DEFAULT_URL
        command = build_command(base_url)
        subprocess.run(command, check=True)
        return

    base_url = args.base_url or prompt_url(DEFAULT_URL)
    command = [sys.executable, "-u", str(Path(__file__).resolve()), "--background", "--base-url", base_url]
    start_detached_process(command, Path(args.log_file))


if __name__ == "__main__":
    main()
