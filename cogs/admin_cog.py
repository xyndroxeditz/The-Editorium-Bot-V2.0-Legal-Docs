"""
Admin cog - Server configuration (premium commands moved to premium_cog)
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
from db.sqlite_helper import set_config, get_config

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="set_profile_channel", description="Set channel for profile showcase")
    @app_commands.describe(channel="Channel to post profiles")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_profile_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        cfg['profile_channel_id'] = str(channel.id)
        set_config(DB_PATH, str(interaction.guild.id), cfg)
        await interaction.response.send_message(f"✅ Profile showcase channel set to {channel.mention}")

    @app_commands.command(name="set_jobs_channel", description="Set channel for job postings")
    @app_commands.describe(channel="Channel to post jobs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_jobs_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        cfg['jobs_channel_id'] = str(channel.id)
        set_config(DB_PATH, str(interaction.guild.id), cfg)
        await interaction.response.send_message(f"✅ Jobs channel set to {channel.mention}")

    @app_commands.command(name="config", description="View server configuration")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def config(self, interaction: discord.Interaction):
        cfg = get_config(DB_PATH, str(interaction.guild.id))
        if not cfg:
            await interaction.response.send_message("No configuration set yet.", ephemeral=True)
            return
        
        embed = discord.Embed(title="⚙️ Server Configuration", color=discord.Color.blue())
        
        if cfg.get('profile_channel_id'):
            channel = interaction.guild.get_channel(int(cfg['profile_channel_id']))
            embed.add_field(name="Profile Channel", value=channel.mention if channel else "Not set")
        
        if cfg.get('jobs_channel_id'):
            channel = interaction.guild.get_channel(int(cfg['jobs_channel_id']))
            embed.add_field(name="Jobs Channel", value=channel.mention if channel else "Not set")
        
        if cfg.get('available_job_roles'):
            try:
                import json
                roles = json.loads(cfg.get('available_job_roles', "[]"))
                embed.add_field(name="Available Job Roles", value=", ".join(roles) if roles else "None", inline=False)
            except:
                pass
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_job_role", description="Add a role option for job postings")
    @app_commands.describe(role="Role to add (mention the role or provide name)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_job_role(self, interaction: discord.Interaction, role: discord.Role):
        import json
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        
        try:
            roles = json.loads(cfg.get('available_job_roles', "[]"))
        except:
            roles = []
        
        role_name = role.name
        
        if role_name in roles:
            await interaction.response.send_message(f"❌ Role **{role_name}** already exists.", ephemeral=True)
            return
        
        roles.append(role_name)
        cfg['available_job_roles'] = json.dumps(roles)
        set_config(DB_PATH, str(interaction.guild.id), cfg)
        
        await interaction.response.send_message(f"✅ Added job role: **{role_name}**\nJob creators can now select this role when posting jobs.", ephemeral=True)

    @app_commands.command(name="remove_job_role", description="Remove a role option from job postings")
    @app_commands.describe(role="Role to remove (mention the role)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_job_role(self, interaction: discord.Interaction, role: discord.Role):
        import json
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        
        try:
            roles = json.loads(cfg.get('available_job_roles', "[]"))
        except:
            roles = []
        
        role_name = role.name
        
        if role_name not in roles:
            await interaction.response.send_message(f"❌ Role **{role_name}** not found.", ephemeral=True)
            return
        
        roles.remove(role_name)
        cfg['available_job_roles'] = json.dumps(roles)
        set_config(DB_PATH, str(interaction.guild.id), cfg)
        
        await interaction.response.send_message(f"✅ Removed job role: **{role_name}**", ephemeral=True)

    @app_commands.command(name="list_job_roles", description="List all available job roles")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def list_job_roles(self, interaction: discord.Interaction):
        import json
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        
        try:
            roles = json.loads(cfg.get('available_job_roles', "[]"))
        except:
            roles = []
        
        if not roles:
            await interaction.response.send_message("No job roles configured yet. Use `/add_job_role` to add some!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📋 Available Job Roles",
            description="Job creators can select these roles to ping when posting jobs:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Roles", value="\n".join([f"• {role}" for role in roles]), inline=False)
        embed.set_footer(text=f"Total: {len(roles)} roles")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear_job_roles", description="Clear all job role options")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def clear_job_roles(self, interaction: discord.Interaction):
        import json
        cfg = get_config(DB_PATH, str(interaction.guild.id)) or {}
        cfg['available_job_roles'] = json.dumps([])
        set_config(DB_PATH, str(interaction.guild.id), cfg)
        
        await interaction.response.send_message("✅ Cleared all job roles. Use `/add_job_role` to add new ones.", ephemeral=True)

    @app_commands.command(name="sync_commands", description="Force sync slash commands for this server (admin only)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def sync_commands(self, interaction: discord.Interaction):
        """Force sync commands for this guild"""
        try:
            synced = await self.bot.tree.sync(guild=interaction.guild)
            await interaction.response.send_message(
                f"✅ Synced {len(synced)} slash commands for this server!\n"
                "Commands should appear immediately in Discord.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to sync commands: {str(e)}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
