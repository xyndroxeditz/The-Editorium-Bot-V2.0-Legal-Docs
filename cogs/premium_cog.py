"""
Premium cog - Developer-only premium management with ticket system
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
import time
from dotenv import load_dotenv
from db.sqlite_helper import (
    add_premium, remove_premium, list_active_premium, is_premium, get_profile
)

load_dotenv()
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")
DEVELOPER_ID = int(os.getenv('DEVELOPER_ID', '0'))


class PremiumTicketView(discord.ui.View):
    """View with button to contact developer for premium"""
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Contact Developer", style=discord.ButtonStyle.primary, emoji="📧", custom_id="premium_ticket")
    async def contact_developer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Create a private ticket channel and notify developer"""
        guild = interaction.guild
        user = interaction.user
        
        # Check if user already has an open ticket
        existing_channel = discord.utils.get(guild.channels, name=f"premium-ticket-{user.id}")
        if existing_channel:
            await interaction.response.send_message(
                f"You already have an open premium ticket: {existing_channel.mention}",
                ephemeral=True
            )
            return
        
        # Create category if doesn't exist
        category = discord.utils.get(guild.categories, name="Premium Tickets")
        if not category:
            category = await guild.create_category("Premium Tickets")
            # Set category permissions: only developer and ticket creators can see
            await category.set_permissions(guild.default_role, view_channel=False)
        
        # Create private channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)
        }
        
        # Add developer permissions if developer is in guild
        developer = guild.get_member(DEVELOPER_ID)
        if developer:
            overwrites[developer] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_messages=True, manage_channels=True
            )
        
        channel = await guild.create_text_channel(
            f"premium-ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )
        
        # Create grant premium view
        grant_view = GrantPremiumView(user.id)
        
        # Send welcome message in ticket channel
        embed = discord.Embed(
            title="🌟 Premium Support Ticket",
            description=f"Hello {user.mention}! This is your private premium support channel.",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💎 Premium Tiers",
            value=(
                "**Basic** - $5/month\n"
                "✅ Unlimited portfolio links\n"
                "✅ Custom banners\n"
                "✅ Gold embeds\n"
                "✅ 6h bump cooldown\n\n"
                "**Pro** - $10/month\n"
                "✅ All Basic features\n"
                "✅ Priority job recommendations\n"
                "✅ Advanced analytics\n\n"
                "**Elite** - $20/month\n"
                "✅ All Pro features\n"
                "✅ Verified badge ✅\n"
                "✅ Featured placement\n"
                "✅ Priority support"
            ),
            inline=False
        )
        embed.add_field(
            name="📝 Next Steps",
            value="The developer has been notified and will respond shortly. Please describe what tier you're interested in and any questions you have.",
            inline=False
        )
        embed.set_footer(text="Developer-only controls below")
        
        await channel.send(embed=embed, view=grant_view)
        await channel.send(f"{user.mention} Welcome to your premium ticket!")
        
        # Try to DM the developer
        try:
            dev_user = await interaction.client.fetch_user(DEVELOPER_ID)
            dm_embed = discord.Embed(
                title="🎫 New Premium Ticket",
                description=f"**User:** {user.mention} ({user.name}#{user.discriminator})\n**ID:** {user.id}",
                color=discord.Color.gold()
            )
            dm_embed.add_field(
                name="Ticket Channel",
                value=f"[#{channel.name}](https://discord.com/channels/{guild.id}/{channel.id})",
                inline=False
            )
            dm_embed.set_thumbnail(url=user.display_avatar.url)
            await dev_user.send(embed=dm_embed, view=JumpToTicketView(guild.id, channel.id))
        except:
            pass  # DM failed, developer will see it in the channel
        
        await interaction.response.send_message(
            f"✅ Premium ticket created! Check {channel.mention}",
            ephemeral=True
        )


class JumpToTicketView(discord.ui.View):
    """View with button to jump to ticket channel"""
    def __init__(self, guild_id: int, channel_id: int):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Jump to Ticket",
            style=discord.ButtonStyle.link,
            url=f"https://discord.com/channels/{guild_id}/{channel_id}"
        ))


