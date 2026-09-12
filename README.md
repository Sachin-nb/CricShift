# 🏏 Momentum Shift Detector in Cricket Matches (Ball-by-Ball)

A production-ready, real-time cricket analytics web application that simulates match progression ball-by-ball, computes dynamic momentum indices, tracks win probabilities, and detects turning points — all visualized through a premium dark-themed sports analytics dashboard.

---

## ✨ Features

### Analytics Engine
- **Rolling Match Features**: Current Run Rate, Required Run Rate, Runs in Last Over, Wickets in Last N Balls, Dot Ball %, Boundary Frequency, Pressure Index, Run Rate Acceleration
- **Dynamic Momentum Index**: Ranges from -100 (bowling dominance) to +100 (batting dominance), computed as a weighted composite of normalized signals
- **Win Probability Engine**: Rule-based probability calculator using sigmoid-transformed factors (chase progress, wickets, rate gap, momentum, match stage)
- **Shift Detection**: Configurable algorithm that triggers alerts when significant momentum swings occur based on defined thresholds

### Dashboard
- **Match Header** — Teams, Score, Overs, Run Rate, Required Rate, Target
- **Live Momentum Graph** — Over vs Momentum Index with color-coded zones
- **Win Probability Graph** — Batting vs Bowling team probability curves
- **Ball-by-Ball Feed** — Color-coded delivery feed with boundary and wicket highlights
- **Turning Points Timeline** — Severity-classified events with explanations
- **Key Statistical Cards** — Last 5 Overs Runs, Dot Ball %, Pressure Index, Momentum Score, Boundary Frequency, RR Acceleration
- **Momentum Indicator Bar** — Visual gauge showing bowling ↔ batting dominance

### Playback Controls
- **Auto-play** with adjustable speed (0.2x to 3.0x)
- **Manual Navigation** — Step forward/backward one ball at a time
- **Progress Scrubbing** — Click anywhere on the progress bar to jump to that point
- **Innings Tabs** — Switch between 1st and 2nd innings
- **CSV Upload** — Upload your own ball-by-ball dataset

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation

```bash
# Navigate to the project
cd cricket-analytics

# Install dependencies
pip install -r requirements.txt

# Generate sample match data (already included)
python generate_sample_data.py

# Start the application
python app.py
```

### Open Dashboard
```
http://localhost:5000
```

Click **"Sample Match"** to load the pre-built T20 match, or **"Upload CSV"** to use your own dataset.

---

## 📊 CSV Dataset Format

Your CSV file must include these columns:

| Column | Type | Description |
|--------|------|-------------|
| `innings` | int | Innings number (1 or 2) |
| `over` | int | Over number (0-indexed) |
| `ball` | int | Ball number within the over (1-6) |
| `batting_team` | str | Name of the batting team |
| `bowling_team` | str | Name of the bowling team |
| `batsman` | str | Batsman on strike |
| `bowler` | str | Bowler name |
| `runs_off_bat` | int | Runs scored off the bat |
| `extras` | int | Extra runs (wides, no-balls, etc.) |
| `total_runs` | int | Total runs from this delivery |
| `is_wicket` | int | 1 if a wicket fell, 0 otherwise |

Optional columns: `match_id`, `dismissal_kind`, `player_dismissed`

---

## 🏗 Architecture

```
cricket-analytics/
├── app.py                     # Flask application & REST API
├── config.py                  # Centralized configuration & thresholds
├── requirements.txt           # Python dependencies
├── generate_sample_data.py    # Sample T20 match generator
├── data/
│   └── sample_match.csv       # Generated sample dataset
├── engine/
│   ├── __init__.py            # Engine package exports
│   ├── data_loader.py         # CSV parsing & validation
│   ├── feature_engine.py      # Rolling feature computation
│   ├── momentum_model.py      # Momentum Index calculation
│   ├── win_probability.py     # Win probability engine
│   └── shift_detector.py      # Momentum shift detection
├── static/
│   ├── css/dashboard.css      # Dark-themed dashboard styles
│   └── js/dashboard.js        # Frontend interactivity & Plotly charts
└── templates/
    └── index.html             # Dashboard HTML template
```

### Layer Separation

| Layer | Module(s) | Purpose |
|-------|-----------|---------|
| **Data Layer** | `data_loader.py` | CSV parsing, validation, normalization |
| **Feature Engineering** | `feature_engine.py` | Rolling metrics computation |
| **Momentum Model** | `momentum_model.py` | Composite momentum index |
| **Detection Engine** | `shift_detector.py` | Shift detection & classification |
| **Probability Engine** | `win_probability.py` | Win probability estimation |
| **API Layer** | `app.py` | Flask routes & data serialization |
| **UI Layer** | `templates/`, `static/` | Dashboard rendering & interactivity |

---

## ⚙️ Configuration

All thresholds and weights are configurable in `config.py`:

```python
# Momentum weights (sum to 1.0)
MOMENTUM_WEIGHTS = {
    "run_rate_factor":       0.25,
    "recent_scoring":        0.20,
    "wicket_pressure":       0.20,
    "dot_ball_pressure":     0.15,
    "boundary_momentum":     0.10,
    "run_rate_acceleration": 0.10,
}

# Shift detection
SHIFT_THRESHOLD = 25         # Minimum change to trigger alert
RAPID_SHIFT_THRESHOLD = 40   # Threshold for "critical" classification
SHIFT_COOLDOWN_BALLS = 6     # Minimum balls between alerts
```

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard page |
| `/api/load-default` | POST | Load sample match |
| `/api/upload` | POST | Upload custom CSV |
| `/api/match-info` | GET | Current match metadata |
| `/api/innings/<n>/balls` | GET | All balls for an innings |
| `/api/innings/<n>/ball/<i>` | GET | Single ball data |
| `/api/innings/<n>/state/<i>` | GET | Full match state at ball position |
| `/api/innings/<n>/summary` | GET | Innings summary stats |

---

## 📝 License

This project is open-source and available for educational and analytics purposes.
