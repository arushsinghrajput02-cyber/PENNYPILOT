from datetime import date, timedelta


def test_challenges_tracking_with_real_transactions(client, auth_headers):
    today = date.today()
    start_date = today - timedelta(days=2)
    end_date = today + timedelta(days=5)

    # Create a 7-day challenge with ₹500 cap on Food & Dining
    c_res = client.post(
        "/api/challenges",
        headers=auth_headers,
        json={
            "title": "Control Canteen Spending",
            "description": "Stay under ₹500 for canteen food this week",
            "category": "Food & Dining",
            "target_amount": 500.0,
            "start_date": str(start_date),
            "end_date": str(end_date)
        }
    )
    assert c_res.status_code == 201
    c_data = c_res.json()
    assert c_data["current_spent"] == 0.0
    assert c_data["is_on_track"] is True

    c_id = c_data["id"]

    # Log an expense in Food & Dining of ₹200 (within ₹500 cap)
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 200.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "transaction_date": str(today),
            "need_or_want": "want"
        }
    )

    # Check challenge - should show 200 spent, on track
    list_res = client.get("/api/challenges", headers=auth_headers)
    assert list_res.status_code == 200
    items = list_res.json()
    target_c = next((item for item in items if item["id"] == c_id), None)
    assert target_c is not None
    assert target_c["current_spent"] == 200.0
    assert target_c["is_on_track"] is True

    # Log an additional expense of ₹400 (total ₹600 > ₹500 cap)
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 400.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "transaction_date": str(today),
            "need_or_want": "want"
        }
    )

    # Re-check challenge - now exceeded and is_on_track False
    list_res2 = client.get("/api/challenges", headers=auth_headers)
    target_c2 = next((item for item in list_res2.json() if item["id"] == c_id), None)
    assert target_c2["current_spent"] == 600.0
    assert target_c2["is_on_track"] is False
