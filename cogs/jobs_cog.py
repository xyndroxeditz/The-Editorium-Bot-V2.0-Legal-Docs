"""
Jobs cog - Complete job creation, application, and management system
"""
import discord
from discord.ext import commands
from discord import app_commands
import os
from typing import Optional, List
from db.jobs_helper import (
    create_job, get_job, get_user_jobs, update_job_status,
    create_application, get_job_applications, update_application_status,
    get_user_applications
)
from db.gamification_helper import add_xp, award_achievement
from db.sqlite_helper import get_config, get_profile
import time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "editorium.db")
DEVELOPER_ID = int(os.getenv('DEVELOPER_ID', '0'))


class RoleSelectionView(discord.ui.View):
    """View for selecting roles to ping before job is posted"""
    def __init__(self, bot: commands.Bot, guild_id: int, available_roles: List[str]):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild_id = guild_id
        self.selected_roles = []
        self.available_roles = available_roles

        # Add select menu with available roles
        if available_roles:
            options = [discord.SelectOption(label=role, value=role) for role in available_roles[:25]]
            self.role_select = discord.ui.Select(
                placeholder="Select roles to ping for this job",
                options=options,
                min_values=0,  # Allow no selection
                max_values=len(options)
            )
            self.role_select.callback = self.role_selected
            self.add_item(self.role_select)

        # Add confirm button to proceed
        confirm_btn = discord.ui.Button(label="Continue to Job Form", style=discord.ButtonStyle.primary, emoji="✅")
        confirm_btn.callback = self.confirm_selection
        self.add_item(confirm_btn)

    async def role_selected(self, interaction: discord.Interaction):
        """Handle role selection and show confirmation"""
        self.selected_roles = self.role_select.values

        # Create confirmation message
        if self.selected_roles:
            roles_text = ", ".join(f"@{role}" for role in self.selected_roles)
            message = f"✅ **Selected roles to ping:** {roles_text}\n\nClick **Continue to Job Form** to proceed with job creation."
        else:
            message = "ℹ️ **No roles selected** - This job won't ping any specific roles.\n\nClick **Continue to Job Form** to proceed with job creation."

        await interaction.response.edit_message(content=message, view=self)

    async def confirm_selection(self, interaction: discord.Interaction):
        # Get the selected roles from the select menu
        if hasattr(self, 'role_select') and self.role_select.values:
            self.selected_roles = self.role_select.values
        else:
            self.selected_roles = []

        await interaction.response.send_modal(JobCreationModal(self.bot, self.selected_roles))
        self.stop()


