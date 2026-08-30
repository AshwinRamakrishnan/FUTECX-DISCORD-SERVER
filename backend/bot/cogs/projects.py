import discord
from discord.ext import commands
from discord import app_commands
from backend.db.database import get_db_session
from backend.db.models import Project, ProjectMember, User, ProjectJoinRequest, AuditLog
from backend.bot.utils.embeds import get_base_embed, create_error_embed, create_project_showcase_embed
from datetime import datetime, timezone

class ProjectsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    project_group = app_commands.Group(name="project", description="Manage FUTECX projects")

    @project_group.command(name="create", description="Create a new project workspace")
    async def create_project(self, interaction: discord.Interaction, name: str, description: str):
        # 1. DB Check
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("Please register using /register first."), ephemeral=True)
                return

            existing = db.query(Project).filter(Project.name.ilike(name)).first()
            if existing:
                await interaction.response.send_message(embed=create_error_embed("A project with that name already exists."), ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)

            # 2. Discord Creation - Find the "🚀 PROJECTS" category
            guild = interaction.guild
            category = discord.utils.get(guild.categories, name="🚀 PROJECTS")
            if not category:
                # Fallback just in case
                category = await guild.create_category("🚀 PROJECTS")

            # Create Roles
            lead_role_name = f"{name} Lead"
            member_role_name = f"{name} Member"

            lead_role = discord.utils.get(guild.roles, name=lead_role_name)
            if not lead_role:
                lead_role = await guild.create_role(name=lead_role_name, reason=f"Created for Project {name}")

            member_role = discord.utils.get(guild.roles, name=member_role_name)
            if not member_role:
                member_role = await guild.create_role(name=member_role_name, reason=f"Created for Project {name}")

            # Assign Lead role to the creator
            try:
                await interaction.user.add_roles(lead_role)
                await interaction.user.add_roles(member_role)
            except discord.Forbidden:
                pass

            # Create private channels under "🚀 PROJECTS"
            safe_name = name.lower().replace(" ", "-")

            # Overwrites: Everyone blocked. Members can see. Leads can manage.
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                lead_role: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_messages=True),
                guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
            }

            general_channel = discord.utils.get(category.channels, name=f"{safe_name}-general")
            if not general_channel:
                general_channel = await guild.create_text_channel(
                    name=f"{safe_name}-general",
                    category=category,
                    overwrites=overwrites
                )

            dev_channel = discord.utils.get(category.channels, name=f"{safe_name}-dev")
            if not dev_channel:
                dev_channel = await guild.create_text_channel(
                    name=f"{safe_name}-dev",
                    category=category,
                    overwrites=overwrites
                )

            # 3. DB Save
            project = Project(name=name, description=description, status="IDEA")
            db.add(project)
            db.flush()
            
            member = ProjectMember(project_id=project.id, user_id=user.id, role="Lead", status="APPROVED")
            db.add(member)

            audit = AuditLog(actor_id=user.id, project_id=project.id, action="PROJECT_CREATED", details=f"Created project {name}")
            db.add(audit)
            db.commit()

            embed = create_project_showcase_embed(name, description, "IDEA")
            
            # Announce in project-board if it exists
            board = discord.utils.get(guild.text_channels, name="project-board")
            if board:
                await board.send(embed=embed)
                await interaction.followup.send(f"Project created! Workspace: {general_channel.mention}\nAnnounced in {board.mention}.")
            else:
                await interaction.followup.send(f"Project created! Workspace: {general_channel.mention}", embed=embed)

    @project_group.command(name="join", description="Request to join a project")
    async def join_project(self, interaction: discord.Interaction, project_name: str):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("Please register using /register first."), ephemeral=True)
                return
                
            project = db.query(Project).filter(Project.name.ilike(project_name)).first()
            if not project:
                await interaction.response.send_message(embed=create_error_embed("Project not found."), ephemeral=True)
                return
                
            # Check existing membership
            existing_member = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id, ProjectMember.status == "APPROVED").first()
            if existing_member:
                await interaction.response.send_message(embed=create_error_embed("You are already an approved member of this project."), ephemeral=True)
                return

            # Check existing request
            existing_req = db.query(ProjectJoinRequest).filter(ProjectJoinRequest.project_id == project.id, ProjectJoinRequest.user_id == user.id, ProjectJoinRequest.status == "PENDING").first()
            if existing_req:
                await interaction.response.send_message(embed=create_error_embed("You already have a pending join request."), ephemeral=True)
                return
                
            req = ProjectJoinRequest(project_id=project.id, user_id=user.id)
            db.add(req)
            
            audit = AuditLog(actor_id=user.id, project_id=project.id, action="PROJECT_JOIN_REQUESTED")
            db.add(audit)
            db.commit()
            
            await interaction.response.send_message(embed=get_base_embed(title="Join Request Sent", description=f"Your request to join **{project.name}** has been sent to the Project Leads."), ephemeral=True)

    @project_group.command(name="approve", description="Approve a user's join request")
    async def approve_user(self, interaction: discord.Interaction, project_name: str, member: discord.Member):
        await self._process_join_request(interaction, project_name, member, True)

    @project_group.command(name="reject", description="Reject a user's join request")
    async def reject_user(self, interaction: discord.Interaction, project_name: str, member: discord.Member):
        await self._process_join_request(interaction, project_name, member, False)

    async def _process_join_request(self, interaction: discord.Interaction, project_name: str, member: discord.Member, approve: bool):
        with get_db_session() as db:
            admin_user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            target_user = db.query(User).filter(User.discord_id == str(member.id)).first()
            
            if not admin_user or not target_user:
                await interaction.response.send_message("Users must be registered.", ephemeral=True)
                return

            project = db.query(Project).filter(Project.name.ilike(project_name)).first()
            if not project:
                await interaction.response.send_message("Project not found.", ephemeral=True)
                return

            # Check if actor is Lead
            is_lead = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == admin_user.id, ProjectMember.role == "Lead", ProjectMember.status == "APPROVED").first()
            
            # Allow FUTECX Admins to bypass
            is_admin = interaction.user.guild_permissions.administrator
            
            if not is_lead and not is_admin:
                await interaction.response.send_message("You must be a Project Lead to manage members.", ephemeral=True)
                return

            req = db.query(ProjectJoinRequest).filter(ProjectJoinRequest.project_id == project.id, ProjectJoinRequest.user_id == target_user.id, ProjectJoinRequest.status == "PENDING").first()
            if not req:
                await interaction.response.send_message("No pending request found for this user.", ephemeral=True)
                return

            if approve:
                req.status = "APPROVED"
                req.reviewed_at = datetime.now(timezone.utc)
                req.reviewed_by = admin_user.id

                proj_mem = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == target_user.id).first()
                if proj_mem:
                    proj_mem.status = "APPROVED"
                    proj_mem.joined_at = datetime.now(timezone.utc)
                    proj_mem.removed_at = None
                else:
                    proj_mem = ProjectMember(project_id=project.id, user_id=target_user.id, role="Member", status="APPROVED")
                    db.add(proj_mem)

                # Discord Role
                member_role_name = f"{project.name} Member"
                role = discord.utils.get(interaction.guild.roles, name=member_role_name)
                if role:
                    try:
                        await member.add_roles(role)
                    except Exception:
                        pass
                
                action = "PROJECT_JOIN_APPROVED"
                msg = f"Approved {member.display_name} for **{project.name}**."
            else:
                req.status = "REJECTED"
                req.reviewed_at = datetime.now(timezone.utc)
                req.reviewed_by = admin_user.id
                action = "PROJECT_JOIN_REJECTED"
                msg = f"Rejected {member.display_name} for **{project.name}**."

            audit = AuditLog(actor_id=admin_user.id, target_id=target_user.id, project_id=project.id, action=action)
            db.add(audit)
            db.commit()

            await interaction.response.send_message(embed=get_base_embed(title="Member Review", description=msg), ephemeral=True)
            try:
                await member.send(f"Your request to join {project.name} was {'approved' if approve else 'rejected'}.")
            except:
                pass

    @project_group.command(name="leave", description="Leave a project")
    async def leave_project(self, interaction: discord.Interaction, project_name: str):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message("Please register.", ephemeral=True)
                return
                
            project = db.query(Project).filter(Project.name.ilike(project_name)).first()
            if not project:
                await interaction.response.send_message("Project not found.", ephemeral=True)
                return

            mem = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id, ProjectMember.status == "APPROVED").first()
            if not mem:
                await interaction.response.send_message("You are not an active member.", ephemeral=True)
                return

            mem.status = "REMOVED"
            mem.removed_at = datetime.now(timezone.utc)
            
            audit = AuditLog(actor_id=user.id, project_id=project.id, action="PROJECT_LEFT")
            db.add(audit)
            db.commit()

            # Discord Role
            role = discord.utils.get(interaction.guild.roles, name=f"{project.name} Member")
            lead_role = discord.utils.get(interaction.guild.roles, name=f"{project.name} Lead")
            try:
                if role: await interaction.user.remove_roles(role)
                if lead_role: await interaction.user.remove_roles(lead_role)
            except Exception:
                pass

            await interaction.response.send_message(f"You have left **{project.name}**. Historical data has been preserved.", ephemeral=True)

    @project_group.command(name="remove", description="Remove a user from a project")
    async def remove_user(self, interaction: discord.Interaction, project_name: str, member: discord.Member):
        with get_db_session() as db:
            admin_user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            target_user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not admin_user or not target_user:
                await interaction.response.send_message("Users must be registered.", ephemeral=True)
                return
                
            project = db.query(Project).filter(Project.name.ilike(project_name)).first()
            if not project:
                await interaction.response.send_message("Project not found.", ephemeral=True)
                return

            is_lead = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == admin_user.id, ProjectMember.role == "Lead", ProjectMember.status == "APPROVED").first()
            is_admin = interaction.user.guild_permissions.administrator
            if not is_lead and not is_admin:
                await interaction.response.send_message("You must be a Project Lead to manage members.", ephemeral=True)
                return

            mem = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == target_user.id, ProjectMember.status == "APPROVED").first()
            if not mem:
                await interaction.response.send_message("Target user is not an active member.", ephemeral=True)
                return

            mem.status = "REMOVED"
            mem.removed_at = datetime.now(timezone.utc)
            
            audit = AuditLog(actor_id=admin_user.id, target_id=target_user.id, project_id=project.id, action="PROJECT_MEMBER_REMOVED")
            db.add(audit)
            db.commit()

            # Discord Role
            role = discord.utils.get(interaction.guild.roles, name=f"{project.name} Member")
            lead_role = discord.utils.get(interaction.guild.roles, name=f"{project.name} Lead")
            try:
                if role: await member.remove_roles(role)
                if lead_role: await member.remove_roles(lead_role)
            except Exception:
                pass

            await interaction.response.send_message(f"Removed {member.display_name} from **{project.name}**.", ephemeral=True)


    @project_group.command(name="members", description="View active project members")
    async def view_team(self, interaction: discord.Interaction, project_name: str):
        with get_db_session() as db:
            project = db.query(Project).filter(Project.name.ilike(project_name)).first()
            if not project:
                await interaction.response.send_message(embed=create_error_embed("Project not found."), ephemeral=True)
                return
                
            # Verify if caller is member or admin (prevent unauthorized access)
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            is_admin = interaction.user.guild_permissions.administrator
            is_member = False
            if user:
                is_member = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id, ProjectMember.status == "APPROVED").first()
            
            if not is_member and not is_admin:
                await interaction.response.send_message(embed=create_error_embed("You must be a member of this project to view its roster."), ephemeral=True)
                return
                
            members = db.query(ProjectMember).filter(ProjectMember.project_id == project.id, ProjectMember.status == "APPROVED").all()
            
            embed = get_base_embed(title=f"Team: {project.name}", description=f"Active members:")
            for m in members:
                username = m.user.profile.username if m.user.profile else "Unknown"
                embed.add_field(name=m.role, value=f"{username}\n(Joined: {m.joined_at.strftime('%Y-%m-%d')})", inline=True)
                
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @project_group.command(name="list", description="List active projects")
    async def list_projects(self, interaction: discord.Interaction):
        with get_db_session() as db:
            projects = db.query(Project).limit(10).all()
            if not projects:
                await interaction.response.send_message(embed=create_error_embed("No active projects found."), ephemeral=True)
                return
                
            embed = get_base_embed(title="FUTECX Projects", description="Latest projects:")
            for p in projects:
                embed.add_field(
                    name=f"#{p.id} - {p.name} [{p.status}]",
                    value=p.description[:100] + "..." if len(p.description) > 100 else p.description,
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProjectsCog(bot))
