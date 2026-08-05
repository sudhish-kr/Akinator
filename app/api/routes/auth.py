from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_auth_service
from app.api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, service: AuthService = Depends(get_auth_service)):
    try:
        result = await service.register(body.email, body.username, body.password)
        return TokenResponse(**result)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, service: AuthService = Depends(get_auth_service)):
    try:
        result = await service.login(body.email, body.password)
        return TokenResponse(**result)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
