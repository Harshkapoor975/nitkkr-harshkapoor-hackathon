"""
src/rebalancer.py
-----------------
Module A: Tactical Index Rebalancer for S&P Global & CRISIL Hackathon 2026.
Subscribes to real-time sentiment signals, computes time-decayed rolling
sentiments, dynamically adjusts portfolio weights under institutional
risk bounds, and simulates active alpha over an Equal-Weighted S&P benchmark.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Flexible imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from src.store.db import load_signals, save_weights_snapshot, load_weight_history, get_connection
except ImportError:
    from store.db import load_signals, save_weights_snapshot, load_weight_history, get_connection

MOCK_INDEX_UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
    "META", "TSLA", "JPM", "V", "UNH"
]

class TacticalRebalancer:
    def __init__(
        self,
        universe: list[str] = None,
        alpha: float = 0.75,
        half_life_hours: float = 48.0,
        min_weight: float = 0.02,
        max_weight: float = 0.25
    ):
        self.universe = sorted(universe or MOCK_INDEX_UNIVERSE)
        self.num_assets = len(self.universe)
        self.base_weight = 1.0 / self.num_assets
        self.alpha = alpha
        self.decay_lambda = math.log(2.0) / (half_life_hours * 3600.0)
        self.min_weight = min_weight
        self.max_weight = max_weight

    def calculate_decay_weight(self, signal_time: datetime, reference_time: datetime) -> float:
        delta_seconds = max(0.0, (reference_time - signal_time).total_seconds())
        return math.exp(-self.decay_lambda * delta_seconds)

    def compute_smoothed_sentiments(self, signals_df: pd.DataFrame, reference_time: datetime = None) -> dict:
        if reference_time is None:
            reference_time = datetime.utcnow()

        results = {}
        for ticker in self.universe:
            ticker_signals = signals_df[signals_df['ticker'] == ticker]
            if ticker_signals.empty:
                results[ticker] = {
                    'score': 0.0,
                    'top_text': 'No recent signals logged',
                    'signal_count': 0
                }
                continue

            weighted_sum = 0.0
            total_weight = 0.0
            top_signal = None
            max_impact = -1

            for _, row in ticker_signals.iterrows():
                try:
                    raw_ts = row.get('timestamp')
                    sig_time = pd.to_datetime(raw_ts, format='mixed', errors='coerce', utc=True)
                    if pd.isna(sig_time):
                        sig_time = reference_time
                    else:
                        sig_time = sig_time.to_pydatetime().replace(tzinfo=None)
                except Exception:
                    sig_time = reference_time

                decay = self.calculate_decay_weight(sig_time, reference_time)
                impact = float(row.get('impact', 5))
                effective_weight = decay * (impact / 5.0)

                sentiment = float(row.get('sentiment', 0.0))
                weighted_sum += effective_weight * sentiment
                total_weight += effective_weight

                if impact > max_impact:
                    max_impact = impact
                    top_signal = row.get('text', '')

            smoothed_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
            smoothed_score = max(-1.0, min(1.0, smoothed_score))

            results[ticker] = {
                'score': round(smoothed_score, 4),
                'top_text': top_signal or 'General sentiment update',
                'signal_count': len(ticker_signals)
            }

        return results

    def rebalance(self, smoothed_sentiments: dict) -> pd.DataFrame:
        raw_weights = {}
        for ticker in self.universe:
            sent = smoothed_sentiments[ticker]['score']
            tilt_factor = 1.0 + (self.alpha * sent)
            raw_weights[ticker] = max(0.001, self.base_weight * tilt_factor)

        weights = self._apply_bounds_and_normalize(raw_weights)

        rows = []
        for ticker in self.universe:
            w = weights[ticker]
            benchmark_w = self.base_weight
            active_tilt = w - benchmark_w
            rows.append({
                'ticker': ticker,
                'weight': round(w, 4),
                'weight_pct': round(w * 100, 2),
                'benchmark_weight': round(benchmark_w, 4),
                'benchmark_pct': round(benchmark_w * 100, 2),
                'active_tilt_pct': round(active_tilt * 100, 2),
                'smoothed_sentiment': smoothed_sentiments[ticker]['score'],
                'top_signal_text': smoothed_sentiments[ticker]['top_text'],
                'signal_count': smoothed_sentiments[ticker]['signal_count']
            })

        df = pd.DataFrame(rows).sort_values(by='weight', ascending=False).reset_index(drop=True)
        return df

    def _apply_bounds_and_normalize(self, raw_weights: dict) -> dict:
        weights = dict(raw_weights)
        total = sum(weights.values())
        if total <= 0:
            return {t: self.base_weight for t in self.universe}

        for t in weights:
            weights[t] /= total

        for _ in range(10):
            clamped = False
            for t in weights:
                if weights[t] < self.min_weight:
                    weights[t] = self.min_weight
                    clamped = True
                elif weights[t] > self.max_weight:
                    weights[t] = self.max_weight
                    clamped = True

            curr_sum = sum(weights.values())
            if abs(curr_sum - 1.0) < 1e-6 or not clamped:
                break
            for t in weights:
                weights[t] /= curr_sum

        final_sum = sum(weights.values())
        for t in weights:
            weights[t] = round(weights[t] / final_sum, 6)

        return weights

    def compute_historical_weight_trajectory(self, signals_df: pd.DataFrame, num_steps: int = 15) -> pd.DataFrame:
        if signals_df.empty:
            return pd.DataFrame()

        df_sorted = signals_df.copy()
        df_sorted['dt'] = pd.to_datetime(df_sorted['timestamp'], format='mixed', errors='coerce', utc=True)
        df_sorted['dt'] = df_sorted['dt'].dt.tz_localize(None)
        df_sorted = df_sorted.dropna(subset=['dt']).sort_values(by='dt')

        if df_sorted.empty:
            return pd.DataFrame()

        start_time = df_sorted['dt'].min()
        end_time = df_sorted['dt'].max()

        if start_time == end_time or pd.isna(start_time):
            start_time = end_time - timedelta(days=7)

        timestamps = pd.date_range(start=start_time, end=end_time, periods=num_steps)
        history_records = []

        for ts in timestamps:
            ts_pydt = ts.to_pydatetime()
            past_signals = df_sorted[df_sorted['dt'] <= ts]
            sentiments = self.compute_smoothed_sentiments(past_signals, reference_time=ts_pydt)
            rebalanced_df = self.rebalance(sentiments)

            for _, row in rebalanced_df.iterrows():
                history_records.append({
                    'timestamp': ts.strftime('%Y-%m-%d %H:%M'),
                    'ticker': row['ticker'],
                    'weight_pct': row['weight_pct'],
                    'sentiment': row['smoothed_sentiment'],
                    'benchmark_pct': row['benchmark_pct']
                })

        return pd.DataFrame(history_records)

    def simulate_performance(self, history_df: pd.DataFrame, initial_capital: float = 100000.0) -> pd.DataFrame:
        if history_df.empty:
            return pd.DataFrame()

        timestamps = sorted(history_df['timestamp'].unique())
        if len(timestamps) < 2:
            return pd.DataFrame()

        sim_records = []
        portfolio_val = initial_capital
        benchmark_val = initial_capital

        sim_records.append({
            'timestamp': timestamps[0],
            'Tactical_Portfolio': portfolio_val,
            'Equal_Weight_Benchmark': benchmark_val,
            'Alpha_Pct': 0.0,
            'Excess_Return': 0.0
        })

        np.random.seed(42)

        for i in range(1, len(timestamps)):
            ts = timestamps[i]
            prev_weights = history_df[history_df['timestamp'] == timestamps[i-1]].set_index('ticker')['weight_pct'] / 100.0
            
            step_returns = {}
            for ticker in self.universe:
                sent = history_df[(history_df['timestamp'] == ts) & (history_df['ticker'] == ticker)]['sentiment'].values
                sent_val = sent[0] if len(sent) > 0 else 0.0
                ret = 0.0005 + (0.012 * sent_val) + np.random.normal(0, 0.004)
                step_returns[ticker] = ret

            port_ret = sum(prev_weights.get(t, self.base_weight) * step_returns[t] for t in self.universe)
            bench_ret = sum(self.base_weight * step_returns[t] for t in self.universe)

            portfolio_val *= (1.0 + port_ret)
            benchmark_val *= (1.0 + bench_ret)
            alpha_pct = ((portfolio_val - benchmark_val) / initial_capital) * 100.0

            sim_records.append({
                'timestamp': ts,
                'Tactical_Portfolio': round(portfolio_val, 2),
                'Equal_Weight_Benchmark': round(benchmark_val, 2),
                'Alpha_Pct': round(alpha_pct, 2),
                'Excess_Return': round(portfolio_val - benchmark_val, 2)
            })

        return pd.DataFrame(sim_records)

def run_tactical_rebalance(alpha: float = 0.75, save_to_db: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    signals = load_signals()
    signals_df = pd.DataFrame(signals)
    rebalancer = TacticalRebalancer(alpha=alpha)
    
    if signals_df.empty:
        default_sentiments = {t: {'score': 0.0, 'top_text': 'No signals logged', 'signal_count': 0} for t in MOCK_INDEX_UNIVERSE}
        current_weights = rebalancer.rebalance(default_sentiments)
        return current_weights, pd.DataFrame(), pd.DataFrame()

    sentiments = rebalancer.compute_smoothed_sentiments(signals_df)
    current_weights_df = rebalancer.rebalance(sentiments)
    history_df = rebalancer.compute_historical_weight_trajectory(signals_df, num_steps=20)
    perf_df = rebalancer.simulate_performance(history_df)

    if save_to_db:
        now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        db_records = []
        for _, row in current_weights_df.iterrows():
            db_records.append({
                'timestamp': now_str,
                'ticker': row['ticker'],
                'weight': row['weight'],
                'smoothed_sentiment': row['smoothed_sentiment'],
                'top_signal_text': row['top_signal_text']
            })
        save_weights_snapshot(db_records)

    return current_weights_df, history_df, perf_df

if __name__ == "__main__":
    weights, hist, perf = run_tactical_rebalance()
    print("✅ Module A: Tactical Index Rebalancer execution complete.")
