# 🏏 CricShift — Real-Time Cricket Analytics & Momentum Shift Detection

A production-ready, real-time cricket analytics web application designed to analyze and visualize match progression ball-by-ball.

**CricShift** computes dynamic momentum indices, tracks win probabilities, analyzes match statistics, detects important turning points, and provides an interactive premium dark-themed cricket analytics dashboard.

The application combines a **Next.js frontend**, **FastAPI backend**, **SQLite/Prisma database**, machine-learning/analytics components, and cricket datasets to provide a complete end-to-end analytics platform.

---

## ✨ Features

### 🧠 Analytics Engine

- **Rolling Match Features**
  - Current Run Rate
  - Required Run Rate
  - Runs in Last Over
  - Wickets in Last N Balls
  - Dot Ball Percentage
  - Boundary Frequency
  - Pressure Index
  - Run Rate Acceleration

- **Dynamic Momentum Index**
  - Ranges from **-100 to +100**
  - Negative values represent bowling dominance
  - Positive values represent batting dominance
  - Calculated using a weighted combination of normalized match signals

- **Win Probability Engine**
  - Calculates estimated win probability
  - Considers chase progress
  - Wickets remaining
  - Required rate
  - Current rate
  - Momentum
  - Match stage

- **Momentum Shift Detection**
  - Detects significant changes in match momentum
  - Configurable shift thresholds
  - Identifies rapid/critical momentum changes
  - Provides turning-point information

---

# 📊 Dashboard

The CricShift dashboard provides an interactive real-time cricket analytics experience.

### 🏏 Match Header

Displays:

- Batting team
- Bowling team
- Current score
- Overs
- Current Run Rate
- Required Run Rate
- Target
- Match status

### 📈 Live Momentum Graph

Visualizes momentum throughout the innings:

- Over-by-over momentum
- Batting dominance
- Bowling dominance
- Momentum shift points
- Momentum zones

### 🎯 Win Probability Graph

Displays changing win probabilities for both teams throughout the match.

### 🏏 Ball-by-Ball Feed

Provides a delivery-by-delivery match feed with:

- Runs
- Extras
- Boundaries
- Wickets
- Batsman
- Bowler
- Over and ball information

### 🔄 Turning Points Timeline

Highlights important match-changing moments and classifies their severity.

### 📋 Key Statistical Cards

Displays important live statistics such as:

- Last 5 Overs Runs
- Dot Ball %
- Pressure Index
- Momentum Score
- Boundary Frequency
- Run Rate Acceleration

### ⚖️ Momentum Indicator

A visual momentum gauge showing the current balance between:

**Bowling Dominance ↔ Batting Dominance**

---

# 🎮 Match Playback Controls

CricShift provides interactive match playback functionality.

### ▶️ Auto Play

Automatically progresses through the match ball-by-ball.

Supported playback speeds include:

- 0.2x
- 0.5x
- 1.0x
- 1.5x
- 2.0x
- 3.0x

### ⏭️ Manual Navigation

Navigate through individual deliveries:

- Previous ball
- Next ball

### 📍 Progress Scrubbing

Jump directly to any point in the match using the progress bar.

### 🏏 Innings Tabs

Switch between:

- 1st Innings
- 2nd Innings

### 📁 CSV Upload

Upload your own ball-by-ball cricket dataset for analysis.

---

# 🏗️ Technology Stack

## Frontend

- **Next.js**
- **React**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **Plotly / interactive visualizations**

## Backend

- **Python**
- **FastAPI**
- **Uvicorn**
- REST APIs
- WebSocket support for live match functionality

## Database

- **SQLite**
- **Prisma ORM**

## Data & Analytics

- **Pandas**
- **NumPy**
- Cricket analytics engine
- Momentum calculations
- Win probability calculations
- Match simulation
- Statistical analysis

## Large File Storage

- **Git LFS**

Git LFS is used for large project datasets such as:

```text
data/features/feature_dataset.csv
```

---

# 🚀 Quick Start

## Prerequisites

Before running CricShift, make sure the following are installed:

- Python 3.8 or higher
- Node.js 18 or higher
- npm
- Git
- Git LFS

---

# 1️⃣ Clone the Repository

Clone the project from GitHub:

```bash
git clone https://github.com/Sachin-nb/CricShift.git
```

Navigate into the project:

```bash
cd CricShift
```

---

# 2️⃣ Initialize Git LFS

CricShift uses Git LFS for large datasets.

Run:

