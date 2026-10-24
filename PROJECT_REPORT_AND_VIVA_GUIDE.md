# PennyPilot — B.Tech CSE Project Report & Viva Defense Guide 🎓

This comprehensive documentation serves as a presentation handbook, technical report, and viva voce preparation guide for the **PennyPilot** Student Finance Platform.

---

## 1. Executive Summary

| Project Detail | Description |
| :--- | :--- |
| **Project Title** | PennyPilot — Smart Student Finance Platform |
| **Domain** | Financial Technology (FinTech), Web Engineering, Software Architecture |
| **Target Audience** | College & University Students managing pocket money, stipends, and hostel expenses |
| **Backend Stack** | Python, FastAPI, SQLAlchemy 2.0 ORM, SQLite, Pydantic v2, PyJWT, Bcrypt |
| **Frontend Stack** | HTML5, CSS3 Custom Fintech System, Vanilla JavaScript (ES6+), Chart.js, Lucide Icons |
| **Testing** | Pytest, HTTPX Test Client (17 Automated Integration Tests) |
| **DevOps / CI/CD** | GitHub Actions Automated Testing Matrix, Docker, Docker Compose |

---

## 2. High-Level Architecture & System Flow

```
+----------------------------------------------------------------------------------+
|                             CLIENT TIER (BROWSER)                                |
|  HTML5 + CSS3 (Design Tokens) + Vanilla JS Controllers + Chart.js Data Visuals   |
+----------------------------------------------------------------------------------+
                                        │
                         HTTP REST Requests (JSON)
                    Authorization: Bearer <JWT Token>
                                        │
                                        ▼
+----------------------------------------------------------------------------------+
|                            FASTAPI APPLICATION TIER                              |
|                                                                                  |
|   ┌────────────────┐   ┌────────────────┐   ┌────────────────┐   ┌───────────┐   |
|   │ CORS / SecOps  │──>│ JWT Auth Guard │──>│ Pydantic DTOs  │──>│ Endpoint  │   |
|   │ Middleware     │   │ & Bcrypt Hash  │   │ Validation     │   │ Routers   │   |
|   └────────────────┘   └────────────────┘   └────────────────┘   └───────────┘   |
|                                                                        │         |
|   ┌─────────────────────────────────────────────────────────────────┐  │         |
|   │                      BUSINESS LOGIC SERVICES                     │  │         |
|   │  • Smart Spend Coach (MoM Surge & 80% Budget Threshold Engine)  │<─┘         |
|   │  • Survival Mode Daily Limit Engine                             │            |
|   │  • Month-End Run-Rate Burn Forecaster                           │            |
|   │  • 0-100 Composite Financial Health Score Calculator            │            |
|   └─────────────────────────────────────────────────────────────────┘            |
|                                        │                                         |
|                                        ▼                                         |
|   ┌─────────────────────────────────────────────────────────────────┐            |
|   │                     DATA ACCESS LAYER (ORM)                     │            |
|   │              SQLAlchemy 2.0 Models & Session Maker              │            |
|   └─────────────────────────────────────────────────────────────────┘            |
+----------------------------------------------------------------------------------+
                                        │
                                        ▼
+----------------------------------------------------------------------------------+
|                             DATABASE STORAGE TIER                                |
|          SQLite Relational Database (Multi-Thread Safe Engine)                   |
|    Tables: users, transactions, budgets, savings_goals, goal_contributions,     |
|            challenges                                                            |
+----------------------------------------------------------------------------------+
```

---

## 3. Entity-Relationship (ER) Schema Specification

```
   ┌──────────────────────┐
   │        USERS         │
   ├──────────────────────┤
   │ id (PK)              │
   │ name                 │
   │ email (Unique, Index)│
   │ password_hash        │
   │ monthly_reserved_amt │
   │ created_at           │
   └──────────┬───────────┘
              │ 1
              │
              ├───────────────────────────────┐
              │ *                             │ *
   ┌──────────▼───────────┐        ┌──────────▼───────────┐
   │     TRANSACTIONS     │        │       BUDGETS        │
   ├──────────────────────┤        ├──────────────────────┤
   │ id (PK)              │        │ id (PK)              │
   │ user_id (FK)         │        │ user_id (FK)         │
   │ amount (Float > 0)   │        │ category             │
   │ transaction_type     │        │ monthly_limit        │
   │ category             │        │ month, year          │
   │ need_or_want         │        │ created_at           │
   │ is_recurring         │        └──────────────────────┘
   │ transaction_date     │
   └──────────────────────┘
              │ 1
              │
              ├───────────────────────────────┐
              │ *                             │ *
   ┌──────────▼───────────┐        ┌──────────▼───────────┐
   │    SAVINGS_GOALS     │        │      CHALLENGES      │
   ├──────────────────────┤        ├──────────────────────┤
   │ id (PK)              │        │ id (PK)              │
   │ user_id (FK)         │        │ user_id (FK)         │
   │ title, target_amount │        │ title, category      │
   │ current_amount       │        │ target_amount        │
   │ target_date, status  │        │ start_date, end_date │
   └──────────┬───────────┘        │ status (active/done) │
              │ 1                  └──────────────────────┘
              │
              │ *
   ┌──────────▼───────────┐
   │  GOAL_CONTRIBUTIONS  │
   ├──────────────────────┤
   │ id (PK)              │
   │ goal_id (FK), user_id│
   │ amount, note, date   │
   └──────────────────────┘
```

