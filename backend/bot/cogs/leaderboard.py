import discord
from discord.ext import commands
from discord import app_commands
from backend.db.database import SessionLocal
from backend.db.models import Profile, User

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="View the FUTECX XP Leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            top_profiles = db.query(Profile).order_by(Profile.xp.desc()).limit(10).all()
            if not top_profiles:
                await interaction.response.send_message("The leaderboard is currently empty.", ephemeral=True)
                return

            embed = discord.Embed(title="🏆 FUTECX XP Leaderboard", color=discord.Color.gold())
            
            for index, profile in enumerate(top_profiles, start=1):
                # Optionally fetch user to show FUTECX ID if desired, but we have username
                medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else "🏅"
                embed.add_field(
                    name=f"{medal} #{index} - {profile.username}",
                    value=f"**Level:** {profile.level} | **XP:** {profile.xp}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error fetching leaderboard: {e}", ephemeral=True)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))
