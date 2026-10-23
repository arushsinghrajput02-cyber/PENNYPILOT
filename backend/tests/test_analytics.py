from datetime import date


def test_analytics_calculations_and_survival_mode(client, auth_headers):
    today = date.today()

    # Log income of ₹15,000
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 15000.0,
            "transaction_type": "income",
            "category": "Pocket Money / Allowance",
            "transaction_date": str(today),
            "need_or_want": "need"
        }
    )

    # Log expense of ₹5,000 (Needs)
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 5000.0,
            "transaction_type": "expense",
            "category": "Hostel & Rent",
            "transaction_date": str(today),
            "need_or_want": "need"
        }
    )

    # Log expense of ₹2,500 (Wants)
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 2500.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "transaction_date": str(today),
            "need_or_want": "want"
        }
    )

    # Overview
    overview_res = client.get(f"/api/analytics/overview?month={today.month}&year={today.year}", headers=auth_headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["current_balance"] == 7500.0
    assert overview["monthly_income"] == 15000.0
    assert overview["monthly_expenses"] == 7500.0
    assert overview["monthly_savings"] == 7500.0
    assert overview["savings_rate"] == 50.0

    # Needs vs Wants
    nw_res = client.get(f"/api/analytics/needs-wants?month={today.month}&year={today.year}", headers=auth_headers)
    assert nw_res.status_code == 200
    nw_data = nw_res.json()
    assert nw_data["needs_amount"] == 5000.0
    assert nw_data["wants_amount"] == 2500.0
    assert round(nw_data["needs_percentage"], 0) == 67.0
    assert round(nw_data["wants_percentage"], 0) == 33.0

    # Survival Mode
    # Reserve 1500
    surv_res = client.get(f"/api/analytics/survival-mode?reserve=1500&month={today.month}&year={today.year}", headers=auth_headers)
    assert surv_res.status_code == 200
    surv_data = surv_res.json()
    assert surv_data["current_balance"] == 7500.0
    assert surv_data["reserved_amount"] == 1500.0
    assert surv_data["spendable_balance"] == 6000.0
    assert surv_data["suggested_daily_limit"] > 0
    assert surv_data["status"] in ["safe", "caution", "critical"]

    # Month-end Forecast
    fc_res = client.get(f"/api/analytics/forecast?month={today.month}&year={today.year}", headers=auth_headers)
    assert fc_res.status_code == 200
    fc_data = fc_res.json()
    assert fc_data["current_spent_this_month"] == 7500.0
    assert fc_data["projected_end_of_month_spend"] > 0
    assert "confidence_note" in fc_data

    # Financial Health Score
    fs_res = client.get(f"/api/analytics/financial-score?month={today.month}&year={today.year}", headers=auth_headers)
    assert fs_res.status_code == 200
    fs_data = fs_res.json()
    assert 0 <= fs_data["overall_score"] <= 100
    assert "factors" in fs_data
    assert "insights" in fs_data
