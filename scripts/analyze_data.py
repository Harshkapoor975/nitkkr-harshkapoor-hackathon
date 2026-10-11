import os
import csv
import sys
import hashlib
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from store.db import Signal, save_signal, get_connection, init_db
from config import TICKERS, EVENT_TYPES

# Explicitly load .env from the root of risk-engine
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path)

# Fallback in case python-dotenv isn't working as expected
if not os.getenv("GEMINI_API_KEY") and os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.split("=", 1)[1].strip()

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Please install the required packages: pip install google-genai")
    sys.exit(1)

# Ensure the API key is set
if not os.getenv("GEMINI_API_KEY"):
    print("ERROR: GEMINI_API_KEY environment variable is not set.")
    print("Please update your .env file to include GEMINI_API_KEY=your-key")
    sys.exit(1)

client = genai.Client() # Automatically picks up GEMINI_API_KEY

# This is the schema we want the LLM to output
class SignalExtraction(BaseModel):
    ticker: str = Field(description=f"The stock ticker symbol. Must be one of: {list(TICKERS.keys())}")
    sentiment: float = Field(ge=-1.0, le=1.0, description="Sentiment score from -1.0 (very negative) to 1.0 (very positive)")
    event_type: str = Field(description=f"The category of the event. Choose the closest fit from: {EVENT_TYPES}")
    impact: int = Field(ge=1, le=10, description="Severity or impact of the event from 1 (lowest) to 10 (highest)")
    rationale: str = Field(description="A brief explanation for the assigned sentiment and impact scores")

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def analyze_and_store():
    # Initialize the database (this will create tables if they don't exist)
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    input_file = "data/raw_texts.csv"
    if not os.path.exists(input_file):
        print(f"File {input_file} not found. Run generate_sample_data.py first.")
        return

    processed_count = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row['text']
            source = row['source']
            timestamp = row['timestamp']
            
            text_hash = get_hash(text)
            
            # 1. Check if we already processed this exact text (Cache)
            cursor.execute("SELECT ticker, sentiment, event_type, impact, rationale FROM label_cache WHERE text_hash = ?", (text_hash,))
            cached = cursor.fetchone()
            
            if cached:
                # Use cached extraction
                extracted = SignalExtraction(
                    ticker=cached['ticker'],
                    sentiment=cached['sentiment'],
                    event_type=cached['event_type'],
                    impact=cached['impact'],
                    rationale=cached['rationale']
                )
                print(f"Cache hit for: {text[:30]}...")
            else:
                # 2. If not in cache, call Gemini
                print(f"Analyzing: {text[:50]}...")
                
                response = client.models.generate_content(
                    model='gemini-3.8-flash', # Fast and cheap model
                    contents=f"Text: {text}\nSource: {source}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SignalExtraction,
                        system_instruction="You are a financial NLP risk analysis engine. Extract structured intelligence from the given text.",
                        temperature=0.0
                    ),
                )
                
                # Parse the JSON response into our Pydantic model
                extracted = SignalExtraction.model_validate_json(response.text)
                
                # Save to cache so we don't call the API again for this text
                cursor.execute("""
                    INSERT INTO label_cache (text_hash, ticker, sentiment, event_type, impact, rationale)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (text_hash, extracted.ticker, extracted.sentiment, extracted.event_type, extracted.impact, extracted.rationale))
                conn.commit()
            
            # 3. Create the final Signal object
            signal = Signal(
                timestamp=timestamp,
                source=source,
                ticker=extracted.ticker,
                sentiment=extracted.sentiment,
                event_type=extracted.event_type,
                impact=extracted.impact,
                text=text,
                rationale=extracted.rationale
            )
            
            # 4. Save to our main database and CSV store
            save_signal(signal)
            processed_count += 1
            
            # For demonstration, we break after 5 items. Remove this to process the whole file.
            if processed_count >= 5:
                print("Processed 5 items. Stopping early for prototype demonstration.")
                print("To process all items, remove the break condition in scripts/analyze_data.py")
                break
                
    conn.close()
    print(f"Successfully processed and stored {processed_count} signals.")

if __name__ == "__main__":
    analyze_and_store()
