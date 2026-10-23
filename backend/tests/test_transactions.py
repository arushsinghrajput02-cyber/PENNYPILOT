from datetime import date


def test_create_income_and_expense_transactions(client, auth_headers):
    # Income
    income_res = client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 10000.0,
            "transaction_type": "income",
            "category": "Pocket Money / Allowance",
            "description": "Monthly allowance",
            "transaction_date": str(date.today()),
            "need_or_want": "need",
            "is_recurring": True
        }
    )
    assert income_res.status_code == 201
    inc_data = income_res.json()
    assert inc_data["amount"] == 10000.0
    assert inc_data["transaction_type"] == "income"

    # Expense
    expense_res = client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 450.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "description": "Canteen burger & cold coffee",
            "transaction_date": str(date.today()),
            "need_or_want": "want",
            "is_recurring": False
        }
    )
    assert expense_res.status_code == 201
    exp_data = expense_res.json()
    assert exp_data["amount"] == 450.0
    assert exp_data["need_or_want"] == "want"


def test_invalid_negative_amount_transaction(client, auth_headers):
    res = client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": -500.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "transaction_date": str(date.today())
        }
    )
    assert res.status_code == 422  # Pydantic validation error


def test_update_and_delete_transaction(client, auth_headers):
    # Create
    create_res = client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 300.0,
            "transaction_type": "expense",
            "category": "Transport & Travel",
            "description": "Auto rickshaw fare",
            "transaction_date": str(date.today()),
            "need_or_want": "need"
        }
    )
    tx_id = create_res.json()["id"]

    # Update
    update_res = client.put(
        f"/api/transactions/{tx_id}",
        headers=auth_headers,
        json={"amount": 350.0, "description": "Shared cab fare"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["amount"] == 350.0
    assert update_res.json()["description"] == "Shared cab fare"

    # Delete
    del_res = client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/transactions/{tx_id}", headers=auth_headers)
    assert get_res.status_code == 404


def test_user_data_isolation(client, auth_headers, second_auth_headers):
    # User 1 creates transaction
    res1 = client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 1200.0,
            "transaction_type": "expense",
            "category": "Books & Academics",
            "description": "Algorithms Book",
            "transaction_date": str(date.today()),
            "need_or_want": "need"
        }
    )
    tx_id = res1.json()["id"]

    # User 2 tries to read User 1's transaction
    res2 = client.get(f"/api/transactions/{tx_id}", headers=second_auth_headers)
    assert res2.status_code == 404

    # User 2 lists transactions - should be empty
    list_res = client.get("/api/transactions", headers=second_auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 0

    # User 2 tries to delete User 1's transaction
    del_res = client.delete(f"/api/transactions/{tx_id}", headers=second_auth_headers)
    assert del_res.status_code == 404


def test_export_transactions_csv(client, auth_headers):
    # Add a transaction first
    client.post(
        "/api/transactions",
        headers=auth_headers,
        json={
            "amount": 250.0,
            "transaction_type": "expense",
            "category": "Food & Dining",
            "description": "Mess snack",
            "transaction_date": str(date.today()),
            "need_or_want": "need"
        }
    )

    res = client.get("/api/transactions/export/csv", headers=auth_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    text = res.text
    assert "Transaction ID,Date,Type,Category,Description,Amount (INR)" in text
    assert "Mess snack" in text
    assert "250.00" in text
