FROM python:3.11

WORKDIR /bot

# 🔧 pipとビルドツールをアップグレード
RUN pip install --upgrade pip setuptools wheel

# 📦 ライブラリインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# 📁 アプリ本体
COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
