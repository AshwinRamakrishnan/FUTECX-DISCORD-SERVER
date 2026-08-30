import discord
from discord.ext import commands
from discord import app_commands
from backend.db.database import SessionLocal
from backend.services.user_service import get_or_create_user
from backend.services.xp_service import award_xp
import logging

logger = logging.getLogger(__name__)

class Onboarding(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        logger.info(f"New member joined: {member.name}")
        
        # In a real setup, we'd send a welcome message to a specific channel
        # or DM them, and perhaps assign a "New Member" role.
        # Let's auto-register them in the DB for now.
        db = SessionLocal()
        try:
            user = get_or_create_user(db, str(member.id), member.name)
            
            # Award starter XP if they are level 1 and have 0 XP
            if user.profile.xp == 0:
                award_xp(db, user.id, 10, "Welcome Bonus")
                
            logger.info(f"Registered FUTECX ID: {user.futecx_id} for {member.name}")
        except Exception as e:
            logger.error(f"Error onboarding member {member.name}: {e}")
        finally:
            db.close()

    @app_commands.command(name="register", description="Register for a FUTECX Profile if you haven't automatically.")
    async def register_profile(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            user = get_or_create_user(db, str(interaction.user.id), interaction.user.name)
            await interaction.response.send_message(f"Welcome to FUTECX! Your unique ID is **{user.futecx_id}**.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error registering: {e}", ephemeral=True)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(Onboarding(bot))
