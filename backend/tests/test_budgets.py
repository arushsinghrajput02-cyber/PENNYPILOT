from datetime import date


def test_budget_creation_and_utilization(client, auth_headers):
    today = date.today()
    # 1. Set overall budget of 5000
    b_res = client.post(
        "/api/budgets",
        headers=auth_headers,
        json={
            "category": "Overall",
            "monthly_limit": 5000.0,
            "month": today.month,
            "year": today.year
        }
    )
    assert b_res.status_code == 201
    assert b_res.json()["monthly_limit"] == 5000.0
    assert b_res.json()["status"] == "normal"

    # 2. Add an expense of 4200 (84% of budget -> status "warning")
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 4200.0,
            "transaction_type": "expense",
            "category": "Hostel & Rent",
            "transaction_date": str(today),
            "need_or_want": "need"
        }
    )

    # 3. Check budget status
    check_res = client.get(f"/api/budgets?month={today.month}&year={today.year}", headers=auth_headers)
    assert check_res.status_code == 200
    items = check_res.json()
    assert len(items) == 1
    overall = items[0]
    assert overall["spent_amount"] == 4200.0
    assert overall["percentage_used"] == 84.0
    assert overall["status"] == "warning"

    # 4. Add another expense of 1000 (total 5200 -> status "exceeded")
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 1000.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "transaction_date": str(today),
            "need_or_want": "need"
        }
    )

    check_res2 = client.get(f"/api/budgets?month={today.month}&year={today.year}", headers=auth_headers)
    items2 = check_res2.json()
    assert items2[0]["spent_amount"] == 5200.0
    assert items2[0]["percentage_used"] == 104.0
    assert items2[0]["status"] == "exceeded"
