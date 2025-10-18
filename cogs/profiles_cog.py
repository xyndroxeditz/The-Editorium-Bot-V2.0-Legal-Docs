"""
Profiles cog for Editorium Bot V2.0
Implements complete profile system with all improvements and interactive UI.
"""
from __future__ import annotations
import discord
from discord.ext import commands
from discord import app_commands
import time
from typing import Optional, List
import os
import re
from db.sqlite_helper import (
    init_db, add_or_update_profile, get_profile, delete_profile,
    bump_profile as db_bump_profile, set_showcase_message_id,
    get_showcase_message_id, set_config, get_config,
    add_premium, remove_premium, list_active_premium, is_premium,
)
from db.gamification_helper import add_xp, award_badge

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")

SPECIALTIES = ["Editor", "Client", "Influencer", "Streamer", "Designer", "Animator", "Thumbnail Artist", "Other"]

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


class SpecialtySelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=s, value=s) for s in SPECIALTIES]
        super().__init__(placeholder="Choose your specialty...", options=options, min_values=1, max_values=1)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()


class ProfileModal(discord.ui.Modal, title="Create / Edit Profile"):
    bio = discord.ui.TextInput(label="Bio", style=discord.TextStyle.long, max_length=200, placeholder="Short bio (200 chars)")
    software = discord.ui.TextInput(label="Software", placeholder="E.g., Premiere Pro, After Effects")
    portfolio = discord.ui.TextInput(label="Portfolio Links", placeholder="One URL per line (free: 1, premium: unlimited)")
    banner_url = discord.ui.TextInput(label="Banner URL (premium only)", required=False)
    youtube = discord.ui.TextInput(label="YouTube Channel URL (premium only)", required=False)
    twitch = discord.ui.TextInput(label="Twitch Channel URL (premium only)", required=False)
    instagram = discord.ui.TextInput(label="Instagram Profile URL (premium only)", required=False)
    tiktok = discord.ui.TextInput(label="TikTok Profile URL (premium only)", required=False)
    twitter = discord.ui.TextInput(label="Twitter Profile URL (premium only)", required=False)

    def __init__(self, bot: commands.Bot, specialty: str):
        super().__init__()
        self.bot = bot
        self.specialty = specialty

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        # Parse portfolio links
        links = [l.strip() for l in self.portfolio.value.split("\n") if l.strip()]
        
        # Validate URLs
        invalid_urls = [l for l in links if not validate_url(l)]
        if invalid_urls:
            await interaction.response.send_message(f"❌ Invalid URLs detected: {', '.join(invalid_urls[:3])}", ephemeral=True)
            return
        
        # Check premium
        premium = is_premium(DB_PATH, user_id)
        if not premium and len(links) > 1:
            await interaction.response.send_message("❌ Free accounts may only provide 1 portfolio link. Upgrade to premium for multiple links.", ephemeral=True)
            return
        
        # Validate banner URL
        banner = self.banner_url.value.strip() if self.banner_url.value else None
        if banner and not premium:
            await interaction.response.send_message("❌ Banners are premium-only. Upgrade to use this feature.", ephemeral=True)
            return
        if banner and not validate_url(banner):
            await interaction.response.send_message("❌ Invalid banner URL.", ephemeral=True)
            return
        
        # Validate YouTube URL
        youtube = self.youtube.value.strip() if self.youtube.value else None
        if youtube and not validate_url(youtube):
            await interaction.response.send_message("❌ Invalid YouTube URL.", ephemeral=True)
            return
        
        # Validate social media URLs (premium only)
        twitch = self.twitch.value.strip() if self.twitch.value else None
        instagram = self.instagram.value.strip() if self.instagram.value else None
        tiktok = self.tiktok.value.strip() if self.tiktok.value else None
        twitter = self.twitter.value.strip() if self.twitter.value else None
        
        social_urls = [twitch, instagram, tiktok, twitter]
        social_labels = ["Twitch", "Instagram", "TikTok", "Twitter"]
        
        for url, label in zip(social_urls, social_labels):
            if url:
                if not premium:
                    await interaction.response.send_message(f"❌ {label} integration is premium-only. Upgrade to use this feature.", ephemeral=True)
                    return
                if not validate_url(url):
                    await interaction.response.send_message(f"❌ Invalid {label} URL.", ephemeral=True)
                    return
        
        now_ts = int(time.time())
        profile = {
            "user_id": user_id,
            "bio": self.bio.value,
            "specialty": self.specialty,
            "software": self.software.value,
            "portfolio_links": links,
            "banner_url": banner,
            "youtube_url": youtube,
            "twitch_url": twitch,
            "instagram_url": instagram,
            "tiktok_url": tiktok,
            "twitter_url": twitter,
            "last_bump_time": None,
            "created_at": now_ts,
        }
        
        add_or_update_profile(DB_PATH, profile)
        
        # Award XP for profile creation
        xp_result = add_xp(DB_PATH, user_id, 50)
        if xp_result["leveled_up"]:
            award_badge(DB_PATH, user_id, "profile_creator")
        
        # Auto-post to showcase
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("profile_channel_id"):
            channel_id = int(cfg["profile_channel_id"])
            channel = interaction.guild.get_channel(channel_id) if interaction.guild else None
            if channel:
                embed = build_profile_embed(interaction.user, profile, premium)
                msg = await channel.send(embed=embed)
                set_showcase_message_id(DB_PATH, user_id, str(msg.id))
        
        level_msg = f"\n🎉 Level up! You're now level {xp_result['level']}!" if xp_result["leveled_up"] else ""
        await interaction.response.send_message(f"✅ Profile saved and posted to showcase! +50 XP{level_msg}", ephemeral=True)


