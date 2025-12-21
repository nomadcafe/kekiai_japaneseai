"""
データベース接続とセッション管理
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from api.database.models import Base

# データベースファイルのパス
# Docker環境では /app/data、ローカルでは ./data
BASE_DIR = Path.cwd()
if (BASE_DIR / "data").exists() or str(BASE_DIR).endswith("/app"):
    # Docker環境または既にdataディレクトリが存在する場合
    DB_DIR = BASE_DIR / "data"
else:
    # ローカル環境
    DB_DIR = BASE_DIR / "data"

DB_DIR.mkdir(exist_ok=True, parents=True)
DB_PATH = DB_DIR / "kekiai.db"

# SQLiteデータベースエンジンを作成
# check_same_thread=False は SQLite のスレッド安全性を無効化（FastAPIの非同期処理で必要）
DATABASE_URL = f"sqlite:///{DB_PATH.absolute()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite用の設定
    echo=False  # デバッグ時は True に設定
)

# セッションファクトリーを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """データベースを初期化（テーブルを作成）"""
    Base.metadata.create_all(bind=engine)
    print(f"データベースを初期化しました: {DB_PATH}")


def get_db() -> Generator[Session, None, None]:
    """
    データベースセッションを取得（依存性注入用）
    使用例:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    データベースセッションを直接取得（バックグラウンドタスク用）
    使用後は必ず close() を呼び出すこと
    使用例:
        db = get_db_session()
        try:
            # データベース操作
            ...
        finally:
            db.close()
    """
    return SessionLocal()

