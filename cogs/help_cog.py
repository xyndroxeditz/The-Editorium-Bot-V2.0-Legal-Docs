"""
Help cog - Comprehensive command guide with interactive buttons
"""
import discord
from discord.ext import commands
from discord import app_commands


class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Profiles", style=discord.ButtonStyle.primary, emoji="👤")
    async def profiles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👤 Profile Commands",
            description="Create and manage your Editorium profile!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="/create_profile",
            value="Create or edit your profile with bio, specialty, software, and portfolio links. Free users get 1 link, premium users get unlimited!",
            inline=False
        )
        embed.add_field(
            name="/profile [@user]",
            value="View any user's profile with their stats, ratings, jobs, and portfolios.",
            inline=False
        )
        embed.add_field(
            name="/bump_profile",
            value="Refresh your profile in the showcase channel. Cooldown: 24h (free) / 6h (premium)",
            inline=False
        )
        embed.add_field(
            name="/delete_profile",
            value="Permanently delete your profile and showcase post.",
            inline=False
        )
        embed.add_field(
            name="/browse_profiles",
            value="Browse all profiles with filters (coming soon)",
            inline=False
        )
        embed.set_footer(text="Editorium Bot V2.0 • The most advanced Discord bot for editors")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Jobs", style=discord.ButtonStyle.success, emoji="💼")
    async def jobs_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💼 Jobs & Applications",
            description="Post jobs and hire talented editors!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="/create_job",
            value="Post a job with title, description, budget, software requirements, and deadline. +30 XP",
            inline=False
        )
        embed.add_field(
            name="/my_jobs",
            value="View all jobs you've posted with their current status.",
            inline=False
        )
        embed.add_field(
            name="/my_applications",
            value="See all jobs you've applied to and their status.",
            inline=False
        )
        embed.add_field(
            name="/close_job <job_id>",
            value="Close one of your open job postings.",
            inline=False
        )
        embed.add_field(
            name="Applying to Jobs",
            value="Click the **Apply** button on any job post to submit your application. +20 XP",
            inline=False
        )
        embed.set_footer(text="Job creators receive applications via DM with Accept/Reject buttons")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Gamification", style=discord.ButtonStyle.secondary, emoji="🏆")
    async def gamification_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏆 XP, Levels & Leaderboards",
            description="Level up and compete with other users!",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Earning XP",
            value=(
                "• Create profile: **+50 XP**\n"
                "• Create job: **+30 XP**\n"
                "• Apply to job: **+20 XP**\n"
                "• Job accepted: **+50 XP**\n"
                "• Bump profile: **+10 XP**\n"
                "• Level up for exclusive perks!"
            ),
            inline=False
        )
        embed.add_field(
            name="/level [@user]",
            value="Check your or another user's level, XP, and progress to next level.",
            inline=False
        )
        embed.add_field(
            name="/leaderboard [category]",
            value="View top 10 users by XP, jobs completed, or ratings. Categories: `xp`, `jobs`, `rating`",
            inline=False
        )
        embed.add_field(
            name="/badges",
            value="View all badges and achievements you've earned.",
            inline=False
        )
        embed.set_footer(text="Grind XP to unlock levels and compete on leaderboards!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Premium", style=discord.ButtonStyle.primary, emoji="🌟")
    async def premium_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🌟 Premium Features",
            description="Unlock exclusive perks with premium!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Basic Premium ($5/month)",
            value=(
                "✅ Unlimited portfolio links\n"
                "✅ Custom banner on profile\n"
                "✅ Social media integration (YouTube, Twitch, Instagram, TikTok, Twitter)\n"
                "✅ Gold profile embed color\n"
                "✅ 6h bump cooldown (vs 24h)\n"
                "✅ 🌟 Premium badge"
            ),
            inline=False
        )
        embed.add_field(
            name="Pro Premium ($10/month)",
            value=(
                "✅ Everything in Basic\n"
                "✅ Priority in job recommendations\n"
                "✅ Advanced analytics dashboard\n"
                "✅ Custom profile themes"
            ),
            inline=False
        )
        embed.add_field(
            name="Elite Premium ($20/month)",
            value=(
                "✅ Everything in Pro\n"
                "✅ Verified Creator badge\n"
                "✅ Priority support\n"
                "✅ Featured profile placement"
            ),
            inline=False
        )
        embed.add_field(
            name="How to Get Premium",
            value="Use `/get_premium` to open a premium support ticket and discuss with the developer!",
            inline=False
        )
        embed.add_field(
            name="Check Your Status",
            value="Use `/premium_status` to check your current premium tier and expiry date.",
            inline=False
        )
        embed.set_footer(text="Premium helps support bot development!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Social", style=discord.ButtonStyle.secondary, emoji="👥")
    async def social_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="👥 Social Features",
            description="Connect with other editors and creators!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="/follow <user>",
            value="Follow users to get notified of their activities (coming soon)",
            inline=False
        )
        embed.add_field(
            name="/collab",
            value="Create collaboration requests to find partners (coming soon)",
            inline=False
        )
        embed.add_field(
            name="/dashboard",
            value="View your personal stats dashboard with all your metrics.",
            inline=False
        )
        embed.add_field(
            name="Marketplace",
            value="Buy and sell editing services with secure escrow (coming soon)",
            inline=False
        )
        embed.set_footer(text="More social features coming soon!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Admin", style=discord.ButtonStyle.danger, emoji="⚙️")
    async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Admin Commands",
            description="Configure the bot for your server (requires Manage Server permission)",
            color=discord.Color.red()
        )
        embed.add_field(
            name="/set_profile_channel <channel>",
            value="Set the channel where profiles will be automatically posted.",
            inline=False
        )
        embed.add_field(
            name="/set_jobs_channel <channel>",
            value="Set the channel for job postings.",
            inline=False
        )
        embed.add_field(
            name="/premium_add <user> <days> [tier]",
            value="Grant premium to a user for specified days. Tiers: basic, pro, elite",
            inline=False
        )
        embed.add_field(
            name="/premium_remove <user>",
            value="Remove premium from a user.",
            inline=False
        )
        embed.add_field(
            name="/premium_list",
            value="View all active premium users and expiry dates.",
            inline=False
        )
        embed.add_field(
            name="/config",
            value="View current server configuration.",
            inline=False
        )
        embed.set_footer(text="Admin commands require Manage Server permission")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Legal", style=discord.ButtonStyle.secondary, emoji="📋")
    async def legal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📋 Legal Documents",
            description="Important legal information for using Editorium Bot",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="/tos",
            value="View our complete Terms of Service covering usage rules, responsibilities, and limitations.",
            inline=False
        )
        embed.add_field(
            name="/privacy_policy",
            value="Learn how we collect, use, and protect your personal data and privacy.",
            inline=False
        )
        embed.add_field(
            name="📖 Full Documents",
            value="Complete legal documents are available on our GitHub repository.",
            inline=False
        )
        embed.set_footer(text="Please read our legal documents carefully • Editorium Bot V2.0")
        await interaction.response.edit_message(embed=embed, view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="View comprehensive command guide")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📚 Editorium Bot V2.0 - Command Guide",
            description=(
                "Welcome to **Editorium Bot** - The most advanced Discord bot for editors, clients, and creators!\n\n"
                "Click the buttons below to explore different command categories:"
            ),
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="🌟 Key Features",
            value=(
                "• Complete profile system with showcase\n"
                "• Job posting and application system\n"
                "• XP, levels, and leaderboards\n"
                "• Premium tiers with exclusive perks\n"
                "• Social features and collaborations\n"
                "• Marketplace (coming soon)"
            ),
            inline=False
        )
        embed.add_field(
            name="🚀 Quick Start",
            value="1. `/create_profile` - Set up your profile\n2. `/create_job` or apply to jobs\n3. `/level` - Track your progress",
            inline=False
        )
        embed.add_field(
            name="📋 Legal",
            value="`/tos` - View Terms of Service\n`/privacy_policy` - View Privacy Policy",
            inline=False
        )
        embed.set_footer(text="Use the buttons below to navigate • Editorium Bot V2.0")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        
        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="info", description="Bot information and statistics")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ℹ️ Editorium Bot V2.0",
            description="The most advanced Discord bot for editor communities!",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Version", value="2.0.0", inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count for g in self.bot.guilds):,}", inline=True)
        embed.add_field(
            name="Features",
            value=(
                "✅ 45+ Features Implemented\n"
                "✅ Profile System with Premium\n"
                "✅ Jobs & Applications\n"
                "✅ XP & Gamification\n"
                "✅ Leaderboards & Badges\n"
                "✅ Interactive UI with Buttons\n"
                "✅ Advanced Database System"
            ),
            inline=False
        )
        embed.add_field(
            name="Legal Compliance",
            value="GDPR • CCPA • Discord ToS Compliant\nUse `/terms` and `/privacy` for details",
            inline=False
        )
        embed.add_field(
            name="Support",
            value="For support, contact server administrators or use `/help` for command info.",
            inline=False
        )
        embed.set_footer(text="Built with discord.py • Editorium Bot V2.0")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="tos", description="View Terms of Service")
    async def tos(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Terms of Service - Editorium Bot",
            description="Please read our complete Terms of Service carefully.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📖 Full Document",
            value="Our complete Terms of Service is available at:\nhttps://xyndroxeditz.github.io/The-Editorium-Bot-V2.0/terms-of-service.html",
            inline=False
        )
        embed.add_field(
            name="⚠️ Important Points",
            value=(
                "• You must be 13+ to use the Bot\n"
                "• Use the Bot responsibly and professionally\n"
                "• Premium subscriptions have specific terms\n"
                "• We respect your privacy and data rights\n"
                "• Service is provided 'as is'"
            ),
            inline=False
        )
        embed.add_field(
            name="❓ Questions?",
            value="Contact us through `/get_premium` for support or use `/help` for more commands.",
            inline=False
        )
        embed.set_footer(text="Last updated: October 18, 2025 • Editorium Bot V2.0")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="privacy_policy", description="View Privacy Policy")
    async def privacy_policy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔒 Privacy Policy - Editorium Bot",
            description="Learn how we protect and handle your data.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📖 Full Document",
            value="Our complete Privacy Policy is available at:\nhttps://xyndroxeditz.github.io/The-Editorium-Bot-V2.0/privacy-policy.html",
            inline=False
        )
        embed.add_field(
            name="🔍 What We Collect",
            value=(
                "• Discord account information\n"
                "• Profile and portfolio data\n"
                "• Usage statistics and interactions\n"
                "• Premium subscription information"
            ),
            inline=False
        )
        embed.add_field(
            name="🛡️ How We Protect Your Data",
            value=(
                "• Data encrypted in transit and at rest\n"
                "• Access limited to authorized personnel\n"
                "• Regular security audits\n"
                "• GDPR and CCPA compliant"
            ),
            inline=False
        )
        embed.add_field(
            name="📧 Contact for Privacy Concerns",
            value="Use `/get_premium` to contact our developer directly for privacy-related questions.",
            inline=False
        )
        embed.set_footer(text="Last updated: October 18, 2025 • Editorium Bot V2.0")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
