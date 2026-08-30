import discord
from discord.ext import commands
from discord import app_commands
from backend.db.database import get_db_session
from backend.db.models import Task, TaskSubmission, User, Project
from backend.services.task_service import create_task, submit_task, review_submission
from backend.bot.utils.embeds import get_base_embed, create_error_embed, create_daily_task_embed, create_xp_award_embed
from backend.bot.utils.permissions import is_reviewer

class TasksCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="task_create", description="Admin: Create a new Daily Task")
    @app_commands.default_permissions(administrator=True)
    async def task_create(self, interaction: discord.Interaction, title: str, description: str, difficulty: str, category: str, xp_reward: int, project_name: str = None):
        with get_db_session() as db:
            try:
                project_id = None
                if project_name:
                    project = db.query(Project).filter(Project.name.ilike(project_name)).first()
                    if not project:
                        await interaction.response.send_message(embed=create_error_embed("Project not found."), ephemeral=True)
                        return
                    project_id = project.id

                task = create_task(db, title, description, difficulty, category, xp_reward, project_id)
                
                embed = create_daily_task_embed(title, description, difficulty, xp_reward)
                
                if project_id:
                    safe_name = project_name.lower().replace(" ", "-")
                    channel = discord.utils.get(interaction.guild.text_channels, name=f"{safe_name}-general")
                    if channel:
                        await channel.send(f"<@&{discord.utils.get(interaction.guild.roles, name=f'{project.name} Member').id}>", embed=embed)
                        await interaction.response.send_message(f"Task created successfully and announced in {channel.mention}!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Task created (ID: {task.id}), but project channel not found.", ephemeral=True)
                else:
                    channel = discord.utils.get(interaction.guild.text_channels, name="daily-tasks")
                    if channel:
                        await channel.send("@everyone", embed=embed)
                        await interaction.response.send_message(f"Task created successfully and announced in {channel.mention}!", ephemeral=True)
                    else:
                        await interaction.response.send_message(f"Task created successfully (ID: {task.id}), but `#daily-tasks` channel was not found.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(embed=create_error_embed(f"Error creating task: {e}"), ephemeral=True)

    @app_commands.command(name="tasks_today", description="View active tasks for today")
    async def tasks_today(self, interaction: discord.Interaction):
        with get_db_session() as db:
            active_tasks = db.query(Task).filter(Task.is_active == True).all()
            if not active_tasks:
                await interaction.response.send_message(embed=get_base_embed(title="Daily Tasks", description="No active tasks today. Check back later!"), ephemeral=True)
                return

            embed = get_base_embed(title="⚡ FUTECX DAILY TASKS", description="Active tasks available for contribution:")
            for t in active_tasks:
                embed.add_field(
                    name=f"Task #{t.id}: {t.title}",
                    value=f"**Category:** {t.category} | **Difficulty:** {t.difficulty} | **XP:** +{t.xp_reward}\n{t.description}",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="submit_task", description="Submit evidence for a task")
    async def submit_task_cmd(self, interaction: discord.Interaction, task_id: int, evidence_url: str, notes: str = ""):
        with get_db_session() as db:
            try:
                user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
                if not user:
                    await interaction.response.send_message(embed=create_error_embed("Please register using /register first."), ephemeral=True)
                    return
                    
                submission = submit_task(db, task_id, user.id, evidence_url, notes)
                
                channel = discord.utils.get(interaction.guild.text_channels, name="task-submissions")
                if channel:
                    admin_embed = get_base_embed(title="New Task Submission", description=f"Submission #{submission.id} pending review.")
                    admin_embed.add_field(name="User", value=interaction.user.mention, inline=True)
                    admin_embed.add_field(name="Task ID", value=str(task_id), inline=True)
                    admin_embed.add_field(name="Evidence", value=evidence_url, inline=False)
                    await channel.send(embed=admin_embed)
                    
                await interaction.response.send_message(embed=get_base_embed(title="Submission Received", description=f"Successfully submitted task #{task_id}! Status is now **Pending Review**.", color=0x00FF00), ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(embed=create_error_embed(f"Error submitting task: {e}"), ephemeral=True)

    @app_commands.command(name="submissions", description="View your task submissions")
    async def submissions_cmd(self, interaction: discord.Interaction):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("Profile not found."), ephemeral=True)
                return
                
            subs = db.query(TaskSubmission).filter(TaskSubmission.user_id == user.id).order_by(TaskSubmission.created_at.desc()).limit(5).all()
            if not subs:
                await interaction.response.send_message(embed=get_base_embed(title="Submissions", description="You have not submitted any tasks yet."), ephemeral=True)
                return
                
            embed = get_base_embed(title="Recent Submissions", description="Your last 5 submissions:")
            for s in subs:
                status_icon = "✅" if s.status == "APPROVED" else "❌" if s.status == "REJECTED" else "⏳"
                embed.add_field(name=f"Sub #{s.id} | Task #{s.task_id}", value=f"Status: {status_icon} {s.status}\nSubmitted: {s.created_at.strftime('%Y-%m-%d')}", inline=False)
                
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="submission_review", description="Admin/Reviewer: Approve or reject a submission")
    @is_reviewer()
    @app_commands.choices(status=[
        app_commands.Choice(name="APPROVED", value="APPROVED"),
        app_commands.Choice(name="REJECTED", value="REJECTED")
    ])
    async def submission_review_cmd(self, interaction: discord.Interaction, submission_id: int, status: str, reviewer_notes: str = ""):
        with get_db_session() as db:
            try:
                admin = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
                if not admin:
                    await interaction.response.send_message(embed=create_error_embed("Admin user not found in DB."), ephemeral=True)
                    return
                    
                sub = review_submission(db, submission_id, admin.id, status, reviewer_notes)
                
                await interaction.response.send_message(embed=get_base_embed(title="Submission Reviewed", description=f"Submission #{submission_id} has been marked as **{status}**.", color=0x00FF00 if status == "APPROVED" else 0xFF0000), ephemeral=True)
                
                if status == "APPROVED":
                    user = db.query(User).filter(User.id == sub.user_id).first()
                    embed = create_xp_award_embed(user.profile.username, sub.task.xp_reward, f"Task Approved: {sub.task.title}", user.profile.xp)
                    
                    channel = discord.utils.get(interaction.guild.text_channels, name="xp-alerts")
                    if channel:
                        await channel.send(f"<@{user.discord_id}>", embed=embed)
            except Exception as e:
                await interaction.response.send_message(embed=create_error_embed(f"Error reviewing submission: {e}"), ephemeral=True)

async def setup(bot):
    await bot.add_cog(TasksCog(bot))
