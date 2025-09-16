import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from googleapiclient.discovery import build
import google.generativeai as genai

# 🌐 UptimeRobot用のWebサーバー
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🤖 Discordボット設定
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    activity = discord.Game(name="ロールと検索を見守ってるよ！")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"ログイン完了：{bot.user}")

# 🎯 ロール人数カウント
@tree.command(name="aimbot", description="指定したロールの人数を数えます！")
@app_commands.describe(role="人数を数えたいロール名")
async def aimbot_role(interaction: discord.Interaction, role: str):
    guild = interaction.guild
    target_role = discord.utils.get(guild.roles, name=role)

    if target_role is None:
        await interaction.response.send_message(f"ロール「{role}」が見つかりません", ephemeral=True)
        return

    count = sum(1 for member in guild.members if target_role in member.roles)
    await interaction.response.send_message(f"ロール「{target_role.name}」を持ってる人は {count} 人です！")

#🔍　検索アプリ
from googleapiclient.discovery import build

def google_search(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID")
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cx, lr="lang_ja", num=3).execute()
    return [item["link"] for item in res.get("items", [])]

@tree.command(name="aimbot_search", description="キーワードでGoogle検索します！")
@app_commands.describe(keyword="調べたい言葉")
async def aimbot_search(interaction: discord.Interaction, keyword: str):
    await interaction.response.defer()

    try:
        results = google_search(keyword)
        if not results:
            await interaction.followup.send(f"「{keyword}」に関する情報は見つかりませんでした💦")
            return

        response = f"🔍「{keyword}」の検索結果：\n"
        for url in results:
            response += f"- {url}\n"

        await interaction.followup.send(response)

    except Exception as e:
        await interaction.followup.send(f"検索中にエラーが発生しました: {e}")

#🧠AI検索

import subprocess

import subprocess
import os

# ✅ Geminiライブラリの読み込み（なければインストール）
try:
    import google.generativeai as genai
except ImportError:
    subprocess.run(["pip", "install", "google-generative-ai"])
    import google.generativeai as genai  # ← インストール後に再インポート！

# ✅ APIキーの設定
genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")


# 🔍 Geminiライブラリの読み込み
import google.generativeai as genai

# 🌟 Gemini APIキーの設定（on_readyの前に置くと◎）
genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# 🔧 /aimbot_search AI: ○○ に対応するコマンド
@tree.command(name="aimbot_search", description="AIが入力された内容について説明します！")
@app_commands.describe(AI="説明してほしい内容を入力してください")
async def aimbot_search(interaction: discord.Interaction, AI: str):
    await interaction.response.defer()

    try:
        response = model.generate_content(AI)
        await interaction.followup.send(response.text)

    except Exception as e:
        await interaction.followup.send(f"エラーが発生しました: {e}")

# 🚀 起動！
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
