import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from googlesearch import search

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

# 🔍 ネット検索機能
@tree.command(name="aimbot_search", description="キーワードでネット検索します！")
@app_commands.describe(keyword="調べたい言葉")
async def aimbot_search(interaction: discord.Interaction, keyword: str):
    await interaction.response.defer()

    try:
        results = list(search(keyword, lang="jp", num=3))
        if not results:
            await interaction.followup.send(f"「{keyword}」に関する情報は見つかりませんでした💦")
            return

        response = f"🔍「{keyword}」の検索結果：\n"
        for url in results:
            response += f"- {url}\n"

        await interaction.followup.send(response)

    except Exception as e:
        await interaction.followup.send(f"検索中にエラーが発生しました: {e}")

# 🚀 起動！
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
