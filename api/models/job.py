"""
ジョブ関連のデータモデル
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobStatus(BaseModel):
    """ジョブステータスモデル"""
    job_id: str
    status: str  # pending, processing, completed, failed
    status_code: str  # ステータスコード (PDF_PROCESSING, DIALOGUE_GENERATING, etc.)
    created_at: datetime
    updated_at: datetime
    progress: int  # 0-100
    result_url: Optional[str] = None
    error_code: Optional[str] = None  # エラーコード (FILE_NOT_FOUND, INVALID_FORMAT, etc.)
    estimated_duration: Optional[int] = None  # 推定動画時間（秒）
    target_duration: Optional[int] = None  # 目標動画時間（分）


class JobCreateResponse(BaseModel):
    """ジョブ作成レスポンス"""
    job_id: str


class GenerateAudioRequest(BaseModel):
    """音声生成リクエスト"""
    job_id: str
    speed_scale: float = 1.0
    pitch_scale: float = 0.0
    intonation_scale: float = 1.2  # デフォルトで表現豊かに
    volume_scale: float = 1.0


class CreateVideoRequest(BaseModel):
    """動画作成リクエスト"""
    job_id: str
    slide_numbers: Optional[list[int]] = None  # 指定しない場合は全スライド
    # BGM設定
    bgm_enabled: bool = False  # BGMを有効にするか
    bgm_path: Optional[str] = None  # BGMファイルパス（相対パスまたはファイル名）
    bgm_volume: float = 0.15  # BGM音量（0.0-1.0）
    # 転場効果設定
    transition_type: str = "crossfade"  # 転場タイプ: "crossfade", "slide", "zoom", "fade", "none"
    transition_duration: float = 0.4  # 転場時間（秒）


class GenerateDialogueRequest(BaseModel):
    """対話生成リクエスト"""
    job_id: str
    additional_prompt: Optional[str] = None  # AIへの追加指示
    continue_to_video: bool = False  # 対話生成後に音声・動画生成を続けるか
    api_key: Optional[str] = None  # APIキー（リクエストから取得、.envに保存しない）
    provider: Optional[str] = None  # プロバイダー名（リクエストから取得）


class UpdateDialogueRequest(BaseModel):
    """対話更新リクエスト"""
    job_id: str
    dialogue_data: dict[str, list[dict]]  # 編集された対話データ


class SlideImportanceRequest(BaseModel):
    """スライド重要度設定リクエスト"""
    job_id: str
    importance_map: dict[int, float]  # スライド番号 -> 重要度 (0.5-1.5)

