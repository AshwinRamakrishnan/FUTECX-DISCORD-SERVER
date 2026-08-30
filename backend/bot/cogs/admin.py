import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.db.database import get_db_session
from backend.db.models import User, Profile, XPTransaction, Certificate, Event, Achievement, UserAchievement
from backend.bot.utils.embeds import get_base_embed, create_error_embed, create_success_embed, create_xp_award_embed, create_certificate_embed
from backend.bot.utils.permissions import is_staff, is_reviewer

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="admin", description="Admin: General admin testing command")
    @is_staff()
    async def admin_cmd(self, interaction: discord.Interaction):
        await interaction.response.send_message("Admin command executed successfully. You have staff permissions.", ephemeral=True)

    @app_commands.command(name="xp_add", description="Admin: Add XP to a member")
    @is_staff()
    async def xp_add_cmd(self, interaction: discord.Interaction, member: discord.Member, amount: int, reason: str):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("User does not have a FUTECX profile."), ephemeral=True)
                return
            
            user.profile.xp += amount
            
            # Level calculation logic
            new_level = max(1, user.profile.xp // 100 + 1)
            if new_level > user.profile.level:
                user.profile.level = new_level
                
            tx = XPTransaction(user_id=user.id, amount=amount, source=reason)
            db.add(tx)
            db.commit()
            db.refresh(user.profile)
            
            embed = create_xp_award_embed(user.profile.username, amount, reason, user.profile.xp)
            
            # Try to send to xp-alerts channel
            xp_channel = discord.utils.get(interaction.guild.text_channels, name="xp-alerts")
            if xp_channel:
                await xp_channel.send(embed=embed)
                await interaction.response.send_message("XP added and announced.", ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="xp_remove", description="Admin: Remove XP from a member")
    @is_staff()
    async def xp_remove_cmd(self, interaction: discord.Interaction, member: discord.Member, amount: int, reason: str):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not user or not user.profile:
                await interaction.response.send_message(embed=create_error_embed("User does not have a FUTECX profile."), ephemeral=True)
                return
            
            user.profile.xp -= amount
            if user.profile.xp < 0:
                user.profile.xp = 0
                
            new_level = max(1, user.profile.xp // 100 + 1)
            user.profile.level = new_level
                
            tx = XPTransaction(user_id=user.id, amount=-amount, source=f"Deduction: {reason}")
            db.add(tx)
            db.commit()
            
            await interaction.response.send_message(embed=create_success_embed("XP Deducted", f"Deducted {amount} XP from {user.profile.username}."), ephemeral=True)

    @app_commands.command(name="badge_grant", description="Admin: Grant an achievement badge to a member")
    @is_staff()
    async def badge_grant_cmd(self, interaction: discord.Interaction, member: discord.Member, badge_name: str, icon: str = "🏆"):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("User not found."), ephemeral=True)
                return
                
            achievement = db.query(Achievement).filter(Achievement.name == badge_name).first()
            if not achievement:
                achievement = Achievement(name=badge_name, description=f"Manually granted badge: {badge_name}", icon=icon, condition="manual")
                db.add(achievement)
                db.commit()
                db.refresh(achievement)
                
            existing = db.query(UserAchievement).filter(UserAchievement.user_id == user.id, UserAchievement.achievement_id == achievement.id).first()
            if existing:
                await interaction.response.send_message(embed=create_error_embed("User already has this badge."), ephemeral=True)
                return
                
            ua = UserAchievement(user_id=user.id, achievement_id=achievement.id)
            db.add(ua)
            db.commit()
            
            embed = get_base_embed(title="Achievement Unlocked!", description=f"**{user.profile.username}** has been granted a new badge!")
            embed.add_field(name=f"{icon} {badge_name}", value="Congratulations!", inline=False)
            
            channel = discord.utils.get(interaction.guild.text_channels, name="achievements")
            if channel:
                await channel.send(member.mention, embed=embed)
                await interaction.response.send_message(f"Badge granted in {channel.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="certificate_issue", description="Admin: Issue a certificate")
    @is_staff()
    async def certificate_issue_cmd(self, interaction: discord.Interaction, member: discord.Member, title: str, achievement_text: str):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("User not found."), ephemeral=True)
                return
                
            cert_id_str = f"FUTECX-CERT-{datetime.now(timezone.utc).year}-{str(user.id).zfill(4)}-{str(int(datetime.now(timezone.utc).timestamp()))[-4:]}"
            
            cert = Certificate(
                cert_id=cert_id_str,
                user_id=user.id,
                title=title,
                achievement_text=achievement_text
            )
            db.add(cert)
            db.commit()
            db.refresh(cert)
            
            embed = create_certificate_embed(user.profile.username, cert_id_str, title)
            
            channel = discord.utils.get(interaction.guild.text_channels, name="certificate-gallery")
            if channel:
                await channel.send(member.mention, embed=embed)
                await interaction.response.send_message(f"Certificate issued in {channel.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="certificate_revoke", description="Admin: Revoke a certificate")
    @is_staff()
    async def certificate_revoke_cmd(self, interaction: discord.Interaction, cert_id: str):
        with get_db_session() as db:
            cert = db.query(Certificate).filter(Certificate.cert_id == cert_id).first()
            if not cert:
                await interaction.response.send_message(embed=create_error_embed("Certificate not found."), ephemeral=True)
                return
                
            cert.is_revoked = True
            db.commit()
            
            await interaction.response.send_message(embed=create_success_embed("Certificate Revoked", f"Certificate `{cert_id}` has been successfully revoked."), ephemeral=True)

    @app_commands.command(name="event_create", description="Admin: Create a new event")
    @is_staff()
    async def event_create_cmd(self, interaction: discord.Interaction, title: str, description: str, date_yyyy_mm_dd: str, time_hh_mm: str, location_url: str = None):
        try:
            dt_str = f"{date_yyyy_mm_dd} {time_hh_mm}"
            scheduled_at = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            await interaction.response.send_message(embed=create_error_embed("Invalid date/time format. Use YYYY-MM-DD and HH:MM"), ephemeral=True)
            return

        with get_db_session() as db:
            event = Event(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                location_url=location_url
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            
            embed = get_base_embed(title="New FUTECX Event Scheduled!", description=description)
            embed.add_field(name="Event", value=title, inline=True)
            embed.add_field(name="Date", value=dt_str, inline=True)
            if location_url:
                embed.add_field(name="Location", value=f"[Link]({location_url})", inline=False)
            
            channel = discord.utils.get(interaction.guild.text_channels, name="event-announcements")
            if channel:
                await channel.send("@everyone", embed=embed)
                await interaction.response.send_message(f"Event published in {channel.mention}", ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="announcement", description="Admin: Post an official announcement")
    @is_staff()
    async def announcement_cmd(self, interaction: discord.Interaction, title: str, message: str, channel_name: str = "announcements"):
        channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if not channel:
            await interaction.response.send_message(embed=create_error_embed(f"Channel #{channel_name} not found."), ephemeral=True)
            return
            
        embed = get_base_embed(title=title, description=message)
        await channel.send(embed=embed)
        await interaction.response.send_message(f"Announcement sent to {channel.mention}", ephemeral=True)

    @app_commands.command(name="member_inspect", description="Admin: Inspect a member's full database record")
    @is_staff()
    async def member_inspect_cmd(self, interaction: discord.Interaction, member: discord.Member):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(member.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("User not found in DB."), ephemeral=True)
                return
                
            embed = get_base_embed(title=f"Member Inspection: {member.name}", description="Internal DB Record")
            embed.add_field(name="DB ID", value=str(user.id), inline=True)
            embed.add_field(name="FUTECX ID", value=user.futecx_id, inline=True)
            if user.profile:
                embed.add_field(name="XP", value=str(user.profile.xp), inline=True)
                embed.add_field(name="Level", value=str(user.profile.level), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
