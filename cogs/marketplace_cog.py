"""
Marketplace cog - Buy/sell services, escrow system (placeholder)
"""
import discord
from discord.ext import commands
from discord import app_commands
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")


class MarketplaceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="marketplace", description="Browse marketplace listings")
    async def marketplace(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Marketplace",
            description="Buy and sell editing services!\n\n*Feature coming soon - full marketplace with escrow, ratings, and secure transactions.*",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="list_service", description="List a service for sale")
    async def list_service(self, interaction: discord.Interaction):
        await interaction.response.send_message("📝 Service listing feature coming soon!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarketplaceCog(bot))
