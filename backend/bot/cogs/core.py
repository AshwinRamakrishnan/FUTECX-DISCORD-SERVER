import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.db.models import User, Profile, Achievement, UserAchievement
from backend.bot.utils.embeds import get_base_embed, create_error_embed

class CoreCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="View all FUTECX commands")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = get_base_embed(
            title="FUTECX Command Center",
            description="Here are the core commands you can use in the FUTECX ecosystem:"
        )
        embed.add_field(name="👤 Profile & Identity", value="`/profile` `/idcard` `/xp` `/rank` `/achievements` `/streak`", inline=False)
        embed.add_field(name="🚀 Projects", value="`/project create` `/project join` `/project status` `/team`", inline=False)
        embed.add_field(name="⚡ Contributions", value="`/tasks_today` `/submit_task` `/submissions` `/leaderboard`", inline=False)
        embed.add_field(name="🎓 Learning & Events", value="`/events` `/event register` `/resources`", inline=False)
        embed.add_field(name="🏆 Recognition", value="`/certificate` `/certificate verify`", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="achievements", description="View your unlocked achievements")
    async def achievements_cmd(self, interaction: discord.Interaction):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("You don't have a FUTECX profile yet. Use `/register`."), ephemeral=True)
                return

            user_achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user.id).all()
            
            if not user_achievements:
                embed = get_base_embed(title="Achievements", description="You haven't unlocked any achievements yet. Keep contributing!")
            else:
                embed = get_base_embed(title="Your Achievements", description=f"You have unlocked {len(user_achievements)} achievements!")
                for ua in user_achievements:
                    icon = ua.achievement.icon or "🏆"
                    embed.add_field(name=f"{icon} {ua.achievement.name}", value=ua.achievement.description, inline=False)
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="badges", description="Alias for /achievements")
    async def badges_cmd(self, interaction: discord.Interaction):
        await self.achievements_cmd(interaction)

    @app_commands.command(name="streak", description="View your current daily streak")
    async def streak_cmd(self, interaction: discord.Interaction):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("Profile not found."), ephemeral=True)
                return
            
            embed = get_base_embed(title="Daily Streak", description=f"🔥 Your current streak is **{user.profile.current_streak}** days!")
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resources", description="View FUTECX learning resources")
    async def resources_cmd(self, interaction: discord.Interaction):
        embed = get_base_embed(title="FUTECX Learning Resources", description="Access our curated list of technical resources.")
        embed.add_field(name="GitHub", value="[FUTECX GitHub](https://github.com/futecx)", inline=False)
        embed.add_field(name="Documentation", value="[FUTECX Docs](https://docs.futecx.com)", inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CoreCog(bot))
