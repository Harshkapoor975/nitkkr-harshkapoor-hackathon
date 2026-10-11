"""
scripts/rebalancer.py
---------------------
CLI Runner forwarding to canonical implementation in src.rebalancer.
"""
import os
import sys

# Ensure root import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Forward all core API symbols from src.rebalancer (Single Source of Truth)
from src.rebalancer import (
    TacticalRebalancer,
    MOCK_INDEX_UNIVERSE,
    run_tactical_rebalance
)

if __name__ == "__main__":
    print("🚀 Running Module A: Tactical Index Rebalancer Engine...")
    weights, hist, perf = run_tactical_rebalance()
    print("\n✅ Current Tactical Allocation vs Equal-Weight Benchmark (10%):")
    print(weights[['ticker', 'weight_pct', 'benchmark_pct', 'active_tilt_pct', 'smoothed_sentiment']])
    if not perf.empty:
        latest = perf.iloc[-1]
        print(f"\n📈 Simulated Performance: Portfolio ${latest['Tactical_Portfolio']:,.2f} vs Benchmark ${latest['Equal_Weight_Benchmark']:,.2f} (Alpha: {latest['Alpha_Pct']:+.2f}%)")
