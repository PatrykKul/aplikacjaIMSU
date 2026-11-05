from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_database_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_unexpected_error_hides_exception_details() -> None:
    app = create_app()

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret detail")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert "secret detail" not in response.text
    assert response.json() == {"code": "INTERNAL_ERROR"}
