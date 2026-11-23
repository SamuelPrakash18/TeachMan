import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.routes = {
            (method, route.path)
            for route in app.routes
            for method in route.methods
        }

    def test_auth_and_public_routes_exist(self) -> None:
        expected = {
            ("POST", "/api/auth/register/tutor"),
            ("POST", "/api/auth/register/parent"),
            ("POST", "/api/auth/login"),
            ("GET", "/api/auth/me"),
            ("PUT", "/api/auth/change-password"),
            ("GET", "/api/public/tutors"),
            ("GET", "/api/public/batches"),
            ("POST", "/api/enrollments/request"),
        }
        self.assertTrue(expected.issubset(self.routes))

    def test_cors_preflight_allows_configured_local_origin(self) -> None:
        response = self.client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")
        self.assertIn("POST", response.headers["access-control-allow-methods"])
        self.assertIn("authorization", response.headers["access-control-allow-headers"].lower())


if __name__ == "__main__":
    unittest.main()
