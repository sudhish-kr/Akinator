from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_auth_service
from app.api.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _http_error(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return TokenResponse(**(await service.register(body.email, body.username, body.password)))
    except AuthError as exc:
        raise _http_error(exc) from exc


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return TokenResponse(**(await service.login(body.email, body.password)))
    except AuthError as exc:
        raise _http_error(exc) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    try:
        return TokenResponse(**(await service.refresh(body.refresh_token)))
    except AuthError as exc:
        raise _http_error(exc) from exc


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    body: LogoutRequest = LogoutRequest(),
    authorization: str | None = Header(default=None),
    service: AuthService = Depends(get_auth_service),
):
    access = None
    if authorization and authorization.lower().startswith("bearer "):
        access = authorization.split(" ", 1)[1]
    try:
        result = await service.logout(
            refresh_token=body.refresh_token, access_token=access
        )
        return LogoutResponse(**result)
    except AuthError as exc:
        raise _http_error(exc) from exc
