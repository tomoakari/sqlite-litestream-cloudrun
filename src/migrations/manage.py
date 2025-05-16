import os
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.models import Base
from src.db.database import engine

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """データベーススキーマを初期化します"""
    logger.info("データベーススキーマを作成中...")
    Base.metadata.create_all(bind=engine)
    logger.info("データベーススキーマの作成が完了しました！")

def reset_db():
    """データベースを削除して再作成します"""
    logger.warning("データベースをリセットします！既存のデータは失われます！")
    confirmation = input("続行しますか？ (y/n): ")
    if confirmation.lower() \!= "y":
        logger.info("操作をキャンセルしました")
        return
    
    Base.metadata.drop_all(bind=engine)
    logger.info("既存のテーブルを削除しました")
    Base.metadata.create_all(bind=engine)
    logger.info("新しいテーブルを作成しました")

def seed_db():
    """テスト用のサンプルデータをデータベースに追加します"""
    from src.db.models import User, Group
    from sqlalchemy.orm import Session
    
    logger.info("サンプルデータを追加中...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # ユーザーの作成
        admin = User(username="admin", email="admin@example.com", full_name="Admin User", is_active=True)
        user1 = User(username="user1", email="user1@example.com", full_name="Test User 1", is_active=True)
        user2 = User(username="user2", email="user2@example.com", full_name="Test User 2", is_active=True)
        
        # グループの作成
        admins = Group(name="Administrators", description="システム管理者グループ")
        users = Group(name="Users", description="一般ユーザーグループ")
        
        # DBに追加
        db.add_all([admin, user1, user2, admins, users])
        db.commit()
        
        # リレーションの設定
        admin.groups.append(admins)
        user1.groups.append(users)
        user2.groups.append(users)
        
        db.commit()
        logger.info("サンプルデータの追加が完了しました！")
    
    except Exception as e:
        db.rollback()
        logger.error(f"サンプルデータの追加中にエラーが発生しました: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("コマンドを指定してください: init, reset, seed")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        init_db()
    elif command == "reset":
        reset_db()
    elif command == "seed":
        seed_db()
    else:
        print(f"不明なコマンドです: {command}")
        print("有効なコマンド: init, reset, seed")
        sys.exit(1)

