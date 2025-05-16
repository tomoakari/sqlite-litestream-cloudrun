# CloudRun SQLite + Litestream Database Service

このプロジェクトは、GoogleのCloudRunとCloudStorageを使用して、SQLiteデータベースをスケーラブルかつ信頼性の高い方法で提供するサービスです。Litestreamによるレプリケーションとバックアップをサポートしています。

## 主な機能

- SQLiteデータベースをCloudRunで実行
- Litestreamを使用したCloudStorageへのリアルタイムレプリケーション
- FastAPIベースのREST API
- ユーザーとグループのモデル管理
- CloudRunでの自動デプロイメント

## 技術スタック

- Python 3.11
- FastAPI
- SQLAlchemy
- SQLite
- Litestream
- Google Cloud Run
- Google Cloud Storage

## 要求事項

- Google Cloud SDK
- Docker
- Python 3.11+

## セットアップと実行

### ローカル開発

```bash
# 依存関係をインストール
pip install -r requirements.txt

# 開発サーバーを起動
uvicorn src.main:app --reload
```

### Dockerビルド

```bash
docker build -t cr-db .
docker run -p 8080:8080 cr-db
```

### CloudRunデプロイ

```bash
# Google Cloudにイメージをビルドしてデプロイ
gcloud builds submit --tag gcr.io/[PROJECT_ID]/cr-db
gcloud run deploy cr-db --image gcr.io/[PROJECT_ID]/cr-db --platform managed --region asia-northeast1
```

## API エンドポイント

- `GET /health` - ヘルスチェック
- `GET /users/` - すべてのユーザーを取得
- `POST /users/` - 新しいユーザーを作成
- `GET /users/{user_id}` - 特定のユーザーを取得
- `GET /groups/` - すべてのグループを取得
- `POST /groups/` - 新しいグループを作成
- `GET /groups/{group_id}` - 特定のグループを取得
- `POST /users/{user_id}/groups/{group_id}` - ユーザーをグループに追加

## 環境変数

- `DATABASE_URL` - SQLiteデータベースのパス
- `RECOVER_DB` - 起動時にCloudStorageからデータベースを復元するかどうか（"true"/"false"）
- `PORT` - サーバーポート（デフォルト：8080）

