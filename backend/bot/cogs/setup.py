import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Dict, List

from backend.bot.utils.permissions import is_staff
from backend.bot.utils.embeds import create_success_embed, get_base_embed

logger = logging.getLogger('futecx-setup')

def normalize(name: str):
    return name.lower().strip()

def normalize_channel(name: str):
    return name.lower().strip().replace(" ", "-")

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.REQUIRED_ROLES = {
            "Leadership": ["Founder / CEO", "CTO", "COO", "Product Lead", "Engineering Lead"],
            "Engineering": ["Senior Engineer", "Developer", "AI Engineer", "ML Engineer", "Cloud Engineer", "DevOps Engineer", "Frontend Engineer", "Backend Engineer", "Full Stack Engineer", "QA Engineer", "Security Engineer"],
            "Community": ["Community Lead", "Community Manager", "Moderator", "Mentor", "Event Coordinator"],
            "Contribution": ["Core Contributor", "Contributor", "Builder", "Project Lead", "Project Member", "Verified Member", "Community Member", "New Member"],
            "Recognition": ["Top Contributor", "AI Specialist", "Code Master", "Creative Builder", "Community Mentor", "Project Champion", "Innovation Leader", "FUTECX Vanguard"],
            "Bot": ["FUTECX Bot", "FUTECX Automation", "FUTECX Moderation"]
        }

        self.REQUIRED_CATEGORIES = {
            "📌 FUTECX HQ": ["announcements", "company-updates", "product-releases", "security-updates", "privacy-updates", "events", "rules-and-guidelines"],
            "🌐 COMMUNITY": ["welcome", "general", "lobby", "introductions", "networking", "ideas", "help", "community-showcase", "community-moments"],
            "👨💻 DEVELOPER HUB": ["dev-general", "python", "javascript", "web-development", "artificial-intelligence", "machine-learning", "cloud", "databases", "devops", "mobile-development", "open-source", "tools-and-resources"],
            "🧠 AI & INNOVATION": ["ai-discussion", "generative-ai", "ai-agents", "rag-and-llm", "voice-ai", "computer-vision", "ai-experiments", "innovation-lab"],
            "🚀 PROJECTS": ["project-board", "project-ideas", "find-a-team", "team-formation", "active-projects", "project-help", "testing", "releases", "project-showcase", "project-archive"],
            "📚 LEARNING CENTER": ["learning-hub", "learning-roadmaps", "resources", "study-room", "coding-challenges", "technical-discussions", "assignments", "certifications"],
            "⚡ FUTECX CONTRIBUTIONS": ["daily-tasks", "task-submissions", "task-review", "contribution-log", "xp-alerts", "achievements", "badges", "monthly-leaderboard", "yearly-leaderboard", "global-leaderboard", "hall-of-fame"],
            "💼 CAREERS & OPPORTUNITIES": ["jobs", "internships", "hackathons", "startup-opportunities", "open-roles", "collaboration", "career-resources"],
            "🎤 EVENTS": ["event-announcements", "tech-talks", "workshops", "coding-events", "hackathons", "recordings", "event-gallery"],
            "🏆 RECOGNITION": ["member-of-the-month", "contributor-of-the-month", "project-of-the-month", "top-developers", "achievement-wall", "certificate-gallery"],
            "🛡️ TRUST & SAFETY": ["community-policy", "privacy", "security-report", "report", "moderation-info", "safety-announcements"]
        }

    @app_commands.command(name="setup-server", description="Setup the FUTECX Server Architecture")
    @app_commands.default_permissions(manage_channels=True, manage_roles=True)
    async def setup_server(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        
        logger.info("[SETUP] Starting server setup")
        logger.info("[SETUP] Checking bot permissions")
        
        if not guild.me.guild_permissions.manage_roles or not guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(
                "FUTECX SERVER SETUP BLOCKED\n\nMissing permission:\nManage Roles and/or Manage Channels\n\nAction:\nServer Settings → Roles → Ensure the FUTECX Bot has Manage Roles and Manage Channels.",
                ephemeral=True
            )
            return

        roles_created = 0
        roles_reused = 0
        categories_created = 0
        categories_reused = 0
        channels_created = 0
        channels_reused = 0
        duplicates_detected = 0

        try:
            logger.info("[SETUP] Creating/reusing roles")
            # 1. Create Roles
            role_objects = {}
            for category, roles in self.REQUIRED_ROLES.items():
                for role_name in roles:
                    norm_role = normalize(role_name)
                    existing_roles = [r for r in guild.roles if normalize(r.name) == norm_role]
                    
                    if not existing_roles:
                        try:
                            new_role = await guild.create_role(name=role_name, reason="FUTECX Architecture Setup")
                            role_objects[role_name] = new_role
                            roles_created += 1
                            logger.info(f"[SETUP] CREATED role: {role_name}")
                        except discord.Forbidden:
                            logger.error(f"[SETUP] Missing permissions to create role {role_name}. Bot role may be too low in hierarchy.")
                            await interaction.followup.send(
                                "FUTECX SERVER SETUP BLOCKED\n\nMissing permission:\nCannot create roles.\n\nAction:\nServer Settings → Roles → move FUTECX Bot above the FUTECX roles.",
                                ephemeral=True
                            )
                            return
                    else:
                        role_objects[role_name] = existing_roles[0] # Use the oldest/first one
                        roles_reused += 1
                        if len(existing_roles) > 1:
                            duplicates_detected += len(existing_roles) - 1
                        logger.info(f"[SETUP] REUSED role: {role_name}")

            logger.info("[SETUP] Applying permission overwrites")
            logger.info("[SETUP] Creating/reusing categories")
            # 3. Create Categories and Channels
            for cat_name, channels in self.REQUIRED_CATEGORIES.items():
                norm_cat = normalize(cat_name)
                existing_categories = [c for c in guild.categories if normalize(c.name) == norm_cat]
                
                overwrites = {}
                
                if not existing_categories:
                    try:
                        category = await guild.create_category(name=cat_name, overwrites=overwrites)
                        categories_created += 1
                        logger.info(f"[SETUP] CREATED category: {cat_name}")
                    except discord.Forbidden:
                        logger.error(f"[SETUP] Missing permissions to create category {cat_name}")
                        continue
                else:
                    category = existing_categories[0]
                    categories_reused += 1
                    if len(existing_categories) > 1:
                        duplicates_detected += len(existing_categories) - 1
                    logger.info(f"[SETUP] REUSED category: {cat_name}")

                logger.info(f"[SETUP] Creating/reusing channels for {cat_name}")
                for channel_name in channels:
                    norm_chan = normalize_channel(channel_name)
                    # Search within the chosen category
                    existing_channels = [c for c in category.text_channels if normalize_channel(c.name) == norm_chan]
                    
                    if not existing_channels:
                        try:
                            await guild.create_text_channel(name=channel_name, category=category)
                            channels_created += 1
                            logger.info(f"[SETUP] CREATED channel: {channel_name}")
                        except discord.Forbidden:
                            logger.error(f"[SETUP] Missing permissions to create channel {channel_name}")
                    else:
                        channels_reused += 1
                        if len(existing_channels) > 1:
                            duplicates_detected += len(existing_channels) - 1
                        logger.info(f"[SETUP] REUSED channel: {channel_name}")

            logger.info("[SETUP] Setup completed")
            # Response
            response_text = (
                "**FUTECX SERVER SETUP COMPLETE**\n\n"
                f"**Roles:**\nCreated: {roles_created}\nReused: {roles_reused}\n\n"
                f"**Categories:**\nCreated: {categories_created}\nReused: {categories_reused}\n\n"
                f"**Channels:**\nCreated: {channels_created}\nReused: {channels_reused}\n\n"
            )
            
            if duplicates_detected > 0:
                response_text += f"**Duplicates Detected:** {duplicates_detected}\n"
                response_text += "*Cleanup required. Run `/setup-cleanup` to review or remove duplicates.*"
            else:
                response_text += "**Duplicates Detected:** 0\n*No cleanup required.*"
                
            await interaction.followup.send(response_text, ephemeral=True)

        except discord.Forbidden as e:
            logger.exception("Forbidden error during setup")
            await interaction.followup.send(f"FUTECX server setup failed: Missing permissions ({e})", ephemeral=True)
        except Exception as e:
            logger.exception("Unexpected error during setup")
            await interaction.followup.send(f"FUTECX server setup failed: An unexpected error occurred.", ephemeral=True)

    @app_commands.command(name="setup-cleanup", description="Admin: Clean up duplicate roles, categories, and channels created by setup")
    @app_commands.default_permissions(manage_channels=True, manage_roles=True)
    async def setup_cleanup(self, interaction: discord.Interaction, confirm: bool = False):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        
        roles_deleted = 0
        categories_deleted = 0
        channels_deleted = 0
        
        # 1. Deduplicate roles
        all_req_roles = []
        for rl in self.REQUIRED_ROLES.values():
            all_req_roles.extend(rl)
            
        for role_name in all_req_roles:
            norm_role = normalize(role_name)
            # Sort by created_at to keep the oldest one
            existing_roles = sorted([r for r in guild.roles if normalize(r.name) == norm_role], key=lambda r: r.created_at)
            if len(existing_roles) > 1:
                # Keep the first one, delete the rest
                for duplicate in existing_roles[1:]:
                    if confirm:
                        try:
                            await duplicate.delete(reason="FUTECX Setup Cleanup")
                            roles_deleted += 1
                        except discord.Forbidden:
                            pass
                    else:
                        roles_deleted += 1 # Just counting
                        
        # 2. Deduplicate categories
        for cat_name, channels in self.REQUIRED_CATEGORIES.items():
            norm_cat = normalize(cat_name)
            existing_categories = sorted([c for c in guild.categories if normalize(c.name) == norm_cat], key=lambda c: c.created_at)
            if len(existing_categories) > 1:
                for duplicate in existing_categories[1:]:
                    if confirm:
                        try:
                            # Before deleting a category, we might want to move its channels or delete them.
                            # For safety, we only delete empty categories, or delete them including channels if they are exact duplicates.
                            # But Discord API delete() on category just removes the category and orphans the channels.
                            await duplicate.delete(reason="FUTECX Setup Cleanup")
                            categories_deleted += 1
                        except discord.Forbidden:
                            pass
                    else:
                        categories_deleted += 1
            
            # 3. Deduplicate channels within the correct category
            if existing_categories:
                primary_category = existing_categories[0]
                for channel_name in channels:
                    norm_chan = normalize_channel(channel_name)
                    existing_channels = sorted([c for c in primary_category.text_channels if normalize_channel(c.name) == norm_chan], key=lambda c: c.created_at)
                    if len(existing_channels) > 1:
                        for duplicate in existing_channels[1:]:
                            if confirm:
                                try:
                                    await duplicate.delete(reason="FUTECX Setup Cleanup")
                                    channels_deleted += 1
                                except discord.Forbidden:
                                    pass
                            else:
                                channels_deleted += 1
                                
        if not confirm:
            msg = (
                "**FUTECX SETUP CLEANUP (DRY RUN)**\n\n"
                f"**Duplicates found:**\nRoles: {roles_deleted}\nCategories: {categories_deleted}\nChannels: {channels_deleted}\n\n"
                "Run `/setup-cleanup confirm:True` to actually delete these duplicate items."
            )
        else:
            msg = (
                "**FUTECX SETUP CLEANUP COMPLETE**\n\n"
                f"**Deleted duplicates:**\nRoles: {roles_deleted}\nCategories: {categories_deleted}\nChannels: {channels_deleted}"
            )
            
        await interaction.followup.send(msg, ephemeral=True)

    @app_commands.command(name="setup-onboarding", description="Setup the interactive onboarding flow in #welcome")
    @app_commands.default_permissions(manage_channels=True)
    async def setup_onboarding(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        welcome_channel = discord.utils.get(interaction.guild.text_channels, name="welcome")
        if not welcome_channel:
            welcome_channel = interaction.channel
            
        embed = get_base_embed(
            title="Welcome to FUTECX 🚀",
            description="FUTECX is a technology ecosystem focused on:\n\n"
                        "• Software Engineering\n"
                        "• Artificial Intelligence\n"
                        "• Innovation\n"
                        "• Open Source\n"
                        "• Projects\n"
                        "• Learning\n"
                        "• Collaboration\n\n"
                        "Please click the button below to verify and complete your profile."
        )
        
        class OnboardingView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
                
            @discord.ui.button(label="Verify & Join", style=discord.ButtonStyle.green, custom_id="verify_join_btn")
            async def verify_join(self, interaction_btn: discord.Interaction, button: discord.ui.Button):
                verified_role = discord.utils.get(interaction_btn.guild.roles, name="Verified Member")
                new_member_role = discord.utils.get(interaction_btn.guild.roles, name="New Member")
                
                if verified_role:
                    await interaction_btn.user.add_roles(verified_role)
                if new_member_role:
                    await interaction_btn.user.remove_roles(new_member_role)
                    
                await interaction_btn.response.send_message("Welcome to FUTECX! You are now a Verified Member. Use `/register` to create a profile.", ephemeral=True)

        try:
            await welcome_channel.send(embed=embed, view=OnboardingView())
            await interaction.followup.send("Onboarding flow created successfully.", ephemeral=True)
        except Exception as e:
            logger.exception("Failed to create onboarding flow")
            await interaction.followup.send(f"Failed to create onboarding flow: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
