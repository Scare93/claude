#!/usr/bin/env python3
"""
Montana Code Annotated (MCA) & Constitution Scraper.

Scrapes the exact text of specified MCA titles and the Montana Constitution
from leg.mt.gov. Stores results as JSON files organized by title/chapter/part/section.

Usage:
    python scrape_mca.py                  # Scrape all configured titles
    python scrape_mca.py --title 45       # Scrape only Title 45
    python scrape_mca.py --title 0        # Scrape only the Constitution
    python scrape_mca.py --force          # Re-scrape even if files exist
    python scrape_mca.py --delay 2.0      # Override request delay (seconds)
    python scrape_mca.py --dry-run        # Show what would be scraped
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

import mca_config as config

logger = logging.getLogger("scrape_mca")


# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------

class PageFetcher:
    """HTTP client with rate limiting, retry, and logging."""

    def __init__(self, delay=None, timeout=None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.USER_AGENT})
        self.delay = delay if delay is not None else config.REQUEST_DELAY_SECONDS
        self.timeout = timeout or config.REQUEST_TIMEOUT_SECONDS
        self.request_count = 0

    def fetch(self, url):
        """Fetch a URL with retry and backoff. Returns HTML string or None."""
        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                time.sleep(self.delay)
                self.request_count += 1
                logger.debug("GET %s (attempt %d)", url, attempt + 1)
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except requests.exceptions.HTTPError as exc:
                status = exc.response.status_code if exc.response else "?"
                if status == 404:
                    logger.warning("404 Not Found: %s", url)
                    return None
                logger.error("HTTP %s for %s (attempt %d)", status, url, attempt + 1)
            except requests.exceptions.RequestException as exc:
                logger.error("Request error for %s: %s (attempt %d)", url, exc, attempt + 1)

            backoff = config.RETRY_BACKOFF_SECONDS * (2 ** attempt)
            logger.info("Retrying in %.0fs...", backoff)
            time.sleep(backoff)

        logger.error("All retries exhausted for %s", url)
        return None


# ---------------------------------------------------------------------------
# HTML Parsers
# ---------------------------------------------------------------------------

def parse_index_links(html, base_url):
    """
    Parse an index page (titles, chapters, parts, or sections) and return
    a list of (name, absolute_url) tuples for child pages.
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []

    # Look for <a> tags whose href points to child index or section pages
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        # Skip navigation/header links, anchors, external links
        if href.startswith("#") or href.startswith("mailto:"):
            continue
        # We want links that go deeper into the MCA hierarchy
        if any(kw in href for kw in [
            "chapters_index", "parts_index", "sections_index",
            "chapter_", "part_", "section_", "article_",
        ]):
            name = a_tag.get_text(strip=True)
            abs_url = urljoin(base_url, href)
            if name and abs_url not in [u for _, u in links]:
                links.append((name, abs_url))

    return links


