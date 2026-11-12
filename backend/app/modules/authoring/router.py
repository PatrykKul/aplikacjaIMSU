from fastapi import APIRouter

# Endpoints: GET /lessons/{id}/readiness, PUT /lessons/{id}/publication (stage B, docs/08)
authoring_router = APIRouter(prefix="/lessons", tags=["authoring"])