class JobCreationModal(discord.ui.Modal, title="Create Job Post"):
    title_input = discord.ui.TextInput(label="Job Title", placeholder="E.g., YouTube Video Editor Needed", max_length=100)
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.long, placeholder="Detailed job description (include software/tools needed)", max_length=1000)
    budget = discord.ui.TextInput(label="Budget/Payment", placeholder="E.g., $50-100 or Revshare", max_length=100)
    deadline = discord.ui.TextInput(label="Deadline", placeholder="E.g., 3 days or 2024-12-31", required=False)
    reference = discord.ui.TextInput(label="Reference Examples", style=discord.TextStyle.long, placeholder="Links to examples/references (one per line)", required=False)

    def __init__(self, bot: commands.Bot, selected_roles: List[str] = None):
        super().__init__()
        self.bot = bot
        self.selected_roles = selected_roles or []

    async def on_submit(self, interaction: discord.Interaction):
        job_data = {
            "creator_id": interaction.user.id,
            "guild_id": interaction.guild.id if interaction.guild else None,
            "title": self.title_input.value,
            "description": self.description.value,
            "budget": self.budget.value,
            "software_required": "",  # Software can be included in description
            "deadline": self.deadline.value,
            "reference_links": self.reference.value,
        }
        
        job_id = create_job(DB_PATH, job_data)
        
        # Post to jobs channel
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        if cfg and cfg.get("jobs_channel_id"):
            channel = interaction.guild.get_channel(int(cfg.get("jobs_channel_id")))
            if channel:
                embed = self.build_job_embed(interaction.user, job_data, job_id)
                view = JobActionView(job_id)
                
                # Build ping message with selected roles
                ping_content = ""
                if self.selected_roles:
                    role_mentions = []
                    for role_name in self.selected_roles:
                        # Try to find the role by name
                        role = discord.utils.get(interaction.guild.roles, name=role_name)
                        if role:
                            role_mentions.append(role.mention)
                        else:
                            # If not found by name, try case-insensitive search
                            role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), interaction.guild.roles)
                            if role:
                                role_mentions.append(role.mention)
                            # If still not found, just use the name as text (not ideal but better than failing)
                            else:
                                role_mentions.append(f"@{role_name}")
                    if role_mentions:
                        ping_content = " ".join(role_mentions) + "\n"
                
                msg = await channel.send(content=ping_content, embed=embed, view=view)
                # Update job with message_id
                job_data["message_id"] = str(msg.id)
        
        # Award XP
        xp_result = add_xp(DB_PATH, str(interaction.user.id), 30)
        
        await interaction.response.send_message(f"✅ Job posted successfully! +30 XP\nJob ID: `{job_id}`", ephemeral=True)

    def build_job_embed(self, creator: discord.User, job_data: dict, job_id: str) -> discord.Embed:
        embed = discord.Embed(
            title=f"💼 {job_data['title']}",
            description=job_data['description'],
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=creator.display_name, icon_url=creator.display_avatar.url)
        embed.add_field(name="💰 Budget", value=job_data['budget'], inline=True)
        if job_data.get('software_required'):
            embed.add_field(name="🛠️ Software", value=job_data['software_required'], inline=True)
        if job_data.get('deadline'):
            embed.add_field(name="⏰ Deadline", value=job_data['deadline'], inline=True)
        if job_data.get('reference_links'):
            ref_links = job_data['reference_links'][:500]  # Limit length
            embed.add_field(name="📎 Reference Examples", value=ref_links, inline=False)
        embed.set_footer(text=f"Job ID: {job_id} • Click Apply to submit application")
        return embed


class ApplicationModal(discord.ui.Modal, title="Submit Application"):
    message = discord.ui.TextInput(label="Cover Message", style=discord.TextStyle.long, placeholder="Why you're the best fit...", max_length=500)
    portfolio = discord.ui.TextInput(label="Portfolio Links", placeholder="One URL per line", required=False)

    def __init__(self, job_id: str):
        super().__init__()
        self.job_id = job_id

    async def on_submit(self, interaction: discord.Interaction):
        links = [l.strip() for l in self.portfolio.value.split("\n") if l.strip()]
        
        app_data = {
            "job_id": self.job_id,
            "applicant_id": interaction.user.id,
            "message": self.message.value,
            "portfolio_links": links
        }
        
        app_id = create_application(DB_PATH, app_data)
        
        # Award XP
        add_xp(DB_PATH, str(interaction.user.id), 20)
        
        # Notify job creator
        job = get_job(DB_PATH, self.job_id)
        if job:
            creator = await interaction.client.fetch_user(int(job['creator_id']))
            if creator:
                notify_embed = discord.Embed(
                    title="📬 New Application Received",
                    description=f"**Job:** {job['title']}\n**Applicant:** {interaction.user.mention}\n\n**Message:**\n{self.message.value}",
                    color=discord.Color.blue()
                )
                if links:
                    notify_embed.add_field(name="Portfolio", value="\n".join(links[:5]))
                view = ApplicationResponseView(app_id, self.job_id, interaction.user.id)
                try:
                    await creator.send(embed=notify_embed, view=view)
                except:
                    pass
        
        await interaction.response.send_message("✅ Application submitted successfully! +20 XP", ephemeral=True)


