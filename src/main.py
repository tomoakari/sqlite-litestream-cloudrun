import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import subprocess
import signal
import atexit
import time

from .db import models, database
from pydantic import BaseModel

# アプリケーション初期化
app = FastAPI(title="SQLite + Litestream Database Service")

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベースが存在しない場合は作成する
if not os.path.exists("./database.db"):
    models.Base.metadata.create_all(bind=database.engine)

# Litestreamプロセス
litestream_process = None

# Pydanticモデル（APIリクエスト/レスポンス用）
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    is_active: bool
    groups: List[str] = []

    class Config:
        orm_mode = True

class GroupBase(BaseModel):
    name: str
    description: str = None

class GroupCreate(GroupBase):
    pass

class Group(GroupBase):
    id: int
    users: List[str] = []

    class Config:
        orm_mode = True


# スタートアップイベント
@app.on_event("startup")
async def startup_event():
    global litestream_process
    
    # リカバリモードが有効かチェック
    if os.getenv("RECOVER_DB", "false").lower() == "true":
        try:
            logger.info("Attempting to recover database from Cloud Storage")
            subprocess.run([
                "litestream", "restore", 
                "-config", "/app/config/litestream.yml", 
                "/app/database.db"
            ], check=True)
            logger.info("Database recovery completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Database recovery failed: {str(e)}")
            if not os.path.exists("/app/database.db"):
                # 新しいデータベースを作成
                logger.info("Creating new database")
                models.Base.metadata.create_all(bind=database.engine)
    
    # Litestreamレプリケーションを開始
    try:
        logger.info("Starting Litestream replication")
        litestream_process = subprocess.Popen([
            "litestream", "replicate",
            "-config", "/app/config/litestream.yml"
        ])
        logger.info(f"Litestream started with PID {litestream_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start Litestream: {str(e)}")


# シャットダウンイベント
@app.on_event("shutdown")
async def shutdown_event():
    global litestream_process
    if litestream_process:
        logger.info(f"Stopping Litestream (PID {litestream_process.pid})")
        litestream_process.terminate()
        try:
            litestream_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Litestream did not terminate gracefully, force killing")
            litestream_process.kill()


# エンドポイント: ヘルスチェック
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# エンドポイント: ユーザー作成
@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# エンドポイント: すべてのユーザーを取得
@app.get("/users/", response_model=List[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# エンドポイント: 特定のユーザーを取得
@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# エンドポイント: グループを作成
@app.post("/groups/", response_model=Group)
def create_group(group: GroupCreate, db: Session = Depends(database.get_db)):
    db_group = models.Group(
        name=group.name,
        description=group.description
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

# エンドポイント: すべてのグループを取得
@app.get("/groups/", response_model=List[Group])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    groups = db.query(models.Group).offset(skip).limit(limit).all()
    return groups

# エンドポイント: 特定のグループを取得
@app.get("/groups/{group_id}", response_model=Group)
def read_group(group_id: int, db: Session = Depends(database.get_db)):
    db_group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group

# エンドポイント: ユーザーをグループに追加
@app.post("/users/{user_id}/groups/{group_id}")
def add_user_to_group(user_id: int, group_id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    group = db.query(models.Group).filter(models.Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    
    user.groups.append(group)
    db.commit()
    return {"message": "User added to group successfully"}
