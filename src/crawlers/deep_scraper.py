"""
src/crawlers/deep_scraper.py
----------------------------
Deep HTML web scraper targeting Yahoo Finance market news headlines.
Cleanses noise, performs Named Entity Recognition, and extracts risk intelligence.
"""

import os
import sys
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import urllib3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
try:
    from src.nlp_engine import analyze_single_text, extract_ticker, preprocess_text
    from src.store.db import save_signal, init_db
except ImportError:
    from scripts.custom_nlp_engine import analyze_single_text, extract_ticker, preprocess_text
    from store.db import save_signal, init_db

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scrape_yahoo_finance() -> int:
    init_db()
    url = "https://finance.yahoo.com/topic/stock-market-news/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Yahoo Finance Scraper error: {e}")
        return 0

    soup = BeautifulSoup(response.text, 'html.parser')
    for elem in soup(["script", "style", "nav", "footer", "header", "aside"]):
        elem.extract()

    text_blocks = soup.find_all(['p', 'h2', 'h3'])
    seen = set()
    processed_count = 0

    for block in text_blocks:
        raw_text = block.get_text().strip()
        if len(raw_text) < 30 or raw_text in seen:
            continue

        seen.add(raw_text)
        clean_text = preprocess_text(raw_text)
        ticker, _ = extract_ticker(clean_text)
        if ticker == "UNKNOWN":
            continue

        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        signal = analyze_single_text(
            raw_text=clean_text[:500],
            source="deep_scrape",
            timestamp=timestamp
        )
        save_signal(signal)
        processed_count += 1

    return processed_count

if __name__ == "__main__":
    count = scrape_yahoo_finance()
    print(f"Scraped {count} items from Yahoo Finance.")