```bash
git lfs install
git lfs pull
```

This downloads the actual large files managed through Git LFS.

---

# 3️⃣ Configure the Backend Environment

The FastAPI backend uses environment variables for configuration.

Create a `.env` file in the project root:

```text
CricShift/
└── .env
```

The environment file should contain the configuration required by the backend.

For security reasons, **do not commit your real `.env` file to GitHub** if it contains:

- API keys
- Passwords
- SMTP credentials
- JWT secrets
- Other sensitive credentials

Use `.env.example` to document required environment variables without exposing secret values.

---

# 4️⃣ Set Up the Python Environment

From the project root:

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

---

# 5️⃣ Start the FastAPI Backend

Start the FastAPI server using Uvicorn:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

FastAPI automatically provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

Keep this terminal running.

---

# 6️⃣ Set Up the Next.js Frontend

Open a **new terminal**.

Navigate to the Next.js application:

```powershell
cd Cricshift-main
```

Install the Node.js dependencies:

```powershell
npm ci
```

Generate the Prisma client:

```powershell
npm run db:generate
```

---

# 7️⃣ Configure the Frontend Database

Create:

```text
Cricshift-main/.env
```

Add:

```env
DATABASE_URL=file:../db/custom.db
```

The project includes the SQLite database:

```text
Cricshift-main/db/custom.db
```

This database is part of the project and should not be deleted or reset unless you intentionally want to modify the project's database.

---

# 8️⃣ Start the Next.js Frontend

From:

```text
Cricshift-main/
```

run:

```powershell
npm run dev
```

The frontend will start on:

```text
http://localhost:3000
```

Open the application in your browser:

**http://localhost:3000**

---

# 🔥 Running CricShift

CricShift currently uses **two development servers**.

You need both servers running.

## Terminal 1 — FastAPI Backend

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

---

## Terminal 2 — Next.js Frontend

```powershell
cd Cricshift-main
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

# 🌐 Application URLs

| Service | URL |
|---|---|
| 🏏 CricShift Frontend | `http://localhost:3000` |
| ⚡ FastAPI Backend | `http://127.0.0.1:8000` |
| 📚 FastAPI Swagger Docs | `http://127.0.0.1:8000/docs` |

### Application Flow

```text
Browser
   │
   ▼
Next.js Frontend
localhost:3000
   │
   │ REST API / WebSocket
   ▼
FastAPI Backend
127.0.0.1:8000
   │
   ├── Analytics Engine
   ├── Prediction Engine
   ├── Match Simulation
   ├── Live Match Services
   ├── Authentication
   │
   ▼
SQLite / Prisma
custom.db
```

---

# 📊 CSV Dataset Format

CricShift supports ball-by-ball cricket datasets.

Your CSV file should include the following columns:

| Column | Type | Description |
|---|---|---|
| `innings` | int | Innings number (1 or 2) |
| `over` | int | Over number |
| `ball` | int | Ball number within the over |
| `batting_team` | str | Name of the batting team |
| `bowling_team` | str | Name of the bowling team |
| `batsman` | str | Batsman on strike |
| `bowler` | str | Bowler name |
| `runs_off_bat` | int | Runs scored from the bat |
| `extras` | int | Extra runs |
| `total_runs` | int | Total runs from the delivery |
| `is_wicket` | int | `1` if a wicket fell, otherwise `0` |

### Optional Columns

The following columns can also be included:

```text
match_id
dismissal_kind
player_dismissed
```

---

# 📁 Project Structure

The CricShift repository contains both the analytics/backend components and the Next.js frontend.

```text
CricShift/
│
├── backend/
│   ├── main.py
│   └── ...
│
├── analytics/
│   └── ...
│
├── engine/
│   └── ...
│
├── etl/
│   └── ...
│
├── feature_engineering/
│   └── ...
│
├── models/
│   └── ...
│
├── data/
│   ├── features/
│   │   └── feature_dataset.csv
│   └── ...
│
├── tests/
│   └── ...
│
├── templates/
│   └── ...
│
├── static/
│   └── ...
│
├── Cricshift-main/
│   │
│   ├── db/
│   │   └── custom.db
│   │
│   ├── public/
│   │   ├── home-bg.mp4
│   │   └── stadium-bg.jpg
│   │
│   ├── prisma/
│   │   └── ...
│   │
│   ├── src/
│   │   └── ...
│   │
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── ...
│
├── config.py
├── requirements.txt
├── generate_sample_data.py
├── app.py
├── .gitignore
├── .gitattributes
└── README.md
```

