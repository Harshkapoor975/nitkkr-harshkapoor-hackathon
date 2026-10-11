import os
import sys
import pytest
import pandas as pd

# Add risk-engine to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nlp_engine import (
    analyze_single_text, 
    evaluate_contextual_sentiment, 
    extract_ticker, 
    classify_event
)
from src.rebalancer import TacticalRebalancer, MOCK_INDEX_UNIVERSE

def test_loughran_mcdonald_sentiment():
    # Severe negative financial terminology
    res_neg = analyze_single_text("Company defaults on debt obligations and faces bankruptcy.", source="news")
    assert res_neg.sentiment < -0.30
    assert res_neg.event_type == "Credit Event"
    assert res_neg.impact >= 7

    # High positive financial terminology
    res_pos = analyze_single_text("Company crushes earnings estimates and stock soars to all-time highs.", source="news")
    assert res_pos.sentiment > 0.40
    assert res_pos.event_type == "Earnings"

def test_negation_scope_resolution():
    # Base negative
    score_down, _ = evaluate_contextual_sentiment("Company faces downgrade.")
    # Negated negative
    score_not_down, notes = evaluate_contextual_sentiment("Company is not facing downgrade.")
    # Negation should shift sentiment significantly higher than the bare negative
    assert score_not_down > score_down

def test_rebalancer_weight_constraints():
    rebalancer = TacticalRebalancer(
        universe=MOCK_INDEX_UNIVERSE,
        alpha=0.75,
        min_weight=0.02,
        max_weight=0.25
    )
    
    # Synthetic extreme sentiments
    mock_sentiments = {
        "AAPL": {'score': 0.95, 'top_text': 'Extreme positive', 'signal_count': 10},
        "MSFT": {'score': -0.95, 'top_text': 'Extreme negative', 'signal_count': 10},
        "NVDA": {'score': 0.80, 'top_text': 'Strong positive', 'signal_count': 8},
        "GOOGL": {'score': 0.10, 'top_text': 'Mild positive', 'signal_count': 2},
        "AMZN": {'score': -0.50, 'top_text': 'Negative', 'signal_count': 5},
        "META": {'score': 0.00, 'top_text': 'Neutral', 'signal_count': 1},
        "TSLA": {'score': -0.80, 'top_text': 'Strong negative', 'signal_count': 7},
        "JPM": {'score': 0.30, 'top_text': 'Positive', 'signal_count': 4},
        "V": {'score': 0.00, 'top_text': 'Neutral', 'signal_count': 0},
        "UNH": {'score': -0.20, 'top_text': 'Mild negative', 'signal_count': 2}
    }
    
    df = rebalancer.rebalance(mock_sentiments)
    
    # 1. Sum must equal 100% (within floating point precision)
    total_pct = df['weight_pct'].sum()
    assert abs(total_pct - 100.0) < 0.15
    
    # 2. Maximum single-asset cap enforced
    assert df['weight_pct'].max() <= 25.1
    
    # 3. Minimum floor enforced
    assert df['weight_pct'].min() >= 1.9
    
    # 4. Sentiment tilt direction: AAPL (+0.95) must have higher weight than MSFT (-0.95)
    aapl_weight = df[df['ticker'] == 'AAPL']['weight_pct'].values[0]
    msft_weight = df[df['ticker'] == 'MSFT']['weight_pct'].values[0]
    assert aapl_weight > msft_weight

def test_historical_trajectory_datetime_parsing():
    rebalancer = TacticalRebalancer(universe=MOCK_INDEX_UNIVERSE)
    signals_df = pd.DataFrame([
        {
            'timestamp': '2026-09-27T03:46:25.158096Z',
            'ticker': 'AAPL',
            'sentiment': 0.8,
            'impact': 7,
            'text': 'Apple beats estimates'
        },
        {
            'timestamp': '2026-09-28T10:00:00Z',
            'ticker': 'MSFT',
            'sentiment': -0.4,
            'impact': 6,
            'text': 'Microsoft faces challenges'
        }
    ])
    history_df = rebalancer.compute_historical_weight_trajectory(signals_df, num_steps=5)
    assert not history_df.empty
    assert 'weight_pct' in history_df.columns
