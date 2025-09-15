import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# 🌐 UptimeRobot用のWebサーバー
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 🤖 Discordボット設定（Intent含む）
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    await tree.sync()
    print(f"ログイン完了：{bot.user}")

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

# 🚀 起動！
keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
