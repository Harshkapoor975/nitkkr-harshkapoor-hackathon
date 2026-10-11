# 🧠 Custom NLP Engine (Explainable AI Architecture)

In modern hackathons, calling an external black-box LLM API (like OpenAI or Gemini) is often considered the "new baseline." To demonstrate a deeper understanding of Machine Learning and Data Science, we have built a **fully local, custom Natural Language Processing (NLP) pipeline**.

This engine requires no external API keys, runs entirely on the edge, is hyper-fast, and most importantly: it utilizes **Explainable AI (XAI)** principles so we always know *why* a decision was made.

## ⚙️ How the Custom Engine Works

The pipeline is implemented in `scripts/custom_nlp_engine.py` and consists of five robust layers:

### Layer 0: Text Preprocessing & Normalization (New)
Raw data from social media is extremely noisy.
- **Mechanism:** Uses Regex to strip out URLs, normalize whitespace, and remove garbage artifacts before any NLP operations occur.
- **Advantage:** Prevents the downstream heuristic models from failing on messy data.

### Layer 1: Dictionary-Based Entity Resolution (NER)
Instead of relying on a slow Transformer model to find company names, we built a highly optimized dictionary matcher using Regular Expressions (`re`). 
- **Mechanism:** It scans the unstructured text against our internal `config.TICKERS` alias dictionary with strict word boundaries.
- **Example:** If it sees "Tim Cook" or "Apple", it resolves the entity directly to the ticker `AAPL`.

### Layer 2: Lexicon-Based Sentiment Analysis (VADER w/ Financial Jargon)
We abandoned black-box sentiment classification in favor of **VADER**. However, standard VADER underestimates financial jargon (e.g., "downgraded", "slashed").
- **Mechanism:** We injected a custom **Financial Lexicon** (inspired by the Loughran-McDonald dictionary) directly into VADER's memory.
- **Output:** Returns a normalized compound score between `-1.0` (extreme negative) and `+1.0` (extreme positive) that properly penalizes financial bad news.

### Layer 3: Keyword-Density Zero-Shot Classification w/ Confidence Scoring
To categorize the type of financial event, we built a heuristic Keyword-Density model.
- **Mechanism:** We defined overlapping semantic clusters. The engine counts the frequency of these clustered keywords in the text.
- **Confidence Routing:** Instead of just guessing, it outputs a Confidence Score. If the confidence is `0.0` (no keywords found), a real production system could route this specific text to a Human-In-The-Loop (HITL) or an LLM fallback!

### Layer 4: Heuristic Impact Scoring
Risk severity is calculated using an arithmetic formula rather than a hidden neural activation.
- **Mechanism:** The base impact starts at 3. It scales up proportionally to the absolute extremity of the VADER sentiment score. Finally, it scans for "impact multipliers" (e.g., "slashed", "soars", "massive") and adds penalty points.

## 🚀 Running the Custom Engine

1. First, make sure you have the local NLP libraries installed:
```powershell
pip install -r requirements.txt
# (or explicitly: pip install vaderSentiment nltk)
```

2. Clear out the old LLM data (optional, but recommended for a clean test):
```powershell
rm data/signals.db
rm data/signals.csv
```

3. Run the blazing-fast local engine:
```powershell
python scripts/custom_nlp_engine.py
```

4. Refresh your Streamlit dashboard (`streamlit run app.py`) to see the custom engine's results!
