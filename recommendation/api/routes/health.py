from fastapi import APIRouter, Request

from ..schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    store = request.app.state.store
    return HealthResponse(
        status="ok",
        items_loaded=len(store["items"]),
        domains=sorted(store["items"]["domain"].unique().tolist()),
    )
