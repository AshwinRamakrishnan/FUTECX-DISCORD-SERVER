import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.db.models import Certificate, User
from backend.bot.utils.embeds import get_base_embed, create_error_embed

class CertificatesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="certificate", description="View your issued certificates")
    async def certificate_cmd(self, interaction: discord.Interaction):
        with get_db_session() as db:
            user = db.query(User).filter(User.discord_id == str(interaction.user.id)).first()
            if not user:
                await interaction.response.send_message(embed=create_error_embed("You don't have a FUTECX profile."), ephemeral=True)
                return

            certs = db.query(Certificate).filter(Certificate.user_id == user.id, Certificate.is_revoked == False).all()
            
            if not certs:
                await interaction.response.send_message(embed=get_base_embed(title="Certificates", description="You have not been issued any certificates yet."))
                return

            embed = get_base_embed(title="Your FUTECX Certificates", description=f"You have {len(certs)} active certificates:")
            for cert in certs:
                embed.add_field(
                    name=cert.title,
                    value=f"**ID:** `{cert.cert_id}`\n**Achievement:** {cert.achievement_text}\n**Issued:** {cert.issued_at.strftime('%Y-%m-%d')}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="certificate_verify", description="Verify a FUTECX Certificate by ID")
    async def certificate_verify_cmd(self, interaction: discord.Interaction, cert_id: str):
        with get_db_session() as db:
            cert = db.query(Certificate).filter(Certificate.cert_id == cert_id).first()
            
            if not cert:
                await interaction.response.send_message(embed=create_error_embed("Certificate not found or invalid."), ephemeral=True)
                return
                
            if cert.is_revoked:
                embed = get_base_embed(title="Certificate Verification", description="This certificate has been **REVOKED** and is no longer valid.", color=0xFF0000)
                await interaction.response.send_message(embed=embed)
                return
                
            embed = get_base_embed(title="Certificate Verification", description="✅ This is a **VALID** FUTECX Certificate.", color=0x00FF00)
            embed.add_field(name="Issued To", value=cert.user.profile.username, inline=True)
            embed.add_field(name="Certificate ID", value=cert.cert_id, inline=True)
            embed.add_field(name="Title", value=cert.title, inline=False)
            embed.add_field(name="Achievement", value=cert.achievement_text, inline=False)
            embed.add_field(name="Date Issued", value=cert.issued_at.strftime('%Y-%m-%d'), inline=True)
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CertificatesCog(bot))