> **Note:** `node_modules`, `.next`, `.venv`, caches, and other generated files are intentionally excluded from Git because they can be recreated from the project's dependency/configuration files.

---

# 🧩 System Architecture

CricShift follows a layered architecture.

```text
                    ┌──────────────────────────┐
                    │      Next.js Frontend    │
                    │                          │
                    │  Dashboard               │
                    │  Charts                  │
                    │  Match Playback          │
                    │  Authentication          │
                    │  Live Match UI           │
                    └────────────┬─────────────┘
                                 │
                         REST API / WebSocket
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      FastAPI Backend     │
                    │                          │
                    │  Authentication          │
                    │  Analytics APIs          │
                    │  Prediction APIs         │
                    │  Simulation APIs         │
                    │  Live Match APIs         │
                    └────────────┬─────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
             ▼                   ▼                   ▼
       Analytics Engine    Prediction Engine    Data Layer
             │                   │                   │
             ▼                   ▼                   ▼
        Features          Win Probability      CSV / SQLite
        Momentum          Momentum Model       Prisma
        Shift Detection   Simulation
```

---

# 🧠 Analytics Pipeline

The analytics pipeline processes cricket data through multiple stages:

```text
Ball-by-Ball Data
       │
       ▼
Data Loading & Validation
       │
       ▼
Feature Engineering
       │
       ▼
Rolling Match Statistics
       │
       ├───────────────┐
       ▼               ▼
Momentum Model    Win Probability
       │               │
       └───────┬───────┘
               ▼
       Shift Detection
               │
               ▼
       Match Insights
               │
               ▼
        Next.js Dashboard
```

---

# 📈 Momentum Index

The Dynamic Momentum Index represents the current balance of match momentum.

The scale is:

```text
-100                         0                         +100
│                            │                            │
Bowling Dominance       Balanced Match          Batting Dominance
```

The momentum calculation uses weighted signals such as:

- Run rate
- Recent scoring
- Wicket pressure
- Dot-ball pressure
- Boundary momentum
- Run-rate acceleration

---

# ⚙️ Configuration

Analytics thresholds and model weights can be configured through the project's configuration system.

Example momentum weights:

```python
MOMENTUM_WEIGHTS = {
    "run_rate_factor":       0.25,
    "recent_scoring":        0.20,
    "wicket_pressure":       0.20,
    "dot_ball_pressure":     0.15,
    "boundary_momentum":     0.10,
    "run_rate_acceleration": 0.10,
}
```

Example shift detection configuration:

```python
SHIFT_THRESHOLD = 25
RAPID_SHIFT_THRESHOLD = 40
SHIFT_COOLDOWN_BALLS = 6
```

### Configuration Meaning

| Setting | Description |
|---|---|
| `SHIFT_THRESHOLD` | Minimum momentum change required to trigger a shift |
| `RAPID_SHIFT_THRESHOLD` | Threshold used for rapid/critical shifts |
| `SHIFT_COOLDOWN_BALLS` | Minimum number of balls between shift alerts |

---

# 🔌 Backend API

The FastAPI backend provides APIs for authentication, analytics, predictions, simulation, commentary, and live match functionality.

Important API groups include:

### Health

```text
GET /api/health
```

### Analytics

```text
/api/analytics/players
/api/analytics/teams
/api/analytics/venues
```

### Predictions

```text
/api/predict/win
/api/predict/momentum
/api/predict/match
```

### Recommendations

```text
/api/recommend/player
```

### Explainability

```text
/api/explain
```

### Simulation

```text
/api/simulate
/api/simulate/monte-carlo
```

### Commentary

```text
/api/commentary/generate
```

### Live Matches

```text
/api/live/matches
/api/live/match/{id}
/api/live/match/{id}/intelligence
```

### Live WebSocket

```text
/ws/live/{matchId}
```

For the complete interactive API specification, open:

```text
http://127.0.0.1:8000/docs
```

---

# 🗄️ Database

CricShift uses **SQLite** with **Prisma** for database management.

The project's database is located at:

```text
Cricshift-main/db/custom.db
```

The database is included as part of the project.

### Generate Prisma Client

```powershell
cd Cricshift-main
npm run db:generate
```

### Important

The existing `custom.db` contains project data and should not be deleted or reset during normal setup.

Avoid running destructive database commands such as:

```text
npm run db:reset
```

unless you intentionally want to reset the database.

---

