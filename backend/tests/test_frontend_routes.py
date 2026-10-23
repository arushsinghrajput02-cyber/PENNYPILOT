def test_frontend_routes_served(client):
    routes = [
        "/",
        "/index.html",
        "/login.html",
        "/register.html",
        "/dashboard.html",
        "/transactions.html",
        "/budgets.html",
        "/analytics.html",
        "/goals.html",
        "/challenges.html",
        "/css/style.css",
        "/css/components.css",
        "/css/dashboard.css",
        "/js/api.js",
        "/js/auth.js",
        "/js/dashboard.js",
        "/js/transactions.js",
        "/js/budgets.js",
        "/js/analytics.js",
        "/js/goals.js",
        "/js/challenges.js"
    ]
    for route in routes:
        res = client.get(route)
        assert res.status_code == 200, f"Failed on route {route}: status {res.status_code}"
