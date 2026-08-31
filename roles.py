"""身份組自助領取系統（動態設定版）。"""

import json
import logging
import os
import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

# 🔒 請在此處填入你個人的 Discord ID (數字)
ONLY_USER_ID = 1177665567117824120  # 👈 替換成你的 ID

CONFIG_FILE = "role_buttons.json"


# ── 設定檔讀寫 ─────────────────────────────────────────────────────────────
def load_role_buttons() -> list:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log.error(f"讀取身分組設定檔失敗: {e}")
            return []
    return []


def save_role_buttons(buttons_data: list):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(buttons_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log.error(f"儲存身分組設定檔失敗: {e}")


# ── 按鈕與視窗 ─────────────────────────────────────────────────────────────
class RoleToggleButton(discord.ui.Button):

    def __init__(self, label: str, role_id: int, custom_id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=custom_id,
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "無法識別你的身份。", ephemeral=True
            )
            return

        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message(
                "找不到該身份組，請聯絡管理員確認身份組設定。",
                ephemeral=True,
            )
            return

        try:
            if role in member.roles:
                await member.remove_roles(role, reason="自助身份組：玩家移除")
                await interaction.response.send_message(
                    f"✅ 已移除身份組 **{role.name}**！", ephemeral=True
                )
            else:
                await member.add_roles(role, reason="自助身份組：玩家領取")
                await interaction.response.send_message(
                    f"🎉 已領取身份組 **{role.name}**！", ephemeral=True
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ 機器人權限不足！請確保機器人的身分組順位高於要發放的身分組，且擁有「管理身分組」權限。",
                ephemeral=True,
            )


class RoleSelectView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        buttons_data = load_role_buttons()
        for btn in buttons_data:
            self.add_item(
                RoleToggleButton(
                    label=btn["label"],
                    role_id=btn["role_id"],
                    custom_id=btn["custom_id"],
                )
            )


# ── Cog ───────────────────────────────────────────────────────────────────────
class Roles(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(RoleSelectView())

    def check_owner(self, interaction: discord.Interaction) -> bool:
        """檢查是否為指定唯一使用者"""
        return interaction.user.id == ONLY_USER_ID

    @app_commands.command(
        name="新增身分組按鈕", description="新增一個自助領取的身分組（僅限指定擁有者）"
    )
    @app_commands.describe(
        按鈕顯示名稱="按鈕上要顯示的文字",
        身分組="選擇要讓玩家領取的身分組",
    )
    async def add_role_button(
        self,
        interaction: discord.Interaction,
        按鈕顯示名稱: str,
        身分組: discord.Role,
    ):
        if not self.check_owner(interaction):
            await interaction.response.send_message(
                "❌ 你沒有使用此指令的權限。", ephemeral=True
            )
            return

        buttons_data = load_role_buttons()
        if len(buttons_data) >= 25:
            await interaction.response.send_message(
                "⚠️ 一張卡片最多只能放 25 個按鈕！", ephemeral=True
            )
            return

        custom_id = f"role_toggle_{身分組.id}"

        # 避免重複新增相同的身分組按鈕
        for btn in buttons_data:
            if btn["role_id"] == 身分組.id:
                btn["label"] = 按鈕顯示名稱  # 更新名稱
                save_role_buttons(buttons_data)
                await interaction.response.send_message(
                    f"✅ 已更新身分組 {身分組.mention} 的按鈕名稱為 **{按鈕顯示名稱}**！",
                    ephemeral=True,
                )
                return

        buttons_data.append(
            {
                "label": 按鈕顯示名稱,
                "role_id": 身分組.id,
                "custom_id": custom_id,
            }
        )
        save_role_buttons(buttons_data)

        # 重新註冊 View
        self.bot.add_view(RoleSelectView())

        await interaction.response.send_message(
            f"✅ 成功新增按鈕：**{按鈕顯示名稱}**（對應身分組：{身分組.mention}）\n"
            f"目前已有 {len(buttons_data)} 個按鈕。可以使用 `/選擇身份組` 發送卡片。",
            ephemeral=True,
        )

    @app_commands.command(
        name="清空身分組按鈕", description="清空所有已設定的身分組按鈕（僅限指定擁有者）"
    )
    async def clear_role_buttons(self, interaction: discord.Interaction):
        if not self.check_owner(interaction):
            await interaction.response.send_message(
                "❌ 你沒有使用此指令的權限。", ephemeral=True
            )
            return

        save_role_buttons([])
        await interaction.response.send_message(
            "🗑️ 已成功清空所有身分組按鈕設定！", ephemeral=True
        )

    @app_commands.command(
        name="選擇身份組", description="發送身份組自助領取面板（僅限指定擁有者）"
    )
    async def 選擇身份組(self, interaction: discord.Interaction):
        if not self.check_owner(interaction):
            await interaction.response.send_message(
                "❌ 你沒有使用此指令的權限。", ephemeral=True
            )
            return

        buttons_data = load_role_buttons()
        if not buttons_data:
            await interaction.response.send_message(
                "⚠️ 目前尚未新增任何身分組按鈕！請先使用 `/新增身分組按鈕` 設定。",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="🎀 身份組自助領取",
            description=(
                "點擊下方按鈕即可領取對應身份組。\n"
                "若已持有該身份組，再次點擊即可**移除**。"
            ),
            color=discord.Color.from_str("#e0cbd2"),
        )
        await interaction.response.send_message(
            embed=embed, view=RoleSelectView()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
