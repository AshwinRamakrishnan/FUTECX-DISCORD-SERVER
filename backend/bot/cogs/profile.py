import discord
from discord.ext import commands
from discord import app_commands
from backend.db.database import SessionLocal
from backend.services.user_service import get_user_by_discord_id
from backend.core.config import settings
from backend.bot.utils.embeds import get_base_embed, create_error_embed
import qrcode
import io

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="profile", description="View your FUTECX Member Profile")
    async def view_profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        
        db = SessionLocal()
        try:
            user = get_user_by_discord_id(db, str(target.id))
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed(f"{target.name} does not have a FUTECX profile yet."), ephemeral=True)
                return

            embed = get_base_embed(title="FUTECX PROFILE", description="Official Member Record")
            embed.set_author(name=target.display_name, icon_url=target.display_avatar.url if target.display_avatar else None)
            
            embed.add_field(name="FUTECX ID", value=f"`{user.futecx_id}`", inline=False)
            embed.add_field(name="Level", value=f"{user.profile.level}", inline=True)
            embed.add_field(name="XP", value=f"{user.profile.xp}", inline=True)
            embed.add_field(name="Current Streak", value=f"{user.profile.current_streak} days", inline=True)
            
            embed.set_footer(text=f"Joined: {user.created_at.strftime('%B %Y')}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(embed=create_error_embed(f"Error loading profile: {e}"), ephemeral=True)
        finally:
            db.close()

    @app_commands.command(name="idcard", description="View your official FUTECX Digital ID Card")
    async def view_idcard(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            user = get_user_by_discord_id(db, str(interaction.user.id))
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("You don't have a FUTECX profile yet. Use `/register`."), ephemeral=True)
                return

            verification_url = f"{settings.public_base_url}/api/verify/member/{user.futecx_id}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            with io.BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                file = discord.File(fp=image_binary, filename='qrcode.png')

                embed = get_base_embed(
                    title="FUTECX OFFICIAL ID CARD",
                    description="This is an official verification card.",
                    color=0x2C2F33
                )
                
                embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None)
                embed.add_field(name="FUTECX ID", value=f"`{user.futecx_id}`", inline=False)
                embed.add_field(name="Status", value="✅ VERIFIED", inline=True)
                embed.add_field(name="Level", value=f"{user.profile.level}", inline=True)
                embed.add_field(name="XP", value=f"{user.profile.xp}", inline=True)
                
                project_count = len(user.projects) if user.projects else 0
                embed.add_field(name="Projects", value=f"{project_count}", inline=True)
                
                embed.set_image(url="attachment://qrcode.png")
                embed.set_footer(text="Scan QR to verify identity online.")
                
                await interaction.response.send_message(embed=embed, file=file)
                
        except Exception as e:
            await interaction.response.send_message(embed=create_error_embed(f"Error generating ID card: {e}"), ephemeral=True)
        finally:
            db.close()

    @app_commands.command(name="xp", description="Check your current XP balance")
    async def view_xp(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            user = get_user_by_discord_id(db, str(interaction.user.id))
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("Profile not found."), ephemeral=True)
                return
            
            embed = get_base_embed(title="XP Balance", description=f"You currently have **{user.profile.xp} XP** (Level {user.profile.level}).")
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()

    @app_commands.command(name="rank", description="Check your current rank on the leaderboard")
    async def view_rank(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            user = get_user_by_discord_id(db, str(interaction.user.id))
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("Profile not found."), ephemeral=True)
                return
                
            from backend.db.models import Profile as DBProfile
            higher_xp_count = db.query(DBProfile).filter(DBProfile.xp > user.profile.xp).count()
            rank = higher_xp_count + 1
            
            embed = get_base_embed(title="Current Rank", description=f"You are currently rank **#{rank}** on the global leaderboard with **{user.profile.xp} XP**.")
            await interaction.response.send_message(embed=embed)
        finally:
            db.close()

async def setup(bot):
    await bot.add_cog(Profile(bot))
