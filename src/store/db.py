# src/store/db.py
import sqlite3
import csv
import os
from typing import Literal
from pydantic import BaseModel, Field

class Signal(BaseModel):
    timestamp: str
    source: Literal["news", "social", "global_web", "deep_scrape"]
    ticker: str
    sentiment: float = Field(ge=-1.0, le=1.0)
    event_type: str
    impact: int = Field(ge=1, le=10)
    text: str
    rationale: str

def get_connection(db_path: str = "data/signals.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = "data/signals.db"):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            ticker TEXT,
            sentiment REAL,
            event_type TEXT,
            impact INTEGER,
            text TEXT,
            rationale TEXT
        )
    """)
    # Table for rebalancer
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            weight REAL,
            smoothed_sentiment REAL,
            top_signal_text TEXT
        )
    """)
    # Cache for LLM labeler
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS label_cache (
            text_hash TEXT PRIMARY KEY,
            ticker TEXT,
            sentiment REAL,
            event_type TEXT,
            impact INTEGER,
            rationale TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_signal(signal: Signal, db_path: str = "data/signals.db", csv_path: str = "data/signals.csv"):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO signals (timestamp, source, ticker, sentiment, event_type, impact, text, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal.timestamp, signal.source, signal.ticker, signal.sentiment,
        signal.event_type, signal.impact, signal.text, signal.rationale
    ))
    conn.commit()
    conn.close()

    # Append to CSV
    file_exists = os.path.isfile(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'source', 'ticker', 'sentiment', 'event_type', 'impact', 'text', 'rationale'])
        writer.writerow([
            signal.timestamp, signal.source, signal.ticker, signal.sentiment,
            signal.event_type, signal.impact, signal.text, signal.rationale
        ])

def load_signals(db_path: str = "data/signals.db"):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM signals ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_weights_snapshot(weights_data: list[dict], db_path: str = "data/signals.db"):
    """Saves a batch of tactical portfolio weights to the database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    for item in weights_data:
        cursor.execute("""
            INSERT INTO weights (timestamp, ticker, weight, smoothed_sentiment, top_signal_text)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item['timestamp'],
            item['ticker'],
            item['weight'],
            item.get('smoothed_sentiment', 0.0),
            item.get('top_signal_text', '')
        ))
    conn.commit()
    conn.close()

def load_weight_history(db_path: str = "data/signals.db"):
    """Loads all historical rebalancing snapshots."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM weights ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def load_latest_weights(db_path: str = "data/signals.db"):
    """Loads the latest snapshot of weights for each ticker."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.* FROM weights w
        INNER JOIN (
            SELECT ticker, MAX(timestamp) as max_ts
            FROM weights
            GROUP BY ticker
        ) latest ON w.ticker = latest.ticker AND w.timestamp = latest.max_ts
        ORDER BY w.weight DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
