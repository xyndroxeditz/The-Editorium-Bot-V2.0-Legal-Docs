"""
Gamification cog - XP, levels, badges, achievements, leaderboards
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
from db.gamification_helper import (
    get_user_stats, get_leaderboard, get_xp_for_next_level
)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")

# Badge definitions
BADGES = {
    "profile_creator": {"name": "Profile Creator", "emoji": "📝", "desc": "Created your first profile"},
    "first_job_accepted": {"name": "First Job", "emoji": "💼", "desc": "Got your first job accepted"},
    "top_10": {"name": "Top 10", "emoji": "🏆", "desc": "Reached top 10 on leaderboard"},
    "verified": {"name": "Verified", "emoji": "✅", "desc": "Verified creator"},
    "level_10": {"name": "Level 10", "emoji": "⭐", "desc": "Reached level 10"},
}


class GamificationCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="level", description="Check your level and XP")
    @app_commands.describe(user="User to check (leave empty for yourself)")
    async def level(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        stats = get_user_stats(DB_PATH, str(target.id))
        
        if not stats:
            await interaction.response.send_message("❌ No stats found. Start by creating a profile or completing jobs!", ephemeral=True)
            return
        
        level, xp_needed = get_xp_for_next_level(stats['xp'])
        
        embed = discord.Embed(
            title=f"📊 {target.display_name}'s Stats",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Level", value=f"**{level}** ⭐", inline=True)
        embed.add_field(name="Total XP", value=f"{stats['xp']:,}", inline=True)
        embed.add_field(name="XP to Next Level", value=f"{xp_needed:,}", inline=True)
        
        # Progress bar
        progress = int((stats['xp'] / (stats['xp'] + xp_needed)) * 10)
        bar = "█" * progress + "░" * (10 - progress)
        embed.add_field(name="Progress", value=f"`{bar}` {progress*10}%", inline=False)
        
        # Badges
        badges = stats.get('badges', [])
        if badges:
            badge_text = " ".join([BADGES.get(b, {}).get("emoji", "🏅") for b in badges[:10]])
            embed.add_field(name="Badges", value=badge_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View top users")
    @app_commands.describe(category="Choose leaderboard type")
    @app_commands.choices(category=[
        app_commands.Choice(name="XP & Levels", value="xp"),
        app_commands.Choice(name="Jobs Completed", value="jobs"),
        app_commands.Choice(name="Ratings", value="rating")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "xp"):
        leaders = get_leaderboard(DB_PATH, category, 10)
        
        if not leaders:
            await interaction.response.send_message("No leaderboard data yet.", ephemeral=True)
            return
        
        title_map = {"xp": "🏆 Top Users by XP", "jobs": "💼 Top Job Completers", "rating": "⭐ Top Rated Users"}
        embed = discord.Embed(
            title=title_map.get(category, "Leaderboard"),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        for i, leader in enumerate(leaders, 1):
            user_id = leader['user_id']
            try:
                user = await self.bot.fetch_user(int(user_id))
                name = user.display_name
            except:
                name = f"User {user_id}"
            
            if category == "xp":
                value = f"Level {leader['level']} • {leader['xp']:,} XP"
            elif category == "jobs":
                value = f"{leader['jobs_completed']} jobs completed"
            elif category == "rating":
                value = f"{'⭐' * int(leader['rating_avg'])} {leader['rating_avg']:.1f}/5 ({leader['rating_count']} reviews)"
            
            medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"#{i}"
            embed.add_field(name=f"{medal} {name}", value=value, inline=False)
        
        embed.set_footer(text="Keep grinding to climb the ranks!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="badges", description="View your badges and achievements")
    async def badges(self, interaction: discord.Interaction):
        stats = get_user_stats(DB_PATH, str(interaction.user.id))
        if not stats:
            await interaction.response.send_message("❌ No badges yet. Start by creating a profile!", ephemeral=True)
            return
        
        badges = stats.get('badges', [])
        achievements = stats.get('achievements', [])
        
        embed = discord.Embed(
            title=f"🏅 {interaction.user.display_name}'s Badges",
            color=discord.Color.gold()
        )
        
        if badges:
            for badge_id in badges:
                badge = BADGES.get(badge_id, {"name": badge_id, "emoji": "🏅", "desc": ""})
                embed.add_field(
                    name=f"{badge['emoji']} {badge['name']}",
                    value=badge['desc'],
                    inline=True
                )
        else:
            embed.description = "No badges yet. Keep completing jobs and activities!"
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(GamificationCog(bot))
