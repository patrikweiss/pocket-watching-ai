# Pocket Watching AI

An AI-powered wealth estimation engine for rappers, producers, media personalities, and boxers. Type a name and get a net worth range, income breakdown, ownership analysis, and AI-generated reasoning.

Built for content creators who need credible, sourced estimates instead of guesswork.

---

## What It Does

- Estimates net worth for 111+ entertainment figures using public data + music industry heuristics
- Breaks down income — streaming, touring, merch, other
- Analyzes ownership — masters, publishing, label situation
- Explains reasoning with AI-generated "Why this estimate?" narrative
- Accepts user refinement — type facts like "owns masters" and the estimate adjusts live
- Uses real data — YouTube subscriber counts, Deezer fan metrics, published tour grosses

---

## Accuracy & Validation

Holdout test: **25 of 111 people** were randomly removed from the database, then re-estimated blind by the pattern estimator. Predictions were compared to their actual manual estimates.

### Overall Results

| Metric | Value |
|--------|-------|
| Median relative error | **40%** |
| Predictions within 2× of actual | **80% (20/25)** |
| Log-scale MAE | **0.29** (≈2× average error factor) |

### Results by Category

| Category | Count | Median Error | Within 2× |
|----------|-------|-------------|-----------|
| Rappers | 15 | 34% | 87% |
| Producers | 3 | 42% | 67% |
| Singers | 3 | 30% | 100% |
| Media personalities | 2 | 45% | 50% |
| **Boxers** | **2** | **78%** | **0%** |

### Known Limitations

**Boxers are systematically hard to estimate.** Floyd Mayweather's 88% error comes from his $1.2B career earnings dwarfing every other boxer in the reference pool. Available signals (YouTube, ownership status) don't correlate with fight-purse wealth. Fixing this requires adding career-earnings data for athletes.

**Underground producers** can be overestimated because the reference pool is small.

All estimates are **ranges with confidence scores**, not point values.

---

## How It Works
User searches name
↓
Database lookup (111 people)
├── Found → exact researched estimate
└── Not found → pattern estimation
↓
Pattern Estimator V2

Fetch real YouTube subscribers, views

Find similar database entries (log-scale similarity)

Weight by similarity, average net worths

Apply ownership adjustment
↓
Refinement Engine (optional)

User adds facts ("owns masters")

±15% adjustments with explanations
↓
DeepSeek AI reasoning

Generates natural-language explanation
↓
Output: range + confidence + reasoning

text

### Core Heuristics

- **Streaming payouts**: $0.0035–$0.007 per stream (blended platform average)
- **Ownership splits**: 80–90% for independent owners, 15–20% for major-label artists
- **Catalog valuation**: 15–20× annual royalties for owned catalogs
- **Touring**: 35–45% net margin on gross box office
- **Taxes & team**: ~45% effective deduction before net income

### Pattern Estimator

- Uses log-scale similarity (net worth spans $75K to $2.6B)
- Compares YouTube subscribers + views against database reference entries
- Averages top 5 matches weighted by similarity
- Applies neutral ownership multiplier (0.5) when unknown
- Caps subscriber-based scaling at 0.5–2× to prevent extreme predictions

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — dashboard
- **YouTube Data API v3** — real subscriber/view data
- **Deezer API** — fan metrics (free, no key)
- **DeepSeek API** — AI-generated explanations
- **Pandas / NumPy** — data processing

---

## Project Structure
pocket-watching-ai/
├── app.py # Streamlit dashboard
├── validate.py # Holdout validation script
├── README.md
├── src/
│ ├── engines.py # FullEngine + PatternEstimator + RefinementEngine
│ ├── data_collection.py # YouTube + Deezer collectors
│ └── reasoning.py # DeepSeek explanation layer
├── config/
│ ├── heuristics.py # Music industry rates
│ └── estimation_rules.py # Tax/fee rules
└── data/
└── manual_estimates/
└── manual_knowledge.json # 111-person database