# 📊 Large Dataset & Git LFS

The repository contains large datasets that cannot be stored efficiently using normal Git object storage.

Git LFS is used for:

```text
data/features/feature_dataset.csv
```

After cloning the repository, make sure Git LFS is installed and pull the large files:

```powershell
git lfs install
git lfs pull
```

Verify tracked LFS files with:

```powershell
git lfs ls-files
```

---

# 🎥 Frontend Assets

CricShift includes important frontend assets such as:

```text
Cricshift-main/public/home-bg.mp4
Cricshift-main/public/stadium-bg.jpg
```

These assets are required by the frontend experience and are included in the repository.

---

# 🔐 Authentication & Admin

CricShift includes authentication and role-based access functionality.

The application supports:

- User registration
- User login
- Authentication sessions
- Role-based access
- Admin functionality

Admin access is controlled through the backend environment configuration.

For local development, configure the appropriate administrator email through:

```env
ADMIN_EMAILS=your-admin-email@example.com
```

Do not expose sensitive authentication credentials or secrets in the public repository.

---

# 🛠️ Development Commands

## FastAPI Backend

Start the development server:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Next.js Frontend

Start the development server:

```powershell
cd Cricshift-main
npm run dev
```

---

## Install Frontend Dependencies

```powershell
cd Cricshift-main
npm ci
```

---

## Generate Prisma Client

```powershell
cd Cricshift-main
npm run db:generate
```

---

## Build the Frontend

```powershell
cd Cricshift-main
npm run build
```

---

## Lint the Frontend

```powershell
cd Cricshift-main
npm run lint
```

---

# 🧪 Testing

The repository includes testing and verification scripts.

Examples include:

```text
tests/
validate.py
verify_5c.py
debug_e2e.py
debug_match.py
debug_phase5b.py
debug_populated_match.py
test_rapidapi.py
```

Run the appropriate test or validation script according to the feature being tested.

---

# 📦 Generated Files

The following directories are intentionally excluded from Git:

```text
.venv/
node_modules/
.next/
__pycache__/
```

These directories contain locally generated dependencies, caches, or build output.

They can be recreated using:

### Python

```powershell
python -m venv .venv
pip install -r requirements.txt
```

### Node.js

```powershell
cd Cricshift-main
npm ci
```

### Next.js

```powershell
npm run dev
```

---

# 🔒 Environment & Security

Never commit sensitive credentials to GitHub.

Sensitive information may include:

```text
API keys
Passwords
SMTP passwords
JWT secrets
OAuth credentials
Private tokens
Database credentials
```

Keep real secrets inside local `.env` files.

Use `.env.example` to document the required environment variables without exposing their actual values.

---

# 🚀 Complete Setup Summary

For a quick setup after cloning:

### Terminal 1 — Backend

```powershell
git clone https://github.com/Sachin-nb/CricShift.git
cd CricShift

git lfs install
git lfs pull

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — Frontend

```powershell
cd CricShift\Cricshift-main

npm ci
npm run db:generate
npm run dev
```

Then open:

```text
http://localhost:3000
```

---

# 🏏 CricShift Architecture at a Glance

```text
                         CRICSHIFT
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
       NEXT.JS FRONTEND             FASTAPI BACKEND
        localhost:3000             localhost:8000
              │                           │
              │                           ├── Authentication
              │                           ├── Analytics
              │                           ├── Predictions
              │                           ├── Momentum
              │                           ├── Simulation
              │                           ├── Recommendations
              │                           ├── Commentary
              │                           └── Live Match APIs
              │                           │
              └──────────────┬────────────┘
                             │
                             ▼
                       DATA & MODELS
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
            SQLite       CSV Datasets     ML/Analytics
           custom.db    feature_dataset   Models
                             │
                             ▼
                    CRICKET MATCH INSIGHTS
```

---

# 🎯 Project Goals

CricShift aims to make cricket analytics more interactive, understandable, and useful by combining:

- Ball-by-ball match analysis
- Dynamic momentum tracking
- Win probability estimation
- Turning-point detection
- Match simulation
- Statistical analytics
- Player and team insights
- Real-time match intelligence
- Interactive data visualization

---

# 📝 License

This project is open-source and available for educational, research, and cricket analytics purposes.

---

# 👨‍💻 Author

**Sachin Nb**

### CricShift

Real-Time Cricket Analytics & Momentum Intelligence Platform

🏏 Analyze the match.  
📊 Understand the numbers.  
🔥 Detect the momentum shift.
