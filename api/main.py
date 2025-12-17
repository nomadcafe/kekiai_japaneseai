from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# ルーターのインポート
from api.routers import jobs, auth, settings, speakers, system


# FastAPIアプリケーション
app = FastAPI(
    title="Gen Movie API", 
    version="1.0.0",
    # 大きなファイルのアップロードを許可（100MB）
    max_request_size=100 * 1024 * 1024
)

# アプリケーション起動時に設定を初期化
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    from api.core.settings_manager import SettingsManager
    # SettingsManagerを初期化することで.envファイルのチェックとコピーが実行される
    settings = SettingsManager()
    print("設定マネージャーを初期化しました")

# CORS設定（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ファイルストレージパス（本番ではS3使用）
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Gen Movie API", "version": "1.0.0"}

# ルーターを登録
app.include_router(jobs.router)
app.include_router(auth.router)
app.include_router(settings.router)
app.include_router(speakers.router)
app.include_router(system.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