class JobActionView(discord.ui.View):
    def __init__(self, job_id: str):
        super().__init__(timeout=None)
        self.job_id = job_id

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.primary, emoji="📝", custom_id="apply_job")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if job is still open
        job = get_job(DB_PATH, self.job_id)
        if job and job['status'] != 'open':
            await interaction.response.send_message("❌ This job is no longer accepting applications.", ephemeral=True)
            return
        
        # Check max applicants
        apps = get_job_applications(DB_PATH, self.job_id)
        if len(apps) >= 10:
            await interaction.response.send_message("❌ This job has reached the maximum of 10 applicants.", ephemeral=True)
            return
        
        await interaction.response.send_modal(ApplicationModal(self.job_id))

    @discord.ui.button(label="View Details", style=discord.ButtonStyle.secondary, emoji="ℹ️", custom_id="view_job_details")
    async def details_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        job = get_job(DB_PATH, self.job_id)
        if job:
            embed = discord.Embed(
                title=f"Job Details: {job['title']}",
                description=f"**Description:**\n{job['description']}\n\n**Budget:** {job['budget']}\n**Status:** {job['status']}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


class ApplicationResponseView(discord.ui.View):
    def __init__(self, app_id: str, job_id: str, applicant_id: int):
        super().__init__(timeout=None)
        self.app_id = app_id
        self.job_id = job_id
        self.applicant_id = applicant_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_app")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            update_application_status(DB_PATH, self.app_id, "accepted")
            update_job_status(DB_PATH, self.job_id, "in_progress", str(self.applicant_id))

            # Notify both parties with contact buttons
            applicant = await interaction.client.fetch_user(self.applicant_id)
            job = get_job(DB_PATH, self.job_id)
            if applicant and job:
                creator = await interaction.client.fetch_user(int(job['creator_id']))
                if creator:
                    # DM to applicant
                    embed_app = discord.Embed(title="🎉 Application Accepted!", description=f"Your application for **{job['title']}** was accepted!", color=discord.Color.green())
                    view_app = ContactView(creator, "Contact Client")
                    try:
                        await applicant.send(embed=embed_app, view=view_app)
                    except Exception as e:
                        print(f"Failed to send DM to applicant: {e}")

                    # DM to creator
                    embed_creator = discord.Embed(title="✅ Job Filled!", description=f"Your job **{job['title']}** has been accepted by {applicant.mention}!", color=discord.Color.green())
                    view_creator = ContactView(applicant, "Contact Editor")
                    try:
                        await creator.send(embed=embed_creator, view=view_creator)
                    except Exception as e:
                        print(f"Failed to send DM to creator: {e}")

            # Award bonus XP
            add_xp(DB_PATH, str(self.applicant_id), 50)
            award_achievement(DB_PATH, str(self.applicant_id), "first_job_accepted")

            # Disable buttons after selection
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(content="✅ Application accepted!", view=self)
        except Exception as e:
            # Check if this is an interaction expiry error
            error_str = str(e)
            if "10062" in error_str or "Unknown interaction" in error_str:
                # Interaction has expired, but still process the accept logic
                print(f"Interaction expired, but processing accept logic anyway: {e}")
                # The accept logic has already been executed above, so we're done
                return
            else:
                # Some other error occurred
                print(f"Error accepting application: {e}")
                # If we haven't responded yet, send a response. If we have, try to edit.
                try:
                    await interaction.response.send_message("❌ An error occurred while accepting the application. Please try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send("❌ An error occurred while accepting the application. Please try again.", ephemeral=True)
                    except:
                        pass

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reject_app")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        update_application_status(DB_PATH, self.app_id, "rejected")
        
        # Notify applicant
        applicant = await interaction.client.fetch_user(self.applicant_id)
        job = get_job(DB_PATH, self.job_id)
        if applicant and job:
            try:
                await applicant.send(f"Thank you for applying to **{job['title']}**. Unfortunately, your application was not selected this time.")
            except:
                pass
        
        # Disable buttons after selection
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Application rejected.", view=self)


class JobFeedbackModal(discord.ui.Modal, title="Job Completion Feedback"):
    job_experience = discord.ui.TextInput(
        label="How did the job go?",
        style=discord.TextStyle.long,
        placeholder="Tell us about your experience with this job...",
        max_length=500
    )
    bot_issues = discord.ui.TextInput(
        label="Any problems using the bot?",
        style=discord.TextStyle.long,
        placeholder="Did you encounter any issues or bugs?",
        required=False,
        max_length=500
    )
    reports = discord.ui.TextInput(
        label="Any reports or concerns?",
        style=discord.TextStyle.long,
        placeholder="Anything you'd like to report?",
        required=False,
        max_length=500
    )
    missing_features = discord.ui.TextInput(
        label="What's missing in the bot?",
        style=discord.TextStyle.long,
        placeholder="Features or improvements you'd like to see...",
        required=False,
        max_length=500
    )

    def __init__(self, job_id: str, job_title: str):
        super().__init__()
        self.job_id = job_id
        self.job_title = job_title

    async def on_submit(self, interaction: discord.Interaction):
        # Send feedback to developer
        try:
            dev_user = await interaction.client.fetch_user(DEVELOPER_ID)
            feedback_embed = discord.Embed(
                title="📋 Job Completion Feedback",
                description=f"**Job:** {self.job_title}\n**Job ID:** `{self.job_id}`\n**User:** {interaction.user.mention} ({interaction.user.id})",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            feedback_embed.add_field(name="Job Experience", value=self.job_experience.value or "No response", inline=False)
            feedback_embed.add_field(name="Bot Issues", value=self.bot_issues.value or "No issues reported", inline=False)
            feedback_embed.add_field(name="Reports", value=self.reports.value or "No reports", inline=False)
            feedback_embed.add_field(name="Missing Features", value=self.missing_features.value or "No suggestions", inline=False)
            
            await dev_user.send(embed=feedback_embed)
        except:
            pass  # DM failed, but don't fail the whole operation
        
        await interaction.response.send_message(
            "✅ Thank you for your feedback! Your responses have been submitted to the developer.",
            ephemeral=True
        )


class ContactView(discord.ui.View):
    def __init__(self, other_user: discord.User, label: str):
        super().__init__(timeout=None)
        self.other_user = other_user
        self.label = label

    @discord.ui.button(label="Contact", style=discord.ButtonStyle.primary)
    async def contact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message(f"{self.label}: {self.other_user.mention}")
        except Exception as e:
            # If interaction response fails, try followup
            try:
                await interaction.followup.send(f"{self.label}: {self.other_user.mention}")
            except:
                # If that also fails, send directly to the channel
                try:
                    await interaction.channel.send(f"{self.label}: {self.other_user.mention}")
                except:
                    pass  # Last resort - do nothing if all methods fail


class JobsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="create_job", description="Create a new job posting")
    async def create_job_cmd(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
            
        # Get available job roles from config
        cfg = get_config(DB_PATH, str(interaction.guild.id)) if interaction.guild else None
        available_roles = []
        
        if cfg and cfg.get("available_job_roles"):
            try:
                import json
                available_roles = json.loads(cfg.get("available_job_roles", "[]"))
            except:
                available_roles = []
        
        # If roles are configured, show selection view first
        if available_roles:
            view = RoleSelectionView(self.bot, interaction.guild.id, available_roles)
            await interaction.response.send_message(
                "📋 **Step 1:** Select which roles to ping for this job\n**Step 2:** Click 'Continue to Job Form' to fill out the job details",
                view=view,
                ephemeral=True
            )
        else:
            # No roles configured, go straight to modal
            await interaction.response.send_modal(JobCreationModal(self.bot))

    @app_commands.command(name="my_jobs", description="View your posted jobs")
    async def my_jobs(self, interaction: discord.Interaction):
        jobs = get_user_jobs(DB_PATH, str(interaction.user.id))
        if not jobs:
            await interaction.response.send_message("You haven't posted any jobs yet.", ephemeral=True)
            return
        
        embed = discord.Embed(title="Your Jobs", color=discord.Color.blue())
        for job in jobs[:10]:
            embed.add_field(
                name=f"{job['title']} ({job['status']})",
                value=f"ID: `{job['job_id']}`\nBudget: {job['budget']}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="my_applications", description="View your job applications")
    async def my_applications(self, interaction: discord.Interaction):
        apps = get_user_applications(DB_PATH, str(interaction.user.id))
        if not apps:
            await interaction.response.send_message("You haven't applied to any jobs yet.", ephemeral=True)
            return
        
        embed = discord.Embed(title="Your Applications", color=discord.Color.blue())
        for app in apps[:10]:
            job = get_job(DB_PATH, app['job_id'])
            if job:
                embed.add_field(
                    name=f"{job['title']} - {app['status']}",
                    value=f"Applied <t:{app['applied_at']}:R>",
                    inline=False
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="close_job", description="Close one of your jobs")
    @app_commands.describe(job_id="Job ID to close")
    async def close_job(self, interaction: discord.Interaction, job_id: str):
        job = get_job(DB_PATH, job_id)
        if not job:
            await interaction.response.send_message("❌ Job not found.", ephemeral=True)
            return
        
        # Check permissions: job creator, server admin, or developer
        is_creator = str(job['creator_id']) == str(interaction.user.id)
        is_admin = interaction.user.guild_permissions.manage_guild if interaction.guild else False
        is_developer = interaction.user.id == DEVELOPER_ID
        
        if not (is_creator or is_admin or is_developer):
            await interaction.response.send_message("❌ You can only close your own jobs. Only server admins and the developer can close other users' jobs.", ephemeral=True)
            return
        
        # Update job status to closed
        update_job_status(DB_PATH, job_id, "closed")
        
        # Update the job post message to disable the Apply button
        if job.get('message_id') and interaction.guild:
            cfg = get_config(DB_PATH, str(interaction.guild.id))
            if cfg and cfg.get("jobs_channel_id"):
                try:
                    channel = interaction.guild.get_channel(int(cfg.get("jobs_channel_id")))
                    if channel:
                        message = await channel.fetch_message(int(job['message_id']))
                        # Create disabled view
                        view = JobActionView(job_id)
                        for item in view.children:
                            item.disabled = True
                        
                        # Update embed to show closed status
                        if message.embeds:
                            embed = message.embeds[0]
                            embed.color = discord.Color.red()
                            embed.title = f"🔒 [CLOSED] {job['title']}"
                            await message.edit(embed=embed, view=view)
                except:
                    pass  # Message not found or can't edit
        
        await interaction.response.send_message("✅ Job closed successfully. Please fill out a quick feedback form!", ephemeral=True)
        
        # Send feedback modal to job creator via DM
        try:
            creator = await interaction.client.fetch_user(int(job['creator_id']))
            feedback_embed = discord.Embed(
                title="📝 Job Closed - Feedback Requested",
                description=f"Your job **{job['title']}** (ID: `{job_id}`) has been closed.\n\nPlease help us improve by filling out this feedback form:",
                color=discord.Color.blue()
            )
            
            # Create a view with a button to trigger the modal
            class FeedbackView(discord.ui.View):
                def __init__(self, job_id, job_title):
                    super().__init__(timeout=None)
                    self.job_id = job_id
                    self.job_title = job_title
                
                @discord.ui.button(label="Fill Feedback Form", style=discord.ButtonStyle.primary, emoji="📋")
                async def feedback_button(self, inter: discord.Interaction, button: discord.ui.Button):
                    await inter.response.send_modal(JobFeedbackModal(self.job_id, self.job_title))
            
            await creator.send(embed=feedback_embed, view=FeedbackView(job_id, job['title']))
        except:
            pass  # DM failed


async def setup(bot: commands.Bot):
    await bot.add_cog(JobsCog(bot))
