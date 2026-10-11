# config.py

import pandas as pd

print("🚀 Booting up Dynamic Universe configuration...")

# We start with some highly-tuned manual overrides
TICKERS = {
    "AAPL": ["Apple", "AAPL", "Tim Cook", "iPhone", "MacBook"],
    "MSFT": ["Microsoft", "MSFT", "Satya Nadella", "Windows", "Azure"],
    "NVDA": ["Nvidia", "NVIDIA", "NVDA", "Jensen Huang", "GeForce"],
    "GOOGL": ["Google", "GOOGL", "Alphabet", "Sundar Pichai", "YouTube"],
    "AMZN": ["Amazon", "AMZN", "Jeff Bezos", "Andy Jassy", "AWS"],
    "META": ["Meta", "META", "Facebook", "Mark Zuckerberg", "Instagram", "WhatsApp"],
    "TSLA": ["Tesla", "TSLA", "Elon Musk", "Model 3", "Cybertruck"],
    "JPM": ["JPMorgan", "JPM", "JPMorgan Chase", "Jamie Dimon"],
}

# Dynamically load the ENTIRE S&P 500 list from Wikipedia
try:
    print("🌐 Downloading live S&P 500 constituents...")
    import requests
    import io
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    # Wikipedia blocks default python scrapers (403 Forbidden), so we use a custom User-Agent
    html_content = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
    table = pd.read_html(io.StringIO(html_content))
    sp500_df = table[0]
    
    for idx, row in sp500_df.iterrows():
        ticker = row['Symbol']
        company_name = row['Security']
        
        if ticker not in TICKERS:
            aliases = [company_name, ticker]
            
            # Create a "short name" by stripping corporate suffixes
            short_name = company_name.split(' Inc')[0].split(' Corp')[0].split(' Co')[0].split(',')[0].strip()
            if short_name not in aliases and len(short_name) > 3:
                aliases.append(short_name)
                
            TICKERS[ticker] = aliases
            
    print(f"✅ Successfully loaded {len(TICKERS)} dynamic companies into the Risk Engine memory!")
except Exception as e:
    print(f"⚠️ Could not load dynamic S&P 500 list. Falling back to core tickers. Error: {e}")

EVENT_TYPES = [
    "Geopolitical",
    "Macroeconomic",
    "Credit Event",
    "Merger/Acquisition",
    "Product Launch",
    "Earnings",
    "Regulatory",
    "Other"
]

BASE_SEVERITY = {
    "Credit Event": 9,
    "Geopolitical": 8,
    "Regulatory": 7,
    "Macroeconomic": 7,
    "Merger/Acquisition": 6,
    "Earnings": 6,
    "Product Launch": 4,
    "Other": 3
}

SOURCE_WEIGHTS = {
    "news": 1.0,
    "social": 0.8
}
