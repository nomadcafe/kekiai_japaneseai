"""
音声・スピーカー関連のルート
"""
from fastapi import APIRouter, HTTPException, Response
import requests
import os
from api.models.speakers import VoiceSampleRequest

router = APIRouter(prefix="/api", tags=["speakers"])


@router.get("/speakers")
async def get_speakers():
    """利用可能なVOICEVOXスピーカー一覧を取得"""
    # Docker環境の場合はvoicevoxホスト名を使用
    if os.path.exists("/.dockerenv"):
        voicevox_url = "http://voicevox:50021"
    else:
        voicevox_url = os.getenv("VOICEVOX_URL", "http://localhost:50021")
    
    try:
        response = requests.get(f"{voicevox_url}/speakers", timeout=5)
        response.raise_for_status()
        speakers = response.json()
        
        # フロントエンドで使いやすい形式に整形
        formatted_speakers = []
        for speaker in speakers:
            for style in speaker['styles']:
                formatted_speakers.append({
                    "speaker_name": speaker['name'],
                    "speaker_uuid": speaker['speaker_uuid'],
                    "style_name": style['name'],
                    "style_id": style['id'],
                    "display_name": f"{speaker['name']} ({style['name']})"
                })
        
        return formatted_speakers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VOICEVOXへの接続に失敗しました: {str(e)}")


@router.post("/voice-sample")
async def generate_voice_sample(request: VoiceSampleRequest):
    """指定したスピーカーでサンプル音声を生成"""
    voicevox_url = os.getenv("VOICEVOX_URL", "http://localhost:50021")
    
    try:
        # 音声クエリの作成
        query_response = requests.post(
            f"{voicevox_url}/audio_query",
            params={
                "text": request.text,
                "speaker": request.speaker_id
            }
        )
        query_response.raise_for_status()
        
        # 音声合成パラメータを調整
        synthesis_data = query_response.json()
        
        # 速度調整
        if request.speed:
            synthesis_data["speedScale"] = request.speed
        elif request.speaker_name == "九州そら":
            # 速度が指定されていない場合、九州そらはデフォルトで1.2倍速
            synthesis_data["speedScale"] = 1.2
        
        # 音声合成
        synthesis_response = requests.post(
            f"{voicevox_url}/synthesis",
            params={"speaker": request.speaker_id},
            json=synthesis_data
        )
        synthesis_response.raise_for_status()
        
        return Response(
            content=synthesis_response.content,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=sample_{request.speaker_id}.wav"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声生成に失敗しました: {str(e)}")

