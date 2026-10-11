"""
src/crawlers/rss_crawler.py
---------------------------
Multi-source financial news RSS feed crawler.
Polls CNBC, WSJ, Moneycontrol, Investing.com, and Google News Finance.
"""

import os
import sys
import time
from datetime import datetime
import feedparser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
try:
    from src.nlp_engine import analyze_single_text, extract_ticker, preprocess_text
    from src.store.db import save_signal, init_db
except ImportError:
    from scripts.custom_nlp_engine import analyze_single_text, extract_ticker, preprocess_text
    from store.db import save_signal, init_db

GENERAL_FEEDS = [
    ("CNBC Markets", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"),
    ("Moneycontrol Latest", "https://www.moneycontrol.com/rss/latestnews.xml"),
    ("WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("Investing.com", "https://www.investing.com/rss/news_25.rss"),
    ("Google News Finance", "https://news.google.com/rss/search?q=stock+market+OR+finance+OR+business")
]

def crawl_rss_feeds(seen_articles_set: set = None) -> int:
    """Crawls all configured financial RSS feeds and processes new signals."""
    if seen_articles_set is None:
        seen_articles_set = set()

    init_db()
    new_signals_count = 0

    for source_name, url in GENERAL_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"⚠️ Feed error ({source_name}): {e}")
            continue

        for entry in feed.entries:
            title = entry.title
            if not title or title in seen_articles_set:
                continue

            seen_articles_set.add(title)
            clean_text = preprocess_text(title)
            ticker, _ = extract_ticker(clean_text)
            if ticker == "UNKNOWN":
                continue

            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed)
            else:
                timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            signal = analyze_single_text(
                raw_text=title,
                source="news",
                timestamp=timestamp
            )
            save_signal(signal)
            new_signals_count += 1

    return new_signals_count

if __name__ == "__main__":
    count = crawl_rss_feeds()
    print(f"Crawled and processed {count} signals from RSS.")
