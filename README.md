# PennyPilot — Smart Student Finance Platform 🧭

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-17%20Passed-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

> **B.Tech Computer Science & Engineering Capstone Project**  
> A full-stack student personal finance platform designed specifically to tackle campus pocket-money management, mid-month cash depletion, discretionary spending, and savings discipline.

---

## 1. Product Vision

College students face unique financial hurdles: irregular allowances, unpredictable mess/canteen bills, peer group hangouts, exam fees, and unexpected tech/hardware expenses. Traditional personal finance and budgeting tools are designed for salaried professionals with fixed monthly paychecks, complex tax deductions, and mortgage payments.

**PennyPilot** addresses the reality of student life:
- **Zero Financial Blindness:** Stop running out of cash ten days before your monthly allowance or stipend arrives.
- **Rule-Based Guidance:** Objective spend coaching without deceptive AI claims or black-box algorithms.
- **Campus Problem Focus:** Built around canteen expenses, hostel dues, textbook xerox, tech accessories, and student travel goals.

---

## 2. Distinctive Student-First Features

### 🛡️ Feature 1: Survival Mode Daily Limit Engine
When funds run low, PennyPilot calculates an exact, realistic daily spending cap:
$$\text{Spendable Balance} = \text{Total Income} - \text{Total Outflow} - \text{Reserved Buffer}$$
$$\text{Suggested Daily Limit} = \frac{\text{Spendable Balance}}{\text{Remaining Days in Current Month}}$$
- **Customizable Emergency Reserve:** Lock away funds for semester registration, mess bills, or medical emergencies.
- **Adaptive Status Alerts:** Categorized into **Safe**, **Caution**, **Critical**, or **Depleted** to prevent cash starvation.

### ⚡ Feature 2: Smart Spend Coach
A deterministic, rule-based spending intelligence engine comparing actual transactional records:
- **Month-over-Month Surges:** Detects when discretionary categories spike by $\ge 20\%$ compared to the previous month (e.g., *"You spent 25% more on Food & Dining than last month"*).
- **Proactive Budget Warnings:** Triggers cautionary alerts when any category reaches $80\%$ utilization.
- **Micro-Savings Opportunity:** Translates daily campus habit tweaks into real monthly savings (e.g., *"Reducing optional snacks by ₹40/day saves ₹1,200/month"*).

### ⚖️ Feature 3: Needs vs Wants Classifier (50/30/20 Rule)
Enables students to classify each expenditure into **Needs** (hostel, mess, books, transit pass), **Wants** (cafe hangouts, Zomato, OTT subscriptions), or **Savings** (deposits into goals). Provides real-time visual balance tracking against the standard 50/30/20 financial rule.

### 🏆 Feature 4: No-Spend Sprint Challenges
Allows students to launch 7-day or weekend challenges (e.g., *"7-Day Zero Food Delivery"*, *"Weekend Discretionary Cap < ₹500"*). Progress is verified dynamically against real database transactions logged during the challenge window.

### 📈 Feature 5: Transparent Month-End Spending Forecast
Calculates end-of-month run-rate spend based on days elapsed and average daily burn:
$$\text{Projected Spend} = \left(\frac{\text{Current Spent}}{\text{Days Elapsed}}\right) \times \text{Total Days in Month}$$
Displays a confidence and data-sufficiency note (e.g., preliminary pace vs stabilized 15+ day consistency).

### 🩺 Feature 6: Objective Financial Health Score (0–100)
A 100-point composite financial health rating based on:
1. **Budget Adherence (30 pts):** Staying disciplined within monthly category caps.
2. **Savings Rate (30 pts):** Saving $\ge 20\%$ of allowance and stipends.
3. **Needs vs Wants Discipline (20 pts):** Keeping discretionary wants $\le 30\%$ of total spend.
4. **Emergency Liquidity Buffer (20 pts):** Maintaining a safe cash cushion.

---

## 3. Technology Stack & Architecture

### Backend
- **Framework:** Python FastAPI (modern async REST API)
- **Database ORM:** SQLAlchemy 2.0 with declarative models
- **Database:** SQLite (local zero-configuration embedded storage with multi-thread safety)
- **Validation:** Pydantic v2 schemas and validators
- **Security:** Bcrypt password hashing (`bcrypt`) & JWT token authentication (`pyjwt`)
- **Testing:** Pytest & HTTPX test client

