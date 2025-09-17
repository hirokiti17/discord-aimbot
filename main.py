import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread
is_lockdown_active = False               # 迎撃モード中かどうか
lockdown_task = None                     # 自動解除用の非同期タスク
evac_channel = None                      # 避難チャンネルの参照
lockdown_messages = {}                  # 警告メッセージの記録 {channel_id: message}
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

        # 🌟 Embed作成
        embed = discord.Embed(
            title=f"🔎 検索結果 for「{keyword}」",
            description="上位3件のリンクを表示しています。",
            color=0x00ccff
        )

        for i, url in enumerate(results, start=1):
            site_name = url.split("/")[2]
            embed.add_field(
                name=f"{i}. {site_name}",
                value=f"[リンクはこちら]({url})",
                inline=False
            )

        embed.set_footer(text="powered by Google Custom Search")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"検索中にエラーが発生しました: {e}")


# 🧠 Geminiによる説明コマンド（小文字で引数を作ってね"AI"はだめ。"ai"で！）
@tree.command(name="aimbot_ai", description="AIが入力された内容について説明します！")
@app_commands.describe(ai="説明してほしい内容を入力してください")
async def aimbot_ai(interaction: discord.Interaction, ai: str):
    await interaction.response.defer()

    # 🌟 自動プロンプト加工
    prompt = (
        f"以下の内容について、初心者にもわかるように、"
        f"要点だけを箇条書きで、2000文字以内に簡潔にまとめてください：\n{ai}"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response.text:
            await interaction.followup.send("AIからの応答が空でした💦")
            return

        # 🌟 応答が長すぎる場合に備えて分割送信
        def split_message(text, max_length=2000):
            return [text[i:i+max_length] for i in range(0, len(text), max_length)]

        for chunk in split_message(response.text):
            await interaction.followup.send(chunk)

    except Exception as e:
        await interaction.followup.send(f"AI検索中にエラーが発生しました: {e}")

#サーバー保護迎撃システム


# 🔧 ロック開始処理（緊急会議チャンネル生成付き）
async def start_lockdown(guild):
    global is_lockdown_active, lockdown_task, evac_channel, lockdown_messages
    is_lockdown_active = True
    lockdown_messages = {}

    # ロールIDで個別取得
    trusted_role = guild.get_role(1415664609397833818)  # 投稿許可ロールID
    evac_role = guild.get_role(1417026509490622537)     # 会議所アクセスロールID

    # 全チャンネルロック（全員投稿不可）
    for channel in guild.text_channels:
        try:
            await channel.edit(overwrites={
                guild.default_role: discord.PermissionOverwrite(send_messages=False),
                trusted_role: discord.PermissionOverwrite(send_messages=False)
            })
            msg = await channel.send("🚨 このチャンネルは現在荒らし迎撃保護モード中です。3分間投稿できません！")
            lockdown_messages[channel.id] = msg
        except:
            pass

    # 緊急会議チャンネル作成（運営ロールのみアクセス可）
    evac_overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        evac_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    evac_channel = await guild.create_text_channel(
        name="緊急運営チャンネル",
        overwrites=evac_overwrites,
        topic="迎撃システム起動中の対応会議はこちらでどうぞ！"
    )

    await evac_channel.send("🏕️ 緊急会議所が開設されました！")

    # 自動解除タスク
    async def unlock_after_delay():
        await asyncio.sleep(180)
        await cancel_lockdown(guild)

    lockdown_task = asyncio.create_task(unlock_after_delay())

# 🔧 ロック解除処理
async def cancel_lockdown(guild):
    global is_lockdown_active, lockdown_task, evac_channel, lockdown_messages
    if not is_lockdown_active:
        return

    is_lockdown_active = False
    if lockdown_task:
        lockdown_task.cancel()

    for channel in guild.text_channels:
        try:
            await channel.edit(overwrites={})
            msg = lockdown_messages.get(channel.id)
            if msg:
                await msg.delete()
        except:
            pass

    lockdown_messages.clear()

    if evac_channel:
        await evac_channel.send("✅ 迎撃が終了しました。会議所は必要に応じて削除してください。")

# 🔧 ダブルチェックView
class ConfirmLockdownView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="はい、迎撃します", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("モデレーター権限が必要です！", ephemeral=True)
            return

        await interaction.response.send_message("🌊 迎撃開始！")
        await start_lockdown(self.guild)

    @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("迎撃をキャンセルしました！", ephemeral=True)

# 🔧 迎撃ボタンView
class LaunchLockdownView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    @discord.ui.button(label="迎撃する", style=discord.ButtonStyle.danger)
    async def launch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("モデレーター権限が必要です！", ephemeral=True)
            return

        await interaction.response.send_message(
            "⚠️ 本当に迎撃しますか？", view=ConfirmLockdownView(self.guild), ephemeral=True
        )

# 🔧 Bot起動時の処理（指定チャンネルにボタン表示）
@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

    # ギルド取得（Botが所属している最初のギルド）
    guild = bot.guilds[0]

    # チャンネルIDで取得（キャッシュ済みのチャンネルから探す）
    admin_channel = discord.utils.get(guild.text_channels, id=1416609997382488064)

    if admin_channel is None:
        print("⚠️ 指定されたチャンネルが見つかりませんでした！")
        return

    await admin_channel.send("🛡️ サーバー迎撃システムスタンバイ", view=LaunchLockdownView(guild))

# 🚀 起動！
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
