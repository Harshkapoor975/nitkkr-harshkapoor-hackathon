"""
scripts/custom_nlp_engine.py
----------------------------
CLI Runner forwarding to canonical implementation in src.nlp_engine.
"""
import os
import sys

# Ensure root import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Forward all core API symbols from src.nlp_engine (Single Source of Truth)
from src.nlp_engine import (
    analyze_single_text,
    evaluate_contextual_sentiment,
    classify_event,
    calculate_impact,
    generate_explainable_rationale,
    preprocess_text,
    extract_ticker,
    run_custom_nlp
)

if __name__ == "__main__":
    run_custom_nlp()
