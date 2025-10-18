"""
Social cog - Following, collaborations, and social features
"""
import discord
from discord.ext import commands
from discord import app_commands
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")


class SocialCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="follow", description="Follow a user to get notified of their activities")
    @app_commands.describe(user="User to follow")
    async def follow(self, interaction: discord.Interaction, user: discord.User):
        if user.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't follow yourself!", ephemeral=True)
            return
        # Placeholder - would implement DB follow system
        await interaction.response.send_message(f"✅ Now following {user.mention}! (Feature in development)", ephemeral=True)

    @app_commands.command(name="collab", description="Create a collaboration request")
    async def collab(self, interaction: discord.Interaction):
        await interaction.response.send_message("🤝 Collaboration system coming soon!", ephemeral=True)

    @app_commands.command(name="dashboard", description="View your personal stats dashboard")
    async def dashboard(self, interaction: discord.Interaction):
        from db.sqlite_helper import get_profile
        from db.gamification_helper import get_user_stats
        
        profile = get_profile(DB_PATH, str(interaction.user.id))
        stats = get_user_stats(DB_PATH, str(interaction.user.id))
        
        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Dashboard",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        if profile:
            embed.add_field(name="Jobs Completed", value=str(profile.get('jobs_completed', 0)), inline=True)
            embed.add_field(name="Jobs Applied", value=str(profile.get('jobs_applied', 0)), inline=True)
            embed.add_field(name="Rating", value=f"{profile.get('rating_avg', 0):.1f}/5", inline=True)
        
        if stats:
            embed.add_field(name="Level", value=str(stats.get('level', 1)), inline=True)
            embed.add_field(name="Total XP", value=f"{stats.get('xp', 0):,}", inline=True)
            embed.add_field(name="Badges", value=str(len(stats.get('badges', []))), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SocialCog(bot))
