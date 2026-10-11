"""
scripts/fetch_live_news.py
--------------------------
CLI Runner forwarding to canonical implementation in src.crawlers.rss_crawler.
"""
import os
import sys

# Ensure root import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.crawlers.rss_crawler import crawl_rss_feeds

def fetch_live_news():
    return crawl_rss_feeds()

if __name__ == "__main__":
    count = fetch_live_news()
    print(f"✅ Fetched and analyzed {count} live news items from RSS feeds.")