### Frontend
- **Markup & Styling:** Semantic HTML5, CSS3 with a custom fintech design system
- **Scripting:** Modular Vanilla JavaScript (ES6+), zero heavy framework dependencies
- **Visualizations:** Chart.js (interactive line, bar, pie, and doughnut charts)
- **Icons:** Lucide Icons
- **Design Tokens:**
  - Deep Midnight Navy Background: `#0B1020`
  - Elevated Cards: `#141B2D`
  - Primary Electric Violet: `#8B5CF6`
  - Secondary Mint Green: `#34D399`
  - Text Primary: `#F8FAFC`
  - Text Muted: `#94A3B8`

---

## 4. Project Structure

```text
PennyPilot/
├── backend/
│   ├── config.py                 # Application settings & environment loader
│   ├── database.py               # SQLAlchemy engine & session dependency
│   ├── models.py                 # Database models (User, Transaction, Budget, Goal, Challenge)
│   ├── schemas.py                # Pydantic validation schemas
│   ├── security.py               # Bcrypt hashing & JWT session management
│   ├── main.py                   # FastAPI application & static route handlers
│   ├── routers/
│   │   ├── auth.py               # User registration, login, and profile
│   │   ├── transactions.py       # Transaction CRUD, filtering, search, CSV export
│   │   ├── budgets.py            # Budget allocation & utilization checks
│   │   ├── analytics.py          # Dashboard summaries, KPIs, trends, survival mode
│   │   ├── goals.py              # Savings goals & contribution deposits
│   │   ├── challenges.py         # No-spend challenge management
│   │   └── demo.py               # 1-click realistic demo environment seeder
│   ├── services/
│   │   ├── insights.py           # Smart Spend Coach rule engine
│   │   ├── forecasting.py        # Month-end burn-rate forecaster
│   │   └── financial_score.py    # 0-100 Financial Health score calculator
│   └── tests/
│       ├── conftest.py           # Pytest test harness with in-memory SQLite
│       ├── test_auth.py          # Registration & authentication tests
│       ├── test_transactions.py  # Transaction CRUD & user isolation tests
│       ├── test_budgets.py       # Budget utilization & warning tests
│       ├── test_goals.py         # Savings goal & contribution tests
│       ├── test_analytics.py     # Analytics & survival mode calculation tests
│       ├── test_challenges.py    # Challenge tracking against real transactions
│       ├── test_demo_and_insights.py # Demo data & Smart Spend Coach tests
│       └── test_frontend_routes.py   # Frontend static routing tests
├── frontend/
│   ├── index.html                # Product landing page & feature showcase
│   ├── login.html                # Student login & 1-click demo access
│   ├── register.html             # Student account registration
│   ├── dashboard.html            # Main financial command center
│   ├── transactions.html         # Transaction ledger with search, filters & CSV
│   ├── budgets.html              # Monthly & category budget planner
│   ├── analytics.html            # Comprehensive financial reports & charts
│   ├── goals.html                # Savings goals & deposit tracker
│   ├── challenges.html           # No-spend sprint challenges
│   ├── css/
│   │   ├── style.css             # Design system variables, buttons, forms, badges
│   │   ├── components.css        # Cards, modals, progress bars, tables
│   │   └── dashboard.css         # Sidebar, top header, responsive grid layouts
│   └── js/
│       ├── api.js                # API client, JWT handler, INR formatter, toasts
│       ├── auth.js               # Route guarding, user state & demo triggers
│       ├── dashboard.js          # Main dashboard data loading & charts
│       ├── transactions.js       # Transaction ledger controller & CSV export
│       ├── budgets.js            # Budget planner controller & status alerts
│       ├── analytics.js          # Analytics reports & Chart.js rendering
│       ├── goals.js              # Savings goals controller & deposits
│       └── challenges.js         # Challenge controller & real transaction audits
├── requirements.txt              # Production & test dependencies
├── .env.example                  # Environment variable template
├── .env                          # Local development environment configuration
├── .gitignore                    # Git ignore file
└── README.md                     # Comprehensive project documentation
```