class ProfileCreateView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=180)
        self.bot = bot
        self.add_item(SpecialtySelect())
    
    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get selected specialty
        specialty = None
        for item in self.children:
            if isinstance(item, SpecialtySelect) and item.values:
                specialty = item.values[0]
                break
        
        if not specialty:
            await interaction.response.send_message("❌ Please select a specialty first.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ProfileModal(self.bot, specialty))


def build_profile_embed(user: discord.User, profile: dict, premium: bool) -> discord.Embed:
    """Build rich profile embed with all fields"""
    title = f"{'🌟 Premium Profile – ' if premium else '📌 Profile – '}{user.display_name}"
    color = discord.Color.gold() if premium else discord.Color.blurple()
    embed = discord.Embed(title=title, color=color, timestamp=discord.utils.utcnow())
    
    if profile.get("banner_url") and premium:
        embed.set_image(url=profile.get("banner_url"))
    
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="👤 Bio", value=profile.get("bio") or "-", inline=False)
    embed.add_field(name="🎯 Specialty", value=profile.get("specialty") or "-", inline=True)
    embed.add_field(name="🛠️ Software", value=profile.get("software") or "-", inline=True)
    
    links = profile.get("portfolio_links") or []
    if links:
        link_text = "\n".join([f"• [{i+1}]({link})" for i, link in enumerate(links[:10])])
        embed.add_field(name="📂 Portfolio", value=link_text, inline=False)
    
    # Stats
    rating_avg = profile.get("rating_avg", 0.0)
    rating_count = profile.get("rating_count", 0)
    rating_text = f"{'⭐' * int(rating_avg)} {rating_avg:.1f}/5 ({rating_count} reviews)" if rating_count > 0 else "No ratings yet"
    embed.add_field(name="⭐ Rating", value=rating_text, inline=True)
    
    jobs_completed = profile.get("jobs_completed", 0)
    jobs_applied = profile.get("jobs_applied", 0)
    embed.add_field(name="📊 Jobs", value=f"{jobs_completed} completed | {jobs_applied} applied", inline=True)
    
    collabs = profile.get("collabs_completed", 0)
    embed.add_field(name="🤝 Collabs", value=f"{collabs} completed", inline=True)
    
    # Social Media Links (Premium only)
    if premium:
        social_links = []
        if profile.get("youtube_url"):
            social_links.append(f"🎥 [YouTube]({profile['youtube_url']})")
        if profile.get("twitch_url"):
            social_links.append(f"🎮 [Twitch]({profile['twitch_url']})")
        if profile.get("instagram_url"):
            social_links.append(f"📸 [Instagram]({profile['instagram_url']})")
        if profile.get("tiktok_url"):
            social_links.append(f"🎵 [TikTok]({profile['tiktok_url']})")
        if profile.get("twitter_url"):
            social_links.append(f"🐦 [Twitter]({profile['twitter_url']})")
        
        if social_links:
            embed.add_field(name="🔗 Social Media", value=" • ".join(social_links), inline=False)
    
    if profile.get("verified_creator"):
        embed.add_field(name="✅ Status", value="Verified Creator", inline=True)
    
    # Bump cooldown
    last_bump = profile.get("last_bump_time")
    if last_bump:
        cooldown = 6 * 3600 if premium else 24 * 3600
        next_bump = last_bump + cooldown
        if next_bump > time.time():
            embed.add_field(name="⏱️ Next Bump", value=f"<t:{next_bump}:R>", inline=False)
    
    embed.set_footer(text="Editorium Profiles • Use /bump_profile to refresh")
    return embed


class ProfilesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db(DB_PATH)

    @app_commands.command(name="create_profile", description="Create or edit your profile")
    async def create_profile(self, interaction: discord.Interaction):
        view = ProfileCreateView(self.bot)
        await interaction.response.send_message("Select your specialty and click Continue:", view=view, ephemeral=True)

    @app_commands.command(name="profile", description="View a user's profile")
    @app_commands.describe(user="User to view (leave empty for your own)")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target = user or interaction.user
        profile = get_profile(DB_PATH, str(target.id))
        if not profile:
            await interaction.response.send_message("❌ Profile not found. Use /create_profile to create one.", ephemeral=True)
            return
        premium = is_premium(DB_PATH, str(target.id))
        embed = build_profile_embed(target, profile, premium)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="delete_profile", description="Delete your profile")
    async def delete_profile_cmd(self, interaction: discord.Interaction):
        profile = get_profile(DB_PATH, str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("❌ No profile found.", ephemeral=True)
            return
        
        # Delete showcase message
        msg_id = get_showcase_message_id(DB_PATH, str(interaction.user.id))
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("profile_channel_id") and msg_id:
            channel = interaction.guild.get_channel(int(cfg.get("profile_channel_id")))
            if channel:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.delete()
                except:
                    pass
        
        delete_profile(DB_PATH, str(interaction.user.id))
        await interaction.response.send_message("✅ Profile deleted successfully.", ephemeral=True)

    @app_commands.command(name="bump_profile", description="Refresh your profile in the showcase channel")
    async def bump_profile(self, interaction: discord.Interaction):
        profile = get_profile(DB_PATH, str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("❌ Create a profile first with /create_profile", ephemeral=True)
            return
        
        premium = is_premium(DB_PATH, str(interaction.user.id))
        now_ts = int(time.time())
        last = profile.get("last_bump_time") or 0
        cooldown = 6 * 3600 if premium else 24 * 3600
        
        if now_ts - last < cooldown:
            remaining = cooldown - (now_ts - last)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await interaction.response.send_message(f"⏱️ You can bump again in {hours}h {minutes}m", ephemeral=True)
            return
        
        # Delete old message
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if not cfg or not cfg.get("profile_channel_id"):
            await interaction.response.send_message("❌ Profile showcase channel not configured.", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(int(cfg.get("profile_channel_id")))
        if not channel:
            await interaction.response.send_message("❌ Showcase channel not found.", ephemeral=True)
            return
        
        msg_id = get_showcase_message_id(DB_PATH, str(interaction.user.id))
        if msg_id:
            try:
                msg = await channel.fetch_message(int(msg_id))
                await msg.delete()
            except:
                pass
        
        # Post new
        embed = build_profile_embed(interaction.user, profile, premium)
        msg = await channel.send(embed=embed)
        set_showcase_message_id(DB_PATH, str(interaction.user.id), str(msg.id))
        db_bump_profile(DB_PATH, str(interaction.user.id), now_ts)
        
        # Award XP
        add_xp(DB_PATH, str(interaction.user.id), 10)
        
        await interaction.response.send_message("✅ Profile bumped successfully! +10 XP", ephemeral=True)

    @app_commands.command(name="browse_profiles", description="Browse all profiles with filters")
    @app_commands.describe(specialty="Filter by specialty", premium_only="Show only premium profiles")
    async def browse_profiles(self, interaction: discord.Interaction, specialty: Optional[str] = None, premium_only: bool = False):
        # This would implement pagination - placeholder for now
        await interaction.response.send_message("🔍 Profile browsing coming soon! Use the showcase channel for now.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfilesCog(bot))


class ProfileModal(discord.ui.Modal, title="Create / Edit Profile"):
    bio = discord.ui.TextInput(label="Bio", style=discord.TextStyle.long, max_length=200, placeholder="Short bio (200 chars)")
    specialty = discord.ui.TextInput(label="Specialty", placeholder="Editor, Client, Influencer, Streamer, Designer")
    software = discord.ui.TextInput(label="Software", placeholder="E.g., Premiere Pro, After Effects")
    portfolio = discord.ui.TextInput(label="Portfolio Links", placeholder="Comma-separated URLs (free: 1, premium: unlimited)")
    banner_url = discord.ui.TextInput(label="Banner URL (premium only)", required=False)

    def __init__(self, bot: commands.Bot, editing_user_id: Optional[int] = None):
        super().__init__()
        self.bot = bot
        self.editing_user_id = editing_user_id

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        # parse portfolio links
        links = [l.strip() for l in self.portfolio.value.split(",") if l.strip()]
        now_ts = int(time.time())
        profile = {
            "user_id": user_id,
            "bio": self.bio.value,
            "specialty": self.specialty.value,
            "software": self.software.value,
            "portfolio_links": links,
            "banner_url": self.banner_url.value or None,
            "last_bump_time": None,
        }
        # check premium status
        premium = is_premium(DB_PATH, user_id)
        if not premium and len(links) > 1:
            await interaction.response.send_message("Free accounts may only provide 1 portfolio link. Upgrade to premium for multiple links.", ephemeral=True)
            return
        add_or_update_profile(DB_PATH, profile)

        # auto-post to showcase channel if set
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("profile_channel_id"):
            channel_id = int(cfg["profile_channel_id"])
            channel = interaction.guild.get_channel(channel_id) if interaction.guild else None
            if channel:
                embed = build_profile_embed(interaction.user, profile, premium)
                msg = await channel.send(embed=embed)
                set_showcase_message_id(DB_PATH, user_id, str(msg.id))

        await interaction.response.send_message("Profile saved and posted to showcase (if configured).", ephemeral=True)


def build_profile_embed(user: discord.User, profile: dict, premium: bool) -> discord.Embed:
    title = f"{'🌟 Premium Profile – ' if premium else 'Profile – '}{user.display_name}"
    color = discord.Color.gold() if premium else discord.Color.blurple()
    embed = discord.Embed(title=title, color=color)
    if profile.get("banner_url") and premium:
        embed.set_image(url=profile.get("banner_url"))
    embed.add_field(name="Bio", value=profile.get("bio") or "-", inline=False)
    embed.add_field(name="Specialty", value=profile.get("specialty") or "-", inline=True)
    embed.add_field(name="Software", value=profile.get("software") or "-", inline=True)
    links = profile.get("portfolio_links") or []
    if links:
        embed.add_field(name="Portfolio", value="\n".join(links[:10]), inline=False)
    else:
        embed.add_field(name="Portfolio", value="-", inline=False)
    # placeholders for rating/jobs/collabs
    embed.add_field(name="Rating", value="N/A", inline=True)
    embed.add_field(name="Jobs", value="0 completed | 0 applied", inline=True)
    embed.set_footer(text="Editorium Profiles")
    return embed


class ProfilesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db(DB_PATH)

    @app_commands.command(name="create_profile")
    async def create_profile(self, interaction: discord.Interaction):
        """Open modal to create or edit profile"""
        await interaction.response.send_modal(ProfileModal(self.bot))

    @app_commands.command(name="edit_profile")
    async def edit_profile(self, interaction: discord.Interaction):
        profile = get_profile(DB_PATH, str(interaction.user.id))
        modal = ProfileModal(self.bot)
        if profile:
            modal.bio.default = profile.get("bio") or ""
            modal.specialty.default = profile.get("specialty") or ""
            modal.software.default = profile.get("software") or ""
            modal.portfolio.default = ", ".join(profile.get("portfolio_links") or [])
            modal.banner_url.default = profile.get("banner_url") or ""
        await interaction.response.send_modal(modal)

    @app_commands.command(name="delete_profile")
    async def delete_profile(self, interaction: discord.Interaction):
        profile = get_profile(DB_PATH, str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("No profile found.", ephemeral=True)
            return
        # delete showcase post if exists
        msg_id = get_showcase_message_id(DB_PATH, str(interaction.user.id))
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("profile_channel_id") and msg_id:
            channel = interaction.guild.get_channel(int(cfg.get("profile_channel_id")))
            try:
                msg = await channel.fetch_message(int(msg_id))
                await msg.delete()
            except Exception:
                pass
        delete_profile(DB_PATH, str(interaction.user.id))
        await interaction.response.send_message("Profile deleted.", ephemeral=True)

    @app_commands.command(name="profile")
    @app_commands.describe(user="User to view")
    async def profile(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target = user or interaction.user
        profile = get_profile(DB_PATH, str(target.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return
        premium = is_premium(DB_PATH, str(target.id))
        embed = build_profile_embed(target, profile, premium)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bump_profile")
    async def bump_profile(self, interaction: discord.Interaction):
        profile = get_profile(DB_PATH, str(interaction.user.id))
        if not profile:
            await interaction.response.send_message("Profile not found.", ephemeral=True)
            return
        premium = is_premium(DB_PATH, str(interaction.user.id))
        now_ts = int(time.time())
        last = profile.get("last_bump_time") or 0
        cooldown = 6 * 3600 if premium else 24 * 3600
        if now_ts - (last or 0) < cooldown:
            remaining = cooldown - (now_ts - (last or 0))
            await interaction.response.send_message(f"You may bump again in {remaining//3600}h {(remaining%3600)//60}m", ephemeral=True)
            return
        # delete old showcase message
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("profile_channel_id"):
            channel = interaction.guild.get_channel(int(cfg.get("profile_channel_id")))
            msg_id = get_showcase_message_id(DB_PATH, str(interaction.user.id))
            if msg_id:
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    await msg.delete()
                except Exception:
                    pass
            # post new
            embed = build_profile_embed(interaction.user, profile, premium)
            msg = await channel.send(embed=embed)
            set_showcase_message_id(DB_PATH, str(interaction.user.id), str(msg.id))
        db_bump_profile(DB_PATH, str(interaction.user.id), now_ts)
        await interaction.response.send_message("Profile bumped.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfilesCog(bot))
