import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

# TO解除ボタンview
class TimeoutActionView(discord.ui.View):
def __init__(self, user, message_to_delete):
        super().__init__(timeout=None)
        self.user = user
        self.message_to_delete = message_to_delete

    @discord.ui.button(label="タイムアウト解除", style=discord.ButtonStyle.success)
    async def release_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "この操作にはモデレーター権限が必要です！", ephemeral=True
            )
            return

        try:
            await self.user.timeout(None)
            await interaction.response.send_message(
                f"{self.user.mention} のタイムアウトを解除しました！", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"解除に失敗しました: {e}", ephemeral=True
            )

    @discord.ui.button(label="解除しない（メッセージ削除）", style=discord.ButtonStyle.danger)
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "この操作にはモデレーター権限が必要です！", ephemeral=True
            )
            return

        try:
            await self.message_to_delete.delete()
        except Exception as e:
            await interaction.response.send_message(
                f"削除に失敗しました: {e}", ephemeral=True
            )


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
async def setup_hook():
    await tree.sync()
    print("コマンド同期完了！")

@bot.event
async def on_ready():
    activity = discord.Game(name="ロールと検索を見守ってるよ！")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f"ログイン完了：{bot.user}")

# 🌟 Geminiクライアントの設定（google-genai SDK）
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 🔍 Google検索用関数（google-api-python-client）
from googleapiclient.discovery import build

def google_search(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("GOOGLE_CSE_ID")
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=query, cx=cx, lr="lang_ja", num=3).execute()
    return [item["link"] for item in res.get("items", [])]

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

# 🌐 Probotのリンク投稿TO解除コマンド

@bot.event
async def on_message(message):
    if message.author.bot:
        return
        # ✅ リンク投稿警告メッセージ
    if "http://" in message.content or "https://" in message.content:
        await message.channel.send(
            f"{message.author.mention} リンクの投稿は禁止されてるよ！次から気をつけてね！モデレーターの判断でタイムアウトは解除されます"
        )

        # ✅ 管理チャンネルの取得
        admin_channel = bot.get_channel(1416608371972243656)

        # ✅ ボタン付き通知を送信
        view = TimeoutActionView(user=message.author, message_to_delete=None)
        sent = await admin_channel.send(
            f"⚠️ {message.author.mention} がリンク投稿でタイムアウトされた可能性があります。\n"
            f"解除するかどうか判断してください。",
            view=view
        )
        view.message_to_delete = sent



# 🔍 Google検索コマンド（小文字に修正！）
@tree.command(name="aimbot_google", description="キーワードでGoogle検索します！")
@app_commands.describe(keyword="調べたい言葉")
async def aimbot_google(interaction: discord.Interaction, keyword: str):
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

# 🧠 Geminiによる説明コマンド（小文字に修正！）
@tree.command(name="aimbot_ai", description="AIが入力された内容について説明します！")
@app_commands.describe(ai="説明してほしい内容を入力してください")
async def aimbot_ai(interaction: discord.Interaction, ai: str):
    await interaction.response.defer()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=ai
        )
        await interaction.followup.send(response.text)

    except Exception as e:
        await interaction.followup.send(f"AI検索中にエラーが発生しました: {e}")

# 🚀 起動！
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
