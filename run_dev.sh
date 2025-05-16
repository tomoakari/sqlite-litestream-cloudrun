#\!/bin/bash
# ローカル開発用の起動スクリプト

# 環境変数の設定
export DATABASE_URL="sqlite:///./database.db"
export PYTHONPATH=$PWD

# 開発サーバーの起動
echo "Starting development server..."
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080

