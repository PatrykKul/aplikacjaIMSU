from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.errors import AppError
from app.main import create_app


class Payload(BaseModel):
    email: str


def make_client() -> TestClient:
    app = create_app()

    @app.get("/app-error")
    def app_error() -> None:
        raise AppError(409, "SOMETHING_TAKEN")

    @app.post("/validated")
    def validated(payload: Payload) -> None:
        return None

    return TestClient(app, raise_server_exceptions=False)


def test_app_error_returns_code() -> None:
    response = make_client().get("/app-error")
    assert response.status_code == 409
    assert response.json() == {"code": "SOMETHING_TAKEN"}


def test_validation_error_lists_fields() -> None:
    response = make_client().post("/validated", json={})
    assert response.status_code == 422
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "fields": [{"field": "email", "type": "missing"}],
    }


def test_unknown_route_returns_code() -> None:
    response = make_client().get("/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"code": "NOT_FOUND"}