---

## 5. Prerequisites

- **Operating System:** macOS (Apple Silicon or Intel), Linux, or Windows 10/11
- **Python:** Python 3.9 or newer (verified on Python 3.9.6)
- **Web Browser:** Any modern browser (Chrome, Safari, Firefox, Edge)

---

## 6. Setup & Installation Instructions (macOS)

### Step 1: Open Terminal and Navigate to Project
```bash
cd /Users/arushsingh/Desktop/FastAPI
```

### Step 2: Create a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Verify Environment Configuration
A `.env` file is pre-configured with secure development defaults:
```bash
cat .env
```
*(Optionally copy from `.env.example` if deploying to a new location).*

---

## 7. Running the Application

### Option A: Unified Full-Stack Server (Recommended)
FastAPI is pre-configured to mount and serve the frontend directly on port 8000:
```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Start server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (or `http://localhost:8000`)

### Option B: Standalone Frontend Server (Decoupled Mode)
If you prefer running the frontend on a separate port (e.g., port 3000):
```bash
# Terminal 1: Backend API
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend Static Server
cd frontend
python3 -m http.server 3000
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser. CORS is pre-configured for port 3000, 5500, and 8000.

---

## 8. Interactive Evaluation & Demo Credentials

To experience PennyPilot with realistic Indian college engineering data:

1. Open **[http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)**.
2. Click the green button: **"⚡ One-Click Demo Student Login"**.
3. You will be instantly logged in as **Alex Sharma (B.Tech CSE)** with pre-seeded data:
   - Monthly allowance (₹12,000) & FastAPI consulting stipend (₹7,500)
   - Realistic hostel rent, mess fees, campus chai, textbooks, and metro pass
   - Active budgets with 80% threshold tracking
   - Active savings goals: *"MacBook Air M3 for Final Year Project"* and *"Graduation Trip"*
   - Active no-spend challenges: *"Zero Food Delivery Week"* and *"Weekend Cap < ₹500"*
   - Full Survival Mode calculation & Smart Spend Coach insights

*Manual Demo Account Credentials:*
- **Email:** `alex.cse@pennypilot.in`
- **Password:** `demopennypilot`

---

## 9. Interactive API Documentation

FastAPI provides automatic interactive API documentation:
- **Swagger UI:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **ReDoc:** [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)
- **OpenAPI JSON:** [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)

---

## 10. Running the Test Suite

PennyPilot includes a comprehensive automated test suite covering authentication, multi-user data isolation, budget limits, calculations, and CSV exports:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all 17 tests with verbose output
pytest -v
```

### Test Coverage Highlights:
- `test_auth.py`: User registration, duplicate email handling, login validation, protected `/me` endpoint.
- `test_transactions.py`: Income/expense creation, validation of non-negative amounts, search, filters, pagination, user data isolation, CSV export.
- `test_budgets.py`: Category limits, live spending calculations, 80% warning triggers, exceeded budget notifications.
- `test_goals.py`: Savings goal creation, contribution deposits, remaining balances, status auto-completion.
- `test_analytics.py`: Real-time KPI summaries, Needs vs Wants 50/30/20 proportions, Survival Mode daily limit math, Month-End run-rate forecasting, Financial Health score.
- `test_challenges.py`: No-spend challenge verification against actual database transactions.
- `test_demo_and_insights.py`: Seeding realistic student sample data & rule-based Smart Spend Coach insights.
- `test_frontend_routes.py`: Verifies all HTML, CSS, and JS routes return 200 OK.

---

## 11. Known Limitations & Future Enhancements

- **SMS/UPI Auto-Parsing:** For local academic demonstration, transaction logging is manual or seeded via demo mode. Integrating SMS parser APIs for automated Indian UPI transaction scraping would be a valuable production enhancement.
- **Push Notifications:** Web Push notifications for the 80% budget threshold could be added using Service Workers.
- **Collaborative Group Splitting:** A future module for splitting hostel grocery and cafe bills with hostel roommates.

---

## 12. License & Academic Attribution

Developed as a college B.Tech Computer Science & Engineering capstone project. Open for educational, academic, and non-commercial portfolio demonstration.
