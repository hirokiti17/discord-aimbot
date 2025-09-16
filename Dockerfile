FROM python:3.10

WORKDIR /bot

# 🔧 pipとビルドツールをアップグレード
RUN pip install --upgrade pip setuptools wheel

# 📦 ライブラリインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 📁 アプリ本体
COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
