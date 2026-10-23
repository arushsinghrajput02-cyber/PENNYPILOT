from datetime import date, timedelta


def test_savings_goals_crud_and_contributions(client, auth_headers):
    target_date = date.today() + timedelta(days=90)
    # Create goal with initial deposit
    res = client.post(
        "/api/goals",
        headers=auth_headers,
        json={
            "title": "Coding Laptop Fund",
            "target_amount": 50000.0,
            "target_date": str(target_date),
            "category": "Tech & Gadgets",
            "initial_deposit": 10000.0
        }
    )
    assert res.status_code == 201
    goal = res.json()
    assert goal["target_amount"] == 50000.0
    assert goal["current_amount"] == 10000.0
    assert goal["remaining_amount"] == 40000.0
    assert goal["percentage_complete"] == 20.0
    assert goal["status"] == "active"
    assert len(goal["contributions"]) == 1

    goal_id = goal["id"]

    # Make an additional contribution
    contrib_res = client.post(
        f"/api/goals/{goal_id}/contribute",
        headers=auth_headers,
        json={
            "amount": 40000.0,
            "note": "Internship bonus"
        }
    )
    assert contrib_res.status_code == 200
    updated_goal = contrib_res.json()
    assert updated_goal["current_amount"] == 50000.0
    assert updated_goal["remaining_amount"] == 0.0
    assert updated_goal["percentage_complete"] == 100.0
    assert updated_goal["status"] == "completed"
