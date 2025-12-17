"""
音声・スピーカー関連のデータモデル
"""
from pydantic import BaseModel
from typing import Optional


class VoiceSampleRequest(BaseModel):
    """音声サンプル生成リクエスト"""
    speaker_id: int
    speaker_name: Optional[str] = None
    speed: Optional[float] = None
    text: str