---

## 4. Mathematical Formulations of Key Algorithms

### 4.1 Survival Mode Daily Allowance
$$\text{Available Net Balance} = \sum \text{Income} - \sum \text{Expenses}$$
$$\text{Spendable Balance} = \text{Available Net Balance} - \text{Reserved Buffer}$$
$$\text{Days Remaining} = \max(1, \text{Total Days In Month} - \text{Current Day} + 1)$$
$$\text{Suggested Daily Limit} = \begin{cases} \frac{\text{Spendable Balance}}{\text{Days Remaining}} & \text{if Spendable Balance} > 0 \\ 0 & \text{otherwise} \end{cases}$$

### 4.2 Month-End Run-Rate Forecast
$$\text{Daily Burn Rate} = \frac{\sum \text{Current Month Expenses}}{\max(1, \text{Days Elapsed})}$$
$$\text{Projected Total Spend} = \text{Daily Burn Rate} \times \text{Total Days in Month}$$

### 4.3 Financial Health Score (0 to 100)
$$\text{Score} = \text{Budget Adherence (30)} + \text{Savings Rate (30)} + \text{Needs vs Wants (20)} + \text{Cash Buffer (20)}$$
- **Budget Adherence:** $\le 75\% \to 30$ pts, $\le 90\% \to 25$ pts, $\le 100\% \to 15$ pts, $>100\% \to \max(5, 30 - 0.5(\% - 100))$.
- **Savings Rate:** $\ge 30\% \to 30$ pts, $\ge 20\% \to 25$ pts, $\ge 10\% \to 18$ pts, $>0\% \to 12$ pts, $\le 0\% \to 5$ pts.
- **Needs vs Wants:** Wants $\le 30\% \to 20$ pts, $\le 45\% \to 15$ pts, $\le 60\% \to 10$ pts, $>60\% \to 5$ pts.
- **Cash Cushion:** $\ge ₹10,000 \to 20$ pts, $\ge ₹4,000 \to 16$ pts, $\ge ₹1,000 \to 11$ pts, $>0 \to 6$ pts, $\le 0 \to 2$ pts.

---

## 5. Viva Voce Questions & Model Answers

### Q1: Why did you choose FastAPI over Flask or Django?
> **Answer:** FastAPI utilizes asynchronous I/O (`asyncio`) and Python type hints, offering performance on par with NodeJS and Go. Unlike Flask, it includes automatic Pydantic data validation, OpenAPI (Swagger) generation out of the box, and dependency injection, which simplifies session management and authorization guards. Unlike monolithic Django, FastAPI is lightweight and avoids unnecessary overhead for a decoupled REST architecture.

### Q2: Why did you opt for Vanilla JavaScript instead of React or Next.js?
> **Answer:** For a college finance application, bundle size, fast loading speeds, and zero build tool overhead are critical advantages. Vanilla JavaScript (ES6+) with modern modular patterns (`async/await`, Fetch API, native DOM manipulation) provides sub-millisecond execution without npm dependency bloat or virtual DOM reconciliation overhead, while seamlessly integrating with Chart.js and Lucide icons.

### Q3: How do you guarantee multi-user data isolation and security?
> **Answer:** Every authenticated request must pass a Bearer JWT token in the `Authorization` header. FastAPI's `get_current_user` dependency decodes the token, extracts the user ID, and injects the verified `User` model. Crucially, **all database queries strictly filter by `user_id == current_user.id`**. Even if an attacker guesses another user's transaction ID (IDOR attack), the query returns `404 Not Found`.

### Q4: How is password storage handled?
> **Answer:** Passwords are never stored in plain text. We utilize `bcrypt` with adaptive salting (`bcrypt.gensalt()`). Bcrypt includes a cryptographic work factor that protects against pre-computed rainbow table and GPU dictionary attacks.

### Q5: How do you prevent negative or irrational transactions?
> **Answer:** Validation is enforced at the API boundary via Pydantic v2 schemas:
> ```python
> amount: float = Field(..., gt=0, description="Amount must be positive")
> ```
> Any negative or zero value is rejected immediately with HTTP 422 Unprocessable Entity before reaching the database.
