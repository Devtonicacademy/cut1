# LivelyBorg AI: Next-Gen Football Intelligence & Smart Staking Platform (Lagos, Nigeria)

[![Python Tests](https://img.shields.io/badge/Python_Tests-15%20Passed-10b981.svg)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)]()
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015%20PWA-black.svg)]()
[![Market](https://img.shields.io/badge/Market-Lagos%2C%20Nigeria-f59e0b.svg)]()

> A premier sports intelligence and bankroll co-pilot engineered to rival legacy platforms (SportyBet, Bet9ja) and obsolete prediction sites (Forebet, Predictz, Betensured). Powered by **Dixon-Coles bivariate Poisson modeling**, **rolling xG analytics**, **Google Gemini contextual analysis**, **Fractional Kelly Criterion bankroll preservation**, and **instant booking code generation**.

---

## 🚀 The Strategic Advantage

In Lagos, Nigeria, millions of football fans wager daily on SportyBet and Bet9ja, while relying on prediction sites like Forebet or chaotic Telegram tipsters. This creates 3 massive pain points:

1. **Obsolete Prediction Models**: Existing sites use simple goal averages or static Poisson models. They ignore **Expected Goals (xG)**, lineup rotations, travel fatigue, and **Expected Value (+EV)**—recommending 1.20 favorites even when the odds offer no mathematical edge.
2. **Bankroll Annihilation**: 90%+ of Nigerian punters blow their capital because of emotional staking on 25-game accumulators. No platform tells them **how much Naira to stake** based on their individual bankroll.
3. **Friction & Scams**: Prediction sites output plain text, forcing bettors to manually find games on SportyBet or Bet9ja. Meanwhile, Telegram tipsters delete losing slips and falsify records.

### How LivelyBorg AI Solves This
- **True +EV Detection**: Calculates true match probabilities and compares them against live SportyBet and Bet9ja market odds to expose real value ($EV \ge +5\%$).
- **Fractional Kelly Staking (₦)**: Computes optimal Naira stakes per play with Conservative, Balanced, and Aggressive risk profiles.
- **Smart 2-Odds Banker & "Cut-1" Slip Doctor**: Combines high-confidence value plays and flags risky legs to protect accumulators from cutting.
- **1-Click Booking Code Exporter**: Translates slips into ready-to-load codes for SportyBet (`SB-XXXXX`) and Bet9ja (`B9-XXXXX`).
- **Viral Growth Loops**: Branded WhatsApp Status and Twitter (X) shareable graphic tickets + the **₦1,000 → ₦50,000 Public Compounding Ladder Challenge**.
- **Admin Superpowers**: 1-Click Multi-Channel Broadcaster (Web PWA, Telegram VIP Channel, WhatsApp) + Automated Result Grader.
- **Anti-Scam Verified Track Record**: Every tip is permanently locked and timestamped before kickoff, with public ROI and AI post-mortems for losses.

---

## 📐 Mathematical Formulation

### 1. Dixon-Coles Bivariate Poisson
Models goal distributions between home team $i$ and away team $j$:
$$\lambda = \alpha_i \cdot \beta_j \cdot \gamma \cdot \text{avg}_{\text{home}}$$
$$\mu = \alpha_j \cdot \beta_i \cdot \text{avg}_{\text{away}}$$
Adjusted for low-score correlation ($0-0, 1-0, 0-1, 1-1$) via the parameter $\tau(x, y)$ with $\rho = -0.11$.

### 2. Expected Value (+EV)
$$\text{EV} = (P_{\text{model}} \times \text{Bookmaker Odds}) - 1$$
Only plays with positive mathematical expectation ($\text{EV} \ge +4.0\%$) are presented to users.

### 3. Fractional Kelly Criterion (Naira Calibrated)
$$f^* = \frac{b \cdot p - q}{b} \times k_{\text{fraction}}$$
where $b = \text{Odds} - 1$, $p = P_{\text{model}}$, $q = 1 - p$.
- **Conservative Profile**: $k = 0.15$, max single bet $2.5\%$, max portfolio risk $12\%$.
- **Balanced Profile**: $k = 0.25$, max single bet $4.5\%$, max portfolio risk $20\%$.
- **Aggressive Profile**: $k = 0.40$, max single bet $7.0\%$, max portfolio risk $35\%$.
- Stakes are rounded to practical Naira multiples (e.g. ₦100, ₦250, ₦500).

---

## 📂 Repository Structure

```
lively-borg/
├── apps/
│   ├── api/                           # Python FastAPI Predictive Backend
│   │   ├── app/
│   │   │   ├── models/schemas.py      # Pydantic schemas (Fixtures, Bankroll, Slips)
│   │   │   ├── services/
│   │   │   │   ├── dixon_coles.py     # Bivariate Poisson predictive engine
│   │   │   │   ├── xg_analyzer.py     # Rolling xG, form decay, fatigue weighting
│   │   │   │   ├── gemini_analyzer.py # Google Gemini 2.5 contextual reasoning
│   │   │   │   ├── ev_engine.py       # Live odds vs model comparison (+EV)
│   │   │   │   ├── kelly_engine.py    # Naira Fractional Kelly bankroll manager
│   │   │   │   ├── accas_optimizer.py # Smart Accumulator & Cut-1 Doctor
│   │   │   │   ├── tracker_service.py # Verified public track record & ROI ledger
│   │   │   │   ├── admin_service.py   # 1-Click Multi-Channel Broadcaster
│   │   │   │   └── fixture_service.py # Match dataset & odds pipeline
│   │   │   └── main.py                # REST API router & endpoints
│   │   └── requirements.txt
│   ├── web/                           # Next.js 15 App Router (Mobile-First PWA)
│   │   ├── src/
│   │   │   ├── app/page.tsx           # Main unified sports intelligence portal
│   │   │   ├── components/
│   │   │   │   ├── Header.tsx         # Live bankroll switcher & Data-Saver mode
│   │   │   │   ├── MatchCard.tsx      # Probability bars & Gemini tactical drawer
│   │   │   │   ├── KellyCalculator.tsx# Interactive Naira bankroll slider
│   │   │   │   ├── SmartAccaModal.tsx # Daily 2-odds banker & Cut-1 alerts
│   │   │   │   ├── WhatsAppSlipGenerator.tsx # Viral WhatsApp & Twitter ticket cards
│   │   │   │   ├── TrackRecordView.tsx# Audited public PnL ledger
│   │   │   │   └── AdminBroadcastModal.tsx # Admin 1-click broadcaster
│   │   └── package.json
│   └── bot/
│       └── telegram_bot.py            # Telegram VIP Alert Bot
└── tests/                             # Automated test suite (15 passing tests)
    ├── test_dixon_coles.py
    ├── test_ev_and_kelly.py
    ├── test_accas_and_api.py
    └── test_api_endpoints.py
```

---

## 🛠️ Quickstart Instructions

### 1. Run Automated Test Suite
```bash
# Activate virtual environment
.\.venv\Scripts\python -m pytest -v tests
```

### 2. Start the FastAPI Predictive Backend
```bash
.\.venv\Scripts\python -m uvicorn apps.api.app.main:app --reload --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/v1/health`

### 3. Start the Next.js Mobile-First Web PWA
```bash
cd apps/web
npm run dev
```
Open `http://localhost:3000` to interact with the full dashboard.

### 4. Test the Telegram VIP Bot
```bash
.\.venv\Scripts\python apps/bot/telegram_bot.py
```
