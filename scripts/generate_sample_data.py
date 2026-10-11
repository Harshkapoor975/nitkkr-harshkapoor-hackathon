import csv
import random
import os
from datetime import datetime, timedelta
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.config import TICKERS, EVENT_TYPES
except ImportError:
    from config import TICKERS, EVENT_TYPES

TEMPLATES = [
    ("news", "positive", "{company} crushes earnings expectations, stock soars on strong guidance.", "Earnings"),
    ("news", "negative", "{company} faces massive lawsuit over antitrust violations.", "Regulatory"),
    ("social", "positive", "Just got the new {company} product, absolutely blowing my mind! #bullish", "Product Launch"),
    ("social", "negative", "Can't believe {company} support is this bad. Switching to competitor. $CASHTAG", "Other"),
    ("news", "neutral", "{company} announces new manufacturing plant in Ohio.", "Merger/Acquisition"),
    ("news", "negative", "Analysts downgrade {company} citing macro headwinds.", "Macroeconomic"),
    ("news", "positive", "{company} secures major government contract.", "Geopolitical"),
    ("social", "neutral", "Waiting to see what {company} announces tomorrow.", "Other"),
    ("news", "negative", "{company} credit rating slashed by Moody's after debt load increases.", "Credit Event"),
    ("news", "positive", "Fed cuts rates, {company} poised to benefit from cheaper borrowing.", "Macroeconomic"),
    ("news", "negative", "New tariffs impact {company} supply chain in Asia.", "Geopolitical"),
    ("social", "positive", "Wow, {company}'s new AI models are insane. Long term hold.", "Product Launch"),
    ("news", "positive", "{company} announces acquisition of smaller rival to boost market share.", "Merger/Acquisition"),
    ("social", "negative", "{company} CEO unexpectedly steps down, stock drops.", "Other"),
    ("news", "neutral", "{company} to hold annual shareholder meeting next week.", "Other"),
    ("social", "neutral", "Has anyone tried {company}'s new features yet?", "Product Launch"),
    ("news", "positive", "{company} forms strategic partnership to expand in Europe.", "Merger/Acquisition"),
    ("social", "negative", "Rumors that {company} will miss earnings this quarter. Scary.", "Earnings"),
]

CORE_INDEX = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "UNH"]

def generate_data(num_records=200):
    os.makedirs('data', exist_ok=True)
    with open('data/raw_texts.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'source', 'text'])
        
        now = datetime.utcnow()
        # Spread timestamps chronologically over last 14 days
        for i in range(num_records):
            # 70% probability to pick from core index so rebalancer has rich signal history
            if random.random() < 0.75:
                ticker = random.choice(CORE_INDEX)
            else:
                ticker = random.choice(list(TICKERS.keys()))
                
            company = TICKERS[ticker][0] # first alias is typically the company name
            source, sentiment, template, event_type = random.choice(TEMPLATES)
            
            text = template.replace("{company}", company).replace("$CASHTAG", f"${ticker}")
            
            days_ago = random.uniform(0, 14)
            ts = now - timedelta(days=days_ago)
            ts_str = ts.isoformat() + "Z"
            
            writer.writerow([ts_str, source, text])

if __name__ == "__main__":
    generate_data()
    print("Generated 200 rows in data/raw_texts.csv")