def parse_section_page(html):
    """
    Parse an individual section page and extract the exact statute text.
    Returns dict with 'heading' and 'text_content', preserving exact text.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extract the heading (section citation + title)
    heading = ""
    # Try common heading patterns on MCA pages
    for tag in ["h3", "h2", "h1", "h4"]:
        h = soup.find(tag)
        if h:
            heading = h.get_text(strip=True)
            break
    if not heading:
        title_tag = soup.find("title")
        if title_tag:
            heading = title_tag.get_text(strip=True)

    # Extract the body text of the statute
    # MCA section pages typically have the statute text in the <body> after
    # navigation elements. We extract all text from <body>, excluding script/style.
    body = soup.find("body")
    if not body:
        return {"heading": heading, "text_content": ""}

    # Remove script and style elements
    for tag in body.find_all(["script", "style", "nav"]):
        tag.decompose()

    # Get the text content, preserving the structure
    text_content = body.get_text(separator="\n")

    # Clean up excessive blank lines while preserving exact text
    lines = text_content.split("\n")
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not prev_blank:
                cleaned_lines.append("")
            prev_blank = True
        else:
            cleaned_lines.append(stripped)
            prev_blank = False

    text_content = "\n".join(cleaned_lines).strip()

    return {"heading": heading, "text_content": text_content}


# ---------------------------------------------------------------------------
# Crawl Orchestrator
# ---------------------------------------------------------------------------

class MCAScraper:
    """Hierarchical crawler for MCA titles and the Montana Constitution."""

    def __init__(self, data_dir, fetcher, force=False, dry_run=False):
        self.data_dir = Path(data_dir)
        self.fetcher = fetcher
        self.force = force
        self.dry_run = dry_run
        self.stats = {
            "titles_scraped": 0,
            "sections_saved": 0,
            "sections_skipped": 0,
            "errors": [],
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

    def run(self, titles):
        """Scrape the specified titles."""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        for title_num in sorted(titles.keys()):
            title_name = titles[title_num]
            logger.info("=" * 60)
            logger.info("TITLE %d: %s", title_num, title_name)
            logger.info("=" * 60)
            self.scrape_title(title_num, title_name)
            self.stats["titles_scraped"] += 1

        self.stats["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.stats["total_requests"] = self.fetcher.request_count
        self._write_manifest()
        self._print_summary()

    def scrape_title(self, title_num, title_name):
        """Fetch title index page, discover chapters/articles, recurse."""
        if title_num == 0:
            dir_name = "constitution"
        else:
            dir_name = f"title_{title_num:02d}"

        title_dir = self.data_dir / dir_name
        title_dir.mkdir(parents=True, exist_ok=True)

        url = config.title_url(title_num)
        logger.info("Fetching title index: %s", url)

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch: %s", url)
            return

        html = self.fetcher.fetch(url)
        if html is None:
            self._record_error(url, "Failed to fetch title index")
            return

        children = parse_index_links(html, url)
        if not children:
            logger.warning("No children found for title %d at %s", title_num, url)
            self._record_error(url, "No children found on title index page")
            return

        index_data = {
            "level": "title",
            "title_number": title_num,
            "title_name": title_name,
            "url": url,
            "children": [{"name": name, "url": u} for name, u in children],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        if title_num == 0:
            index_data["type"] = "constitution"
        self._save_json(title_dir / "_index.json", index_data)

        for child_name, child_url in children:
            self._scrape_chapter_or_article(title_num, title_name, title_dir,
                                            child_name, child_url)

    def _scrape_chapter_or_article(self, title_num, title_name, title_dir,
                                    chapter_name, chapter_url):
        """Fetch a chapter (or article) page, discover parts, recurse."""
        # Derive a directory name from the URL path component
        dir_name = self._dir_from_url(chapter_url, level="chapter")
        chapter_dir = title_dir / dir_name
        chapter_dir.mkdir(parents=True, exist_ok=True)

        logger.info("  Chapter/Article: %s", chapter_name)

        html = self.fetcher.fetch(chapter_url)
        if html is None:
            self._record_error(chapter_url, f"Failed to fetch chapter: {chapter_name}")
            return

        children = parse_index_links(html, chapter_url)

        index_data = {
            "level": "chapter",
            "title_number": title_num,
            "name": chapter_name,
            "url": chapter_url,
            "children": [{"name": n, "url": u} for n, u in children],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_json(chapter_dir / "_index.json", index_data)

        if not children:
            # Some chapters link directly to sections from the chapter page
            # Try parsing as section links
            self._try_sections_from_page(html, chapter_url, title_num,
                                         title_name, chapter_name, chapter_dir)
            return

        # Check if children are parts or direct sections
        first_url = children[0][1] if children else ""
        if "sections_index" in first_url or "section_" in first_url:
            # Children are sections directly (no part layer)
            for sec_name, sec_url in children:
                if "sections_index" in sec_url:
                    # It's a part's sections index
                    self._scrape_part(title_num, title_name, chapter_name,
                                      chapter_dir, sec_name, sec_url)
                else:
                    self._scrape_section(title_num, chapter_dir, sec_name, sec_url)
        else:
            # Children are parts
            for part_name, part_url in children:
                self._scrape_part(title_num, title_name, chapter_name,
                                  chapter_dir, part_name, part_url)

    def _scrape_part(self, title_num, title_name, chapter_name,
                     chapter_dir, part_name, part_url):
        """Fetch a part page, discover sections, scrape each."""
        dir_name = self._dir_from_url(part_url, level="part")
        part_dir = chapter_dir / dir_name
        part_dir.mkdir(parents=True, exist_ok=True)

        logger.info("    Part: %s", part_name)

        html = self.fetcher.fetch(part_url)
        if html is None:
            self._record_error(part_url, f"Failed to fetch part: {part_name}")
            return

        children = parse_index_links(html, part_url)

        index_data = {
            "level": "part",
            "title_number": title_num,
            "name": part_name,
            "url": part_url,
            "children": [{"name": n, "url": u} for n, u in children],
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_json(part_dir / "_index.json", index_data)

        for sec_name, sec_url in children:
            if "sections_index" in sec_url:
                # Nested deeper - fetch that index too
                sub_html = self.fetcher.fetch(sec_url)
                if sub_html:
                    sub_children = parse_index_links(sub_html, sec_url)
                    for sub_name, sub_url in sub_children:
                        self._scrape_section(title_num, part_dir, sub_name, sub_url)
            else:
                self._scrape_section(title_num, part_dir, sec_name, sec_url)

    def _scrape_section(self, title_num, parent_dir, section_name, section_url):
        """Fetch and save an individual section page."""
        # Derive filename from the URL
        filename = self._filename_from_url(section_url)
        filepath = parent_dir / filename

        if not self.force and filepath.exists():
            logger.debug("      Skipping (exists): %s", section_name)
            self.stats["sections_skipped"] += 1
            return

        logger.info("      Section: %s", section_name)

        html = self.fetcher.fetch(section_url)
        if html is None:
            self._record_error(section_url, f"Failed to fetch section: {section_name}")
            return

        parsed = parse_section_page(html)
        content_hash = hashlib.sha256(parsed["text_content"].encode("utf-8")).hexdigest()

        section_data = {
            "title_number": title_num,
            "section_name": section_name,
            "heading": parsed["heading"],
            "url": section_url,
            "raw_html": html,
            "text_content": parsed["text_content"],
            "content_hash": f"sha256:{content_hash}",
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }

        self._save_json(filepath, section_data)
        self.stats["sections_saved"] += 1

    def _try_sections_from_page(self, html, page_url, title_num, title_name,
                                 chapter_name, chapter_dir):
        """Try to find section links on a page that might list them directly."""
        soup = BeautifulSoup(html, "html.parser")
        section_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Section pages end with a numbered .html file like 0010-0010-0010-0010.html
            if re.search(r"\d{4}-\d{4}-\d{4}-\d{4}\.html", href):
                name = a_tag.get_text(strip=True)
                abs_url = urljoin(page_url, href)
                if name:
                    section_links.append((name, abs_url))

        for sec_name, sec_url in section_links:
            self._scrape_section(title_num, chapter_dir, sec_name, sec_url)

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _dir_from_url(self, url, level="chapter"):
        """Extract a directory name from a URL path component."""
        # e.g. .../title_0450/chapter_0050/parts_index.html -> chapter_0050
        # e.g. .../article_0020/part_0010/sections_index.html -> article_0020
        parts = url.rstrip("/").split("/")
        for part in reversed(parts):
            if part.startswith(("chapter_", "article_", "part_")):
                return part
            # For sections_index.html or parts_index.html, look at parent
            if part.endswith(".html"):
                continue
        # Fallback: use a sanitized version of the last path component
        return re.sub(r"[^\w-]", "_", parts[-2] if len(parts) >= 2 else "unknown")

    def _filename_from_url(self, url):
        """Extract a JSON filename from a section URL."""
        # e.g. .../0450-0050-0010-0020.html -> 0450-0050-0010-0020.json
        basename = url.rstrip("/").split("/")[-1]
        if basename.endswith(".html") or basename.endswith(".htm"):
            return re.sub(r"\.html?$", ".json", basename)
        return basename + ".json"

    def _save_json(self, path, data):
        """Write JSON file atomically."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.rename(path)

    def _record_error(self, url, message):
        """Record an error for the manifest."""
        self.stats["errors"].append({
            "url": url,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _write_manifest(self):
        """Write a master manifest summarizing the scrape."""
        manifest_path = self.data_dir / "manifest.json"
        self._save_json(manifest_path, self.stats)
        logger.info("Manifest written to %s", manifest_path)

    def _print_summary(self):
        """Print a summary of the scrape results."""
        print("\n" + "=" * 60)
        print("SCRAPE SUMMARY")
        print("=" * 60)
        print(f"Titles processed:  {self.stats['titles_scraped']}")
        print(f"Sections saved:    {self.stats['sections_saved']}")
        print(f"Sections skipped:  {self.stats['sections_skipped']}")
        print(f"Total requests:    {self.stats['total_requests']}")
        print(f"Errors:            {len(self.stats['errors'])}")
        if self.stats["errors"]:
            print("\nErrors:")
            for err in self.stats["errors"]:
                print(f"  - {err['message']}: {err['url']}")
        print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def setup_logging(data_dir):
    """Configure logging to stdout and file."""
    log_dir = Path(data_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "scrape_mca.log"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    root_logger = logging.getLogger("scrape_mca")
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Montana Code Annotated (MCA) titles and Constitution."
    )
    parser.add_argument(
        "--title", type=int, default=None,
        help="Scrape only this title number (0 for Constitution)."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-scrape sections even if JSON files already exist."
    )
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Delay between requests in seconds (default: %.1f)." % config.REQUEST_DELAY_SECONDS
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be scraped without making requests."
    )
    parser.add_argument(
        "--data-dir", type=str, default=config.DATA_DIR,
        help="Output directory for scraped data (default: %s)." % config.DATA_DIR
    )
    args = parser.parse_args()

    setup_logging(args.data_dir)

    # Determine which titles to scrape
    if args.title is not None:
        if args.title not in config.TITLES_TO_SCRAPE:
            print(f"Error: Title {args.title} is not in the configured list.")
            print("Configured titles:", sorted(config.TITLES_TO_SCRAPE.keys()))
            sys.exit(1)
        titles = {args.title: config.TITLES_TO_SCRAPE[args.title]}
    else:
        titles = config.TITLES_TO_SCRAPE

    fetcher = PageFetcher(delay=args.delay)
    scraper = MCAScraper(
        data_dir=args.data_dir,
        fetcher=fetcher,
        force=args.force,
        dry_run=args.dry_run,
    )

    logger.info("Starting MCA scraper for %d title(s)", len(titles))
    scraper.run(titles)


if __name__ == "__main__":
    main()
