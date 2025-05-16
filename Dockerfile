FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y wget curl unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Litestreamのインストール - GitHub Releaseから直接バイナリをダウンロード
RUN curl -L https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.tar.gz -o litestream.tar.gz \
    && tar -xzf litestream.tar.gz \
    && mv litestream /usr/local/bin/ \
    && rm litestream.tar.gz

# Google Cloud SDKインストール
RUN curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-434.0.0-linux-x86_64.tar.gz \
    && tar -xf google-cloud-sdk-434.0.0-linux-x86_64.tar.gz \
    && ./google-cloud-sdk/install.sh --quiet \
    && rm google-cloud-sdk-434.0.0-linux-x86_64.tar.gz
ENV PATH $PATH:/google-cloud-sdk/bin

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# データベースディレクトリの作成
RUN mkdir -p /data
VOLUME ["/data"]

# 環境変数の設定
ENV DATABASE_URL=sqlite:///database.db \
    PYTHONPATH=/app \
    PORT=8080

# 起動コマンド
CMD ["gunicorn", "src.main:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
