import os
import sys
import pytest
from pydantic import ValidationError

# Add risk-engine to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from store.db import init_db, save_signal, load_signals, Signal
import tempfile

def test_db_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        csv_path = os.path.join(tmpdir, "test.csv")
        
        init_db(db_path)
        
        sig = Signal(
            timestamp="2024-01-01T12:00:00Z",
            source="news",
            ticker="AAPL",
            sentiment=0.8,
            event_type="Earnings",
            impact=8,
            text="Apple earnings beat expectations.",
            rationale="Positive earnings report"
        )
        
        save_signal(sig, db_path, csv_path)
        
        loaded = load_signals(db_path)
        assert len(loaded) == 1
        assert loaded[0]["ticker"] == "AAPL"
        assert loaded[0]["sentiment"] == 0.8
        
        # Check CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2 # header + 1 row
            assert "AAPL" in lines[1]

def test_signal_validation():
    # Invalid sentiment (too high)
    with pytest.raises(ValidationError):
        Signal(
            timestamp="2024-01-01T12:00:00Z",
            source="news",
            ticker="AAPL",
            sentiment=1.5,
            event_type="Earnings",
            impact=8,
            text="Apple is doing well.",
            rationale="Test"
        )
    
    # Invalid source
    with pytest.raises(ValidationError):
        Signal(
            timestamp="2024-01-01T12:00:00Z",
            source="blog",
            ticker="AAPL",
            sentiment=0.5,
            event_type="Earnings",
            impact=8,
            text="Test text.",
            rationale="Test"
        )
