import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from chatbot.database.database import SessionLocal
from chatbot.database.models import Document
from pathlib import Path
from chatbot.config import URLS_FILE
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

MAX_PAGES = 200
BASE_URL = "https://www.adcountymedia.com"

SKIP_PAGES = [
    "terms-and-conditions",
    "privacy-policy",
    "cookie-policy",
    "investors",
    "/v1/PDFFile/"
]

ALLOWED_PATHS = [
    "/products/",
    "/about-us",
    "/careers",
    "/contact",
]

SCRAPE_TARGETS = [
    {
        "mode": "adcounty",
        "urls": {BASE_URL},
    },
    {
        "mode": "gitbook",
        "urls": {
            line.strip()
            for line in URLS_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        } if URLS_FILE.exists() else set(),
    },
]

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_default_timeout(60000)

    for target in SCRAPE_TARGETS:

        SCRAPE_MODE = target["mode"]
        to_visit = target["urls"]
        visited = set()

        if not to_visit:
            print(f"\nSkipping {SCRAPE_MODE} — no URLs to scrape.")
            continue

        print(f"\n{'='*50}")
        print(f"STARTING SCRAPE: {SCRAPE_MODE.upper()}")
        print(f"{'='*50}\n")

        while to_visit:

            url = to_visit.pop()

            if any(skip_page in url for skip_page in SKIP_PAGES):
                continue

            if url in visited:
                continue

            visited.add(url)

            if len(visited) > MAX_PAGES:
                break

            print(f"Scraping: {url}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)

                # Scroll to trigger lazy-loaded content
                page.evaluate("""
                    if (document.body) {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                """)
                for _ in range(5):
                    page.evaluate("window.scrollBy(0, 2000)")
                    page.wait_for_timeout(1000)
                page.wait_for_timeout(2000)

                all_accordion_text = ""
                all_tab_text = ""

                if SCRAPE_MODE == "adcounty" and "/products/" in url:

                    # ── Accordions ───────────────────────────────────────────
                    # Query all triggers (open + closed) upfront by index
                    # to avoid stale DOM references from toggling
                    triggers = page.locator("[data-state='closed'], [data-state='open']")
                    total = triggers.count()
                    print(f"Found {total} accordion triggers")

                    seen_sections = set()

                    for i in range(total):
                        try:
                            trigger = triggers.nth(i)

                            if not trigger.is_visible():
                                continue

                            section_name = trigger.inner_text().strip()

                            # Skip content panels masquerading as triggers
                            if len(section_name) > 100:
                                continue

                            # Skip duplicates
                            if section_name in seen_sections:
                                continue
                            seen_sections.add(section_name)

                            trigger.scroll_into_view_if_needed()
                            trigger.click(force=True)
                            page.wait_for_timeout(1500)

                            try:
                                panel = page.locator("[data-state='open']").last
                                panel_text = panel.inner_text().strip()
                                if panel_text and panel_text != section_name:
                                    all_accordion_text += f"\n\n## {section_name}\n{panel_text}"
                                    print(f"  Accordion '{section_name}' → {len(panel_text)} chars")
                                else:
                                    print(f"  Accordion '{section_name}' → empty")
                            except Exception as e:
                                print(f"  Panel grab [{i}] failed: {e}")

                        except Exception as e:
                            print(f"  Accordion [{i}] failed: {e}")

                    page.wait_for_timeout(1000)

                    # ── Tabs — role='tab' only ───────────────────────────────────
                    tab_elements = page.locator("[role='tab']")
                    tab_count = tab_elements.count()
                    print(f"Found {tab_count} tabs")

                    seen_tabs = set()

                    for i in range(tab_count):
                        try:
                            tab = page.locator("[role='tab']").nth(i)
                            tab_name = tab.inner_text().strip()

                            if not tab_name or len(tab_name) > 100:
                                continue
                            if tab_name in seen_tabs:
                                continue
                            seen_tabs.add(tab_name)

                            print(f"Opening tab: {tab_name}")
                            tab.click(force=True)
                            page.wait_for_timeout(2000)

                            panel = page.locator("[role='tabpanel']")
                            panel.wait_for(timeout=5000)
                            content = panel.inner_text().strip()

                            if content:
                                all_tab_text += f"\n\n## {tab_name}\n{content}"
                                print(f"  Tab '{tab_name}' → {len(content)} chars")

                        except Exception as e:
                            print(f"  Tab [{i}] failed: {e}")

                # ── Base page HTML extraction ────────────────────────────────
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Collect internal links
                if SCRAPE_MODE == "adcounty":
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        if href.lower().endswith(".pdf"):
                            continue
                        full_url = urljoin(BASE_URL, href)
                        parsed = urlparse(full_url)
                        if parsed.netloc == urlparse(BASE_URL).netloc:
                            clean_url = (
                                parsed.scheme + "://" + parsed.netloc
                                + parsed.path.rstrip("/")
                            )
                            if not any(path in clean_url for path in ALLOWED_PATHS):
                                continue
                            if clean_url not in visited:
                                to_visit.add(clean_url)

                # Strip UI chrome
                for tag in soup.find_all(["form", "input", "button", "select", "textarea"]):
                    tag.decompose()
                for tag in soup(["script", "style"]):
                    tag.decompose()

                main_content = (
                    soup.find("main")
                    or soup.find("article")
                    or soup.find("body")
                )

                if not main_content:
                    continue

                if SCRAPE_MODE == "gitbook":
                    page_text = page.locator("main").inner_text()
                else:
                    page_text = main_content.get_text(separator="\n", strip=True)

                # ── Merge all sections — accordion/tab content FIRST ────────────────
                # Put structured content before base page text so chunking
                # captures it in the first chunks rather than burying it after noise
                
                text = ""
                if all_accordion_text.strip():
                    text += all_accordion_text.strip() + "\n\n"
                if all_tab_text.strip():
                    text += all_tab_text.strip() + "\n\n"
                text += page_text.strip()

                text = text.replace("Your browser does not support the video tag.", "")

                print(f"Extracted {len(text)} chars total")

                # Skip binary/asset URLs
                if any(
                    x in url.lower()
                    for x in [".jpg", ".jpeg", ".png", ".svg", ".pdf", ".zip", "#"]
                ):
                    continue

                page_title = soup.title.string.strip() if soup.title else url
                source_type = "website" if SCRAPE_MODE == "adcounty" else "gitbook"

                # ── Persist to PostgreSQL ────────────────────────────────────
                db = SessionLocal()
                try:
                    existing = db.query(Document).filter(Document.url == url).first()
                    if existing:
                        existing.title = page_title
                        existing.content = text
                        existing.source = source_type
                        db.commit()
                    else:
                        doc = Document(
                            source=source_type,
                            title=page_title,
                            url=url,
                            content=text,
                        )
                        db.add(doc)
                        db.commit()
                finally:
                    db.close()

                print(f"Saved → {page_title} ({source_type})")

            except Exception as e:
                print(f"Failed: {url} — {e}")

        print(f"\nFinished {SCRAPE_MODE.upper()} — {len(visited)} pages scraped.")

    browser.close()

print("\nAll scraping complete!")