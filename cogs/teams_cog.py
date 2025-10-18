import discord
from discord import app_commands
from discord.ext import commands
import time
import uuid
import re
from typing import Optional, Dict, Any, List

from db.sqlite_helper import (
    create_team, get_team, get_user_team, get_team_members,
    add_team_member, update_team_settings, search_teams,
    create_team_invite, get_team_invite, accept_team_invite, decline_team_invite
)


class TeamCreationModal(discord.ui.Modal, title="Create Your Team"):
    def __init__(self):
        super().__init__()

    team_name = discord.ui.TextInput(
        label="Team Name",
        placeholder="Enter your team name (3-50 characters)",
        min_length=3,
        max_length=50,
        required=True
    )

    team_description = discord.ui.TextInput(
        label="Team Description",
        placeholder="Describe your team's focus and goals",
        style=discord.TextStyle.paragraph,
        min_length=10,
        max_length=500,
        required=True
    )

    max_members = discord.ui.TextInput(
        label="Maximum Members",
        placeholder="Enter max members (2-50, default: 10)",
        min_length=1,
        max_length=2,
        required=False,
        default="10"
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Validate team name
        team_name = self.team_name.value.strip()
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', team_name):
            await interaction.response.send_message(
                "❌ Team name can only contain letters, numbers, spaces, hyphens, underscores, and periods.",
                ephemeral=True
            )
            return

        # Validate max members
        try:
            max_members = int(self.max_members.value)
            if max_members < 2 or max_members > 50:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message(
                "❌ Maximum members must be a number between 2 and 50.",
                ephemeral=True
            )
            return

        # Check if user already has a team
        db_path = interaction.client.db_path
        existing_team = get_user_team(db_path, str(interaction.user.id))
        if existing_team:
            await interaction.response.send_message(
                f"❌ You are already a member of **{existing_team['name']}**. Leave your current team before creating a new one.",
                ephemeral=True
            )
            return

        # Generate unique team ID
        team_id = str(uuid.uuid4())[:8].upper()

        # Create the team
        try:
            create_team(
                db_path=db_path,
                team_id=team_id,
                name=team_name,
                description=self.team_description.value.strip(),
                leader_id=str(interaction.user.id),
                max_members=max_members
            )

            embed = discord.Embed(
                title="🎉 Team Created Successfully!",
                description=f"**{team_name}** has been created with you as the leader!",
                color=discord.Color.green()
            )
            embed.add_field(name="Team ID", value=f"`{team_id}`", inline=True)
            embed.add_field(name="Max Members", value=str(max_members), inline=True)
            embed.add_field(
                name="Next Steps",
                value="• Use `/team invite` to invite members\n• Use `/team settings` to customize your team\n• Use `/team dashboard` to manage your team",
                inline=False
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create team: {str(e)}",
                ephemeral=True
            )


class TeamInviteView(discord.ui.View):
    def __init__(self, invite_id: str, team_name: str, inviter_name: str):
        super().__init__(timeout=172800)  # 48 hours
        self.invite_id = invite_id
        self.team_name = team_name
        self.inviter_name = inviter_name

    @discord.ui.button(label="Accept Invite", style=discord.ButtonStyle.success, emoji="✅")
    async def accept_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_path = interaction.client.db_path

        # Check if user already has a team
        existing_team = get_user_team(db_path, str(interaction.user.id))
        if existing_team:
            await interaction.response.send_message(
                f"❌ You are already a member of **{existing_team['name']}**. Leave your current team before joining another.",
                ephemeral=True
            )
            return

        success = accept_team_invite(db_path, self.invite_id)
        if success:
            embed = discord.Embed(
                title="🎉 Welcome to the Team!",
                description=f"You have successfully joined **{self.team_name}**!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Disable buttons
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message(
                "❌ Failed to accept invite. It may have expired or the team is full.",
                ephemeral=True
            )

    @discord.ui.button(label="Decline Invite", style=discord.ButtonStyle.danger, emoji="❌")
    async def decline_invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        db_path = interaction.client.db_path
        success = decline_team_invite(db_path, self.invite_id)

        if success:
            embed = discord.Embed(
                title="Invite Declined",
                description=f"You have declined the invitation to join **{self.team_name}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Disable buttons
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message(
                "❌ Failed to decline invite. It may have already been processed.",
                ephemeral=True
            )


class TeamsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="team_create", description="Create a new editing team")
    @app_commands.checks.cooldown(1, 300)  # 5 minute cooldown to prevent spam
    async def team_create(self, interaction: discord.Interaction):
        """Create a new team with customizable settings"""
        modal = TeamCreationModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="team_info", description="View information about a team")
    @app_commands.describe(team_id="The team ID to look up (leave empty to view your own team)")
    async def team_info(self, interaction: discord.Interaction, team_id: Optional[str] = None):
        """Display detailed information about a team"""
        db_path = self.bot.db_path

        if team_id is None:
            # Get user's team
            team = get_user_team(db_path, str(interaction.user.id))
            if not team:
                await interaction.response.send_message(
                    "❌ You are not a member of any team. Use `/team_create` to create one or `/team_join` to join an existing team.",
                    ephemeral=True
                )
                return
        else:
            # Look up specific team
            team = get_team(db_path, team_id.upper())
            if not team:
                await interaction.response.send_message(
                    f"❌ No team found with ID `{team_id}`.",
                    ephemeral=True
                )
                return

        # Get team members
        members = get_team_members(db_path, team['team_id'])
        leader = next((m for m in members if m['role'] == 'leader'), None)

        embed = discord.Embed(
            title=f"🎭 {team['name']}",
            description=team['description'],
            color=discord.Color.blue()
        )

        embed.add_field(name="Team ID", value=f"`{team['team_id']}`", inline=True)
        embed.add_field(name="Leader", value=f"<@{leader['user_id']}>" if leader else "Unknown", inline=True)
        embed.add_field(name="Members", value=f"{len(members)}/{team['max_members']}", inline=True)

        embed.add_field(
            name="Recruiting",
            value="✅ Open" if team['is_recruiting'] else "❌ Closed",
            inline=True
        )

        created_at = f"<t:{team['created_at']}:F>" if team['created_at'] else "Unknown"
        embed.add_field(name="Created", value=created_at, inline=True)

        if team['team_website']:
            embed.add_field(name="Website", value=team['team_website'], inline=False)

        if team['team_social_links']:
            social_links = []
            for platform, link in team['team_social_links'].items():
                if link:
                    social_links.append(f"[{platform.title()}]({link})")
            if social_links:
                embed.add_field(name="Social Links", value=" | ".join(social_links), inline=False)

        # List members
        member_list = []
        for member in members:
            role_emoji = {
                'leader': '👑',
                'admin': '⚡',
                'member': '👤'
            }.get(member['role'], '👤')
            member_list.append(f"{role_emoji} <@{member['user_id']}>")

        if member_list:
            embed.add_field(
                name=f"Team Members ({len(members)})",
                value="\n".join(member_list),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="team_invite", description="Invite a user to join your team")
    @app_commands.describe(
        user="The user to invite",
        message="Optional personal message with the invite"
    )
    async def team_invite(self, interaction: discord.Interaction, user: discord.Member, message: Optional[str] = None):
        """Invite a user to join your team"""
        db_path = self.bot.db_path

        # Check if user is team leader or admin
        team = get_user_team(db_path, str(interaction.user.id))
        if not team:
            await interaction.response.send_message(
                "❌ You are not a member of any team.",
                ephemeral=True
            )
            return

        if team['role'] not in ['leader', 'admin']:
            await interaction.response.send_message(
                "❌ Only team leaders and admins can send invites.",
                ephemeral=True
            )
            return

        # Check if team is recruiting
        if not team['is_recruiting']:
            await interaction.response.send_message(
                "❌ Your team is not currently recruiting new members.",
                ephemeral=True
            )
            return

        # Check if target user already has a team
        target_team = get_user_team(db_path, str(user.id))
        if target_team:
            await interaction.response.send_message(
                f"❌ {user.mention} is already a member of **{target_team['name']}**.",
                ephemeral=True
            )
            return

        # Check team capacity
        members = get_team_members(db_path, team['team_id'])
        if len(members) >= team['max_members']:
            await interaction.response.send_message(
                "❌ Your team is already at maximum capacity.",
                ephemeral=True
            )
            return

        # Check if user is already invited
        # Note: This is a simplified check - in production you'd want to check pending invites

        # Create invite
        invite_id = str(uuid.uuid4())[:12].upper()
        create_team_invite(
            db_path=db_path,
            invite_id=invite_id,
            team_id=team['team_id'],
            invited_user_id=str(user.id),
            invited_by=str(interaction.user.id),
            message=message or ""
        )

        # Send invite embed to target user
        embed = discord.Embed(
            title=f"🎭 Team Invitation from {interaction.user.display_name}",
            description=f"You've been invited to join **{team['name']}**!",
            color=discord.Color.blue()
        )

        embed.add_field(name="Team Description", value=team['description'], inline=False)

        if message:
            embed.add_field(name="Personal Message", value=message, inline=False)

        embed.add_field(
            name="Team Stats",
            value=f"Members: {len(members)}/{team['max_members']}\nCreated: <t:{team['created_at']}:R>",
            inline=False
        )

        embed.set_footer(text=f"Invite ID: {invite_id} • Expires in 48 hours")

        view = TeamInviteView(invite_id, team['name'], interaction.user.display_name)

        try:
            await user.send(embed=embed, view=view)
            await interaction.response.send_message(
                f"✅ Invitation sent to {user.mention}!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ Cannot send DM to {user.mention}. They may have DMs disabled.",
                ephemeral=True
            )

    @app_commands.command(name="team_search", description="Search for teams that are recruiting")
    @app_commands.describe(query="Search term (team name or description)")
    async def team_search(self, interaction: discord.Interaction, query: str):
        """Search for teams that are currently recruiting"""
        if len(query) < 2:
            await interaction.response.send_message(
                "❌ Search query must be at least 2 characters long.",
                ephemeral=True
            )
            return

        db_path = self.bot.db_path
        teams = search_teams(db_path, query, limit=5)

        if not teams:
            await interaction.response.send_message(
                f"❌ No recruiting teams found matching '{query}'.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"🔍 Teams Recruiting - '{query}'",
            description=f"Found {len(teams)} team(s)",
            color=discord.Color.blue()
        )

        for team in teams:
            value = f"👥 {team['member_count']}/{team['max_members']} members\n{team['description'][:100]}{'...' if len(team['description']) > 100 else ''}"
            embed.add_field(
                name=f"{team['name']} (`{team['team_id']}`)",
                value=value,
                inline=False
            )

        embed.set_footer(text="Use /team_info <team_id> for more details")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="team_leave", description="Leave your current team")
    async def team_leave(self, interaction: discord.Interaction):
        """Leave your current team"""
        db_path = self.bot.db_path

        team = get_user_team(db_path, str(interaction.user.id))
        if not team:
            await interaction.response.send_message(
                "❌ You are not a member of any team.",
                ephemeral=True
            )
            return

        if team['role'] == 'leader':
            await interaction.response.send_message(
                "❌ Team leaders cannot leave their team. Transfer leadership first or disband the team.",
                ephemeral=True
            )
            return

        # Confirm leaving
        view = LeaveTeamView(team['name'])
        await interaction.response.send_message(
            f"⚠️ Are you sure you want to leave **{team['name']}**? This action cannot be undone.",
            view=view,
            ephemeral=True
        )

    @app_commands.command(name="team_settings", description="Update your team's settings (leaders only)")
    async def team_settings(self, interaction: discord.Interaction):
        """Update team settings - leaders only"""
        db_path = self.bot.db_path

        team = get_user_team(db_path, str(interaction.user.id))
        if not team or team['role'] != 'leader':
            await interaction.response.send_message(
                "❌ Only team leaders can modify team settings.",
                ephemeral=True
            )
            return

        # This would open a settings modal - simplified for now
        embed = discord.Embed(
            title="⚙️ Team Settings",
            description="Team settings management is coming soon!",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Available Settings",
            value="• Team name and description\n• Maximum members\n• Recruiting status\n• Team banner and website\n• Social media links",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class LeaveTeamView(discord.ui.View):
    def __init__(self, team_name: str):
        super().__init__(timeout=300)  # 5 minutes
        self.team_name = team_name

    @discord.ui.button(label="Confirm Leave", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def confirm_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        from db.sqlite_helper import remove_team_member
        db_path = interaction.client.db_path

        try:
            remove_team_member(db_path, get_user_team(db_path, str(interaction.user.id))['team_id'], str(interaction.user.id))
            embed = discord.Embed(
                title="👋 Left Team",
                description=f"You have successfully left **{self.team_name}**.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to leave team: {str(e)}",
                ephemeral=True
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Action cancelled.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TeamsCog(bot))