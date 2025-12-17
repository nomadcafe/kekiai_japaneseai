"""
設定関連のデータモデル
"""
from pydantic import BaseModel
from typing import Optional, Dict


class ProviderConfig(BaseModel):
    """プロバイダー設定"""
    provider: str
    api_key: str
    model: Optional[str] = None


class TestKeyRequest(BaseModel):
    """APIキーテストリクエスト"""
    provider: str
    api_key: str


class SettingsUpdate(BaseModel):
    """設定更新リクエスト"""
    default_provider: Optional[str] = None
    default_model: Optional[Dict[str, str]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