class GrantPremiumView(discord.ui.View):
    """View for developer to grant premium in ticket"""
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    @discord.ui.button(label="Grant Basic (30d)", style=discord.ButtonStyle.green, emoji="⭐", custom_id="grant_basic")
    async def grant_basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.grant_premium(interaction, "basic", 30)
    
    @discord.ui.button(label="Grant Pro (30d)", style=discord.ButtonStyle.blurple, emoji="💎", custom_id="grant_pro")
    async def grant_pro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.grant_premium(interaction, "pro", 30)
    
    @discord.ui.button(label="Grant Elite (30d)", style=discord.ButtonStyle.primary, emoji="👑", custom_id="grant_elite")
    async def grant_elite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.grant_premium(interaction, "elite", 30)
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the ticket channel"""
        if interaction.user.id != DEVELOPER_ID:
            await interaction.response.send_message("Only the developer can close tickets.", ephemeral=True)
            return
        
        await interaction.response.send_message("Closing ticket in 5 seconds...", ephemeral=False)
        await interaction.channel.send("🔒 **Ticket closed by developer.** This channel will be deleted shortly.")
        
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()
    
    async def grant_premium(self, interaction: discord.Interaction, tier: str, days: int):
        """Grant premium to user"""
        if interaction.user.id != DEVELOPER_ID:
            await interaction.response.send_message("Only the developer can grant premium.", ephemeral=True)
            return
        
        expiry = int(time.time()) + (days * 24 * 3600)
        add_premium(DB_PATH, str(self.user_id), expiry, tier)
        
        user = await interaction.client.fetch_user(self.user_id)
        
        embed = discord.Embed(
            title="✅ Premium Granted!",
            description=f"**{tier.capitalize()} Premium** has been granted to {user.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Duration", value=f"{days} days", inline=True)
        embed.add_field(name="Expires", value=f"<t:{expiry}:F>", inline=True)
        embed.add_field(
            name="🎉 Active Benefits",
            value=(
                "✅ Unlimited portfolio links\n"
                "✅ Custom banners\n"
                "✅ Gold embeds\n"
                "✅ 6-hour bump cooldown\n"
                "✅ Premium badge"
            ) + (
                "\n✅ Priority job recommendations\n✅ Advanced analytics" if tier in ["pro", "elite"] else ""
            ) + (
                "\n✅ Verified badge ✅\n✅ Featured placement" if tier == "elite" else ""
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title="🎉 Premium Activated!",
                description=f"Your **{tier.capitalize()} Premium** has been activated!",
                color=discord.Color.gold()
            )
            dm_embed.add_field(name="Duration", value=f"{days} days", inline=True)
            dm_embed.add_field(name="Expires", value=f"<t:{expiry}:R>", inline=True)
            dm_embed.add_field(
                name="Your Benefits",
                value=(
                    "✅ Unlimited portfolio links\n"
                    "✅ Custom banners on profile\n"
                    "✅ Gold profile embeds\n"
                    "✅ Bump every 6 hours\n"
                    "✅ 🌟 Premium badge"
                ),
                inline=False
            )
            dm_embed.set_footer(text="Thank you for supporting The Editorium!")
            await user.send(embed=dm_embed)
        except:
            pass


class PremiumCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Register persistent views
        self.bot.add_view(PremiumTicketView())
    
    @app_commands.command(name="get_premium", description="Request premium subscription")
    async def get_premium(self, interaction: discord.Interaction):
        """Open premium request ticket"""
        embed = discord.Embed(
            title="🌟 Get Premium",
            description="Unlock exclusive features and support The Editorium Bot!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="💎 Premium Tiers",
            value=(
                "**Basic** - $5/month\n"
                "**Pro** - $10/month\n"
                "**Elite** - $20/month"
            ),
            inline=False
        )
        embed.add_field(
            name="🎯 How It Works",
            value=(
                "1. Click **Contact Developer** below\n"
                "2. A private ticket channel will be created\n"
                "3. Discuss your needs with the developer\n"
                "4. Get premium activated instantly!"
            ),
            inline=False
        )
        embed.set_footer(text="Click the button below to get started")
        
        await interaction.response.send_message(embed=embed, view=PremiumTicketView(), ephemeral=True)
    
    @app_commands.command(name="dev_premium_add", description="[DEVELOPER ONLY] Grant premium to user")
    @app_commands.describe(user="User to grant premium", days="Number of days", tier="Premium tier")
    @app_commands.choices(tier=[
        app_commands.Choice(name="Basic", value="basic"),
        app_commands.Choice(name="Pro", value="pro"),
        app_commands.Choice(name="Elite", value="elite")
    ])
    async def dev_premium_add(self, interaction: discord.Interaction, user: discord.User, days: int = 30, tier: str = "basic"):
        """Developer-only command to grant premium"""
        if interaction.user.id != DEVELOPER_ID:
            await interaction.response.send_message("❌ This command is only available to the bot developer.", ephemeral=True)
            return
        
        expiry = int(time.time()) + (days * 24 * 3600)
        add_premium(DB_PATH, str(user.id), expiry, tier)
        
        await interaction.response.send_message(
            f"✅ Granted **{tier.capitalize()} Premium** to {user.mention} for **{days} days**.\nExpires: <t:{expiry}:F>",
            ephemeral=True
        )
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title="🎉 Premium Activated!",
                description=f"You've been granted **{tier.capitalize()} Premium**!",
                color=discord.Color.gold()
            )
            dm_embed.add_field(name="Duration", value=f"{days} days")
            dm_embed.add_field(name="Expires", value=f"<t:{expiry}:R>")
            await user.send(embed=dm_embed)
        except:
            pass
    
    @app_commands.command(name="dev_premium_remove", description="[DEVELOPER ONLY] Remove premium from user")
    @app_commands.describe(user="User to revoke premium")
    async def dev_premium_remove(self, interaction: discord.Interaction, user: discord.User):
        """Developer-only command to remove premium"""
        if interaction.user.id != DEVELOPER_ID:
            await interaction.response.send_message("❌ This command is only available to the bot developer.", ephemeral=True)
            return
        
        remove_premium(DB_PATH, str(user.id))
        await interaction.response.send_message(f"✅ Removed premium from {user.mention}", ephemeral=True)
    
    @app_commands.command(name="dev_premium_list", description="[DEVELOPER ONLY] List all premium users")
    async def dev_premium_list(self, interaction: discord.Interaction):
        """Developer-only command to list premium users"""
        if interaction.user.id != DEVELOPER_ID:
            await interaction.response.send_message("❌ This command is only available to the bot developer.", ephemeral=True)
            return
        
        active = list_active_premium(DB_PATH)
        if not active:
            await interaction.response.send_message("No active premium users.", ephemeral=True)
            return
        
        embed = discord.Embed(title="🌟 Active Premium Users", color=discord.Color.gold())
        for entry in active[:25]:
            try:
                user = await self.bot.fetch_user(int(entry['user_id']))
                tier = entry.get('tier', 'basic')
                embed.add_field(
                    name=f"{user.display_name} ({tier.capitalize()})",
                    value=f"Expires: <t:{entry['expiry_date']}:R>",
                    inline=False
                )
            except:
                pass
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="premium_status", description="Check your premium status")
    async def premium_status(self, interaction: discord.Interaction):
        """Check premium status"""
        premium_data = is_premium(DB_PATH, str(interaction.user.id))
        
        if premium_data:
            tier = premium_data.get('tier', 'basic')
            expiry = premium_data['expiry_date']
            
            embed = discord.Embed(
                title="🌟 Your Premium Status",
                description=f"You have **{tier.capitalize()} Premium**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="Tier", value=tier.capitalize(), inline=True)
            embed.add_field(name="Expires", value=f"<t:{expiry}:R>", inline=True)
            embed.add_field(
                name="Active Benefits",
                value=(
                    "✅ Unlimited portfolio links\n"
                    "✅ Custom banners\n"
                    "✅ Gold embeds\n"
                    "✅ 6-hour bump cooldown\n"
                    "✅ Premium badge"
                ),
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="💎 Premium Not Active",
                description="You don't have premium yet. Use `/get_premium` to upgrade!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Premium Benefits",
                value=(
                    "✅ Unlimited portfolio links\n"
                    "✅ Custom banners\n"
                    "✅ Gold embeds\n"
                    "✅ 6-hour bump cooldown\n"
                    "✅ Premium badge\n"
                    "✅ Priority support"
                ),
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(PremiumCog(bot))
