import discord
from datetime import datetime

# FUTECX Branding Colors
COLOR_PRIMARY = 0x00FFCC # Cyan/Teal tech vibe
COLOR_SUCCESS = 0x00FF00
COLOR_ERROR = 0xFF0000
COLOR_WARNING = 0xFFA500
COLOR_INFO = 0x3498DB
COLOR_DARK = 0x2C2F33

def get_base_embed(title: str, description: str, color: int = COLOR_PRIMARY) -> discord.Embed:
    embed = discord.Embed(
        title=f"🚀 {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="FUTECX Infrastructure", icon_url="https://ui-avatars.com/api/?name=FUTECX&background=00FFCC&color=000")
    return embed

def create_welcome_embed(member_name: str) -> discord.Embed:
    embed = get_base_embed(
        title="Welcome to FUTECX",
        description=f"Welcome {member_name} to the Future Technology Community ecosystem! We focus on Software Engineering, AI, Open Source, and Collaborative Projects."
    )
    embed.add_field(name="Next Steps", value="Please complete the onboarding verification below to gain access to the server.", inline=False)
    return embed

def create_daily_task_embed(title: str, description: str, difficulty: str, xp: int) -> discord.Embed:
    embed = get_base_embed(
        title=f"Daily Task: {title}",
        description=description,
        color=COLOR_INFO
    )
    embed.add_field(name="Difficulty", value=difficulty, inline=True)
    embed.add_field(name="XP Reward", value=f"{xp} XP", inline=True)
    embed.add_field(name="How to submit", value="Use `/submit_task` with your evidence url.", inline=False)
    return embed

def create_xp_award_embed(member_name: str, xp_amount: int, reason: str, total_xp: int = None) -> discord.Embed:
    embed = get_base_embed(
        title="XP Awarded",
        description=f"**{member_name}** earned **{xp_amount} XP**!",
        color=COLOR_SUCCESS
    )
    embed.add_field(name="Reason", value=reason, inline=False)
    if total_xp is not None:
        embed.add_field(name="Total XP", value=str(total_xp), inline=True)
    return embed

def create_achievement_embed(member_name: str, achievement_name: str, icon: str = "🏆") -> discord.Embed:
    embed = get_base_embed(
        title="Achievement Unlocked!",
        description=f"**{member_name}** has unlocked a new achievement!",
        color=COLOR_PRIMARY
    )
    embed.add_field(name=f"{icon} {achievement_name}", value="Congratulations!", inline=False)
    return embed

def create_project_showcase_embed(project_name: str, description: str, status: str, repo_url: str = None) -> discord.Embed:
    embed = get_base_embed(
        title=f"Project: {project_name}",
        description=description,
        color=COLOR_INFO
    )
    embed.add_field(name="Status", value=status, inline=True)
    if repo_url:
        embed.add_field(name="Repository", value=f"[GitHub Link]({repo_url})", inline=False)
    return embed

def create_error_embed(message: str) -> discord.Embed:
    return get_base_embed(
        title="Error",
        description=message,
        color=COLOR_ERROR
    ).set_footer(text="FUTECX System Error")

def create_success_embed(title: str, message: str) -> discord.Embed:
    return get_base_embed(
        title=title,
        description=message,
        color=COLOR_SUCCESS
    )

def create_certificate_embed(member_name: str, cert_id: str, title: str) -> discord.Embed:
    embed = get_base_embed(
        title="Certificate Issued",
        description=f"A new official FUTECX Certificate has been issued to **{member_name}**.",
        color=COLOR_PRIMARY
    )
    embed.add_field(name="Title", value=title, inline=False)
    embed.add_field(name="Certificate ID", value=cert_id, inline=True)
    embed.add_field(name="Verify", value=f"Use `/certificate verify {cert_id}` to verify authenticity.", inline=False)
    return embed
