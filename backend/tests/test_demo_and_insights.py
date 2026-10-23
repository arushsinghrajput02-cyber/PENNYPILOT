def test_demo_user_seed_and_insights(client):
    # 1. Login as demo user
    demo_res = client.post("/api/demo/login-demo")
    assert demo_res.status_code == 200
    data = demo_res.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check overview
    ov_res = client.get("/api/analytics/overview", headers=headers)
    assert ov_res.status_code == 200
    ov = ov_res.json()
    assert ov["monthly_income"] > 0
    assert ov["monthly_expenses"] > 0
    assert ov["current_balance"] > 0

    # 3. Check insights
    in_res = client.get("/api/analytics/insights", headers=headers)
    assert in_res.status_code == 200
    insights = in_res.json()
    assert isinstance(insights, list)
    assert len(insights) > 0

    # 4. Check survival mode
    sm_res = client.get("/api/analytics/survival-mode", headers=headers)
    assert sm_res.status_code == 200
    sm = sm_res.json()
    assert sm["suggested_daily_limit"] > 0
    assert sm["reserved_amount"] == 2500.0

    # 5. Check savings goals
    goals_res = client.get("/api/goals", headers=headers)
    assert goals_res.status_code == 200
    goals = goals_res.json()
    assert len(goals) >= 2
