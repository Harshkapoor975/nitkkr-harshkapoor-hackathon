"""
src/crawlers/daemon.py
----------------------
Autonomous Live Intelligence Daemon.
Continuously scans RSS feeds and Yahoo Finance, extracts risk signals,
and updates tactical index rebalancing weights automatically.
"""

import os
import sys
import time
import threading
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
try:
    from src.crawlers.rss_crawler import crawl_rss_feeds
    from src.crawlers.deep_scraper import scrape_yahoo_finance
    from src.rebalancer import run_tactical_rebalance
except ImportError:
    from scripts.manual_web_scraper import scrape_deep_web
    from scripts.rebalancer import run_tactical_rebalance

class LiveRiskDaemon:
    def __init__(self, rss_interval_sec: int = 60, scrape_interval_sec: int = 120):
        self.rss_interval = rss_interval_sec
        self.scrape_interval = scrape_interval_sec
        self.seen_articles = set()
        self.is_running = False
        self._thread = None

    def single_crawl_cycle(self) -> dict:
        """Runs a single pass of both crawlers and recalculates weights."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Executing multi-source live intelligence crawl...")
        rss_count = 0
        scrape_count = 0

        try:
            from src.crawlers.rss_crawler import crawl_rss_feeds
            rss_count = crawl_rss_feeds(self.seen_articles)
        except Exception as e:
            print(f"⚠️ RSS crawl error: {e}")

        try:
            from src.crawlers.deep_scraper import scrape_yahoo_finance
            scrape_count = scrape_yahoo_finance()
        except Exception as e:
            print(f"⚠️ Yahoo scraper error: {e}")

        total_new = rss_count + scrape_count
        print(f"✅ Ingested {total_new} new signals ({rss_count} RSS, {scrape_count} Deep Scrape)")

        if total_new > 0:
            print("⚖️ Updating Module A Tactical Rebalancing snapshot...")
            try:
                run_tactical_rebalance(save_to_db=True)
                print("✅ Rebalancing snapshot updated in database!")
            except Exception as e:
                print(f"⚠️ Rebalance recalculation error: {e}")

        return {"rss_new": rss_count, "scrape_new": scrape_count, "total_new": total_new}

    def _loop(self):
        last_scrape_time = 0
        while self.is_running:
            self.single_crawl_cycle()
            time.sleep(self.rss_interval)

    def start_background(self):
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("🚀 Background Live Risk Daemon thread started.")

    def stop(self):
        self.is_running = False
        print("🛑 Live Risk Daemon thread stopped.")

# Global singleton daemon instance
GLOBAL_DAEMON = LiveRiskDaemon()

if __name__ == "__main__":
    print("🌐 Starting Live Risk Intelligence Daemon...")
    print("Press Ctrl+C to terminate.")
    try:
        GLOBAL_DAEMON.is_running = True
        GLOBAL_DAEMON._loop()
    except KeyboardInterrupt:
        GLOBAL_DAEMON.stop()
