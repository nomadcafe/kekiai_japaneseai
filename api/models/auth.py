"""
認証関連のデータモデル
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """ログインリクエスト"""
    password: str


class AuthStatusResponse(BaseModel):
    """認証ステータスレスポンス"""
    auth_enabled: bool
    authenticated: bool = False

