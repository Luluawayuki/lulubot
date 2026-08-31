import asyncio
import logging
import os
import discord
from discord.ext import commands

# 設定 Logging，能在主控台看到 Bot 的運行日誌
logging.basicConfig(level=logging.INFO)

# 設定 Bot 的 Intents (權限)
# ⚠️ 注意：成員加入事件 (on_member_join) 必須開啟 members 選項！
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 開啟成員監聽權限

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """當 Bot 成功連線並準備就緒時觸發"""
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

    # 同步斜線指令 (Slash Commands) 到 Discord 伺服器
    try:
        synced = await bot.tree.sync()
        print(f"成功同步 {len(synced)} 個斜線指令！")
    except Exception as e:
        print(f"同步斜線指令失敗: {e}")


async def load_extensions():
    """載入你的 Cog 檔案"""
    # 假設你的 Cog 檔名叫做 welcome.py，這裡就填 "welcome"
    # 如果你的 Cog 直接寫在 main.py 裡面，就不需要此步驟
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("roles")


async def main():
    async with bot:
        # 載入 welcome.pyCog 模組
        # await bot.load_extension("welcome")
        await bot.load_extension("roles")

        TOKEN = os.getenv("DISCORD_TOKEN")
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
