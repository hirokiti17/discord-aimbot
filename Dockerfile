FROM python:3.9

WORKDIR /bot

# 🔧 pipとビルドツールをアップグレード
RUN pip install --upgrade pip setuptools wheel

# ✅ requirements.txt を先にコピー！
COPY requirements.txt .

# 📦 ライブラリインストール
RUN pip install --no-cache-dir -r requirements.txt

# ✅ 直接インストール！
RUN pip install google-generative-ai

# 📁 アプリ本体
COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
