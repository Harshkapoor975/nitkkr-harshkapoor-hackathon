"""
scripts/manual_web_scraper.py
-----------------------------
CLI Runner forwarding to canonical implementation in src.crawlers.deep_scraper.
"""
import os
import sys

# Ensure root import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawlers.deep_scraper import scrape_yahoo_finance

def scrape_deep_web():
    return scrape_yahoo_finance()

if __name__ == "__main__":
    count = scrape_deep_web()
    print(f"✅ Scraped and analyzed {count} blocks from Yahoo Finance.")
