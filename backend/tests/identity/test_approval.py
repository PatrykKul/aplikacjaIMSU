from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.identity.models import ApprovalStatus, User, UserRole
from tests.conftest import PASSWORD

Login = Callable[[User], None]
MakeUser = Callable[..., User]

ACCOUNT = {"password": "BardzoTajne1", "display_name": "Nowy"}


@pytest.fixture
def make_teacher(make_user: MakeUser, db: Session) -> Callable[[ApprovalStatus], User]:
    def _make(status: ApprovalStatus) -> User:
        user = make_user(UserRole.TEACHER)
        user.approval_status = status
        db.commit()
        return user

    return _make


# --- Registration and login --------------------------------------------------------------------


def test_registered_teacher_waits_for_approval(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={**ACCOUNT, "email": "n1@test.pl", "role": "teacher"}
    )

    assert response.status_code == 201
    assert response.json()["approval_status"] == "pending"
    assert client.get("/auth/me").json()["approval_status"] == "pending"


def test_registered_student_is_approved(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={**ACCOUNT, "email": "u1@test.pl", "role": "student"}
    )
    assert response.json()["approval_status"] == "approved"


def test_teacher_created_by_admin_is_approved(
    client: TestClient, login: Login, admin: User
) -> None:
    login(admin)
    response = client.post("/users", json={**ACCOUNT, "email": "n2@test.pl", "role": "teacher"})
    assert response.status_code == 201
    assert response.json()["approval_status"] == "approved"


@pytest.mark.parametrize("status", [ApprovalStatus.PENDING, ApprovalStatus.REJECTED])
def test_teacher_not_approved_can_log_in(
    client: TestClient, make_teacher: Callable[[ApprovalStatus], User], status: ApprovalStatus
) -> None:
    teacher = make_teacher(status)

    response = client.post("/auth/login", json={"email": teacher.email, "password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["approval_status"] == status
    assert client.get("/auth/me").json()["approval_status"] == status


# --- Teacher endpoints need an approved account -------------------------------------------------


@pytest.mark.parametrize("status", [ApprovalStatus.PENDING, ApprovalStatus.REJECTED])
def test_teacher_not_approved_cannot_use_teacher_endpoints(
    client: TestClient,
    login: Login,
    make_teacher: Callable[[ApprovalStatus], User],
    status: ApprovalStatus,
) -> None:
    login(make_teacher(status))

    responses = [
        client.post("/courses", json={"title": "Kurs"}),
        client.post("/files", files={"file": ("a.png", b"abc", "image/png")}),
    ]

    for response in responses:
        assert response.status_code == 403
        assert response.json() == {"code": "TEACHER_NOT_APPROVED"}


def test_approved_teacher_uses_teacher_endpoints(
    client: TestClient, login: Login, admin: User
) -> None:
    client.post("/auth/register", json={**ACCOUNT, "email": "n3@test.pl", "role": "teacher"})
    teacher_id = client.get("/auth/me").json()["id"]
    assert client.post("/courses", json={"title": "Kurs"}).status_code == 403

    login(admin)
    client.post(f"/users/{teacher_id}/approve")
    client.post("/auth/login", json={"email": "n3@test.pl", "password": ACCOUNT["password"]})

    assert client.post("/courses", json={"title": "Kurs"}).status_code == 201


# --- Admin decisions -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("before", "action", "after"),
    [
        (ApprovalStatus.PENDING, "approve", "approved"),
        (ApprovalStatus.PENDING, "reject", "rejected"),
        (ApprovalStatus.APPROVED, "reject", "rejected"),
        (ApprovalStatus.REJECTED, "approve", "approved"),
        (ApprovalStatus.APPROVED, "approve", "approved"),  # repeated: no change
        (ApprovalStatus.REJECTED, "reject", "rejected"),
    ],
)
def test_admin_decides_on_teacher(
    client: TestClient,
    login: Login,
    admin: User,
    make_teacher: Callable[[ApprovalStatus], User],
    before: ApprovalStatus,
    action: str,
    after: str,
) -> None:
    teacher = make_teacher(before)
    login(admin)

    response = client.post(f"/users/{teacher.id}/{action}")

    assert response.status_code == 200
    assert response.json()["id"] == teacher.id
    assert response.json()["approval_status"] == after


@pytest.mark.parametrize("action", ["approve", "reject"])
@pytest.mark.parametrize("target", ["student", "admin", "missing"])
def test_decision_only_for_teacher_accounts(
    client: TestClient,
    login: Login,
    admin: User,
    make_user: MakeUser,
    action: str,
    target: str,
) -> None:
    user_ids = {
        "student": lambda: make_user(UserRole.STUDENT).id,
        "admin": lambda: admin.id,
        "missing": lambda: 999999,
    }
    user_id = user_ids[target]()
    login(admin)

    response = client.post(f"/users/{user_id}/{action}")

    assert response.status_code == 404
    assert response.json() == {"code": "USER_NOT_FOUND"}


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
@pytest.mark.parametrize("action", ["approve", "reject"])
def test_only_admin_decides(
    client: TestClient,
    login: Login,
    make_user: MakeUser,
    make_teacher: Callable[[ApprovalStatus], User],
    role: UserRole,
    action: str,
) -> None:
    teacher = make_teacher(ApprovalStatus.PENDING)
    login(make_user(role))

    response = client.post(f"/users/{teacher.id}/{action}")

    assert response.status_code == 403
    assert response.json() == {"code": "FORBIDDEN"}


def test_anonymous_cannot_decide(
    client: TestClient, make_teacher: Callable[[ApprovalStatus], User]
) -> None:
    teacher = make_teacher(ApprovalStatus.PENDING)
    assert client.post(f"/users/{teacher.id}/approve").status_code == 401


# --- Listing by approval status ------------------------------------------------------------------


def test_admin_filters_teachers_by_approval(
    client: TestClient,
    login: Login,
    admin: User,
    make_teacher: Callable[[ApprovalStatus], User],
) -> None:
    pending = make_teacher(ApprovalStatus.PENDING)
    approved = make_teacher(ApprovalStatus.APPROVED)
    rejected = make_teacher(ApprovalStatus.REJECTED)
    login(admin)

    def ids(query: str) -> set[int]:
        return {user["id"] for user in client.get(f"/users?role=teacher{query}").json()}

    assert ids("&approval=pending") == {pending.id}
    assert ids("&approval=rejected") == {rejected.id}
    assert approved.id in ids("&approval=approved")
    assert pending.id not in ids("&approval=approved")
    assert {pending.id, approved.id, rejected.id} <= ids("")


def test_approval_filter_is_validated(client: TestClient, login: Login, admin: User) -> None:
    login(admin)
    response = client.get("/users?role=teacher&approval=waiting")
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
