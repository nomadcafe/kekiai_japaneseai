"""
認証関連のルート
"""
from fastapi import APIRouter, HTTPException, Request, status
from api.models.auth import LoginRequest, AuthStatusResponse
from api.core.auth import auth_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(request: Request):
    """認証状態を取得"""
    return AuthStatusResponse(
        auth_enabled=auth_manager.is_auth_enabled(),
        authenticated=auth_manager.check_auth(request)
    )


@router.post("/login")
async def login(login_request: LoginRequest):
    """ログイン"""
    if not auth_manager.is_auth_enabled():
        return {"success": True, "message": "認証は無効です", "token": None}
    
    if auth_manager.verify_password(login_request.password):
        return {"success": True, "message": "ログイン成功", "token": login_request.password}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="パスワードが正しくありません"
        )

