import discord
from discord.ext import commands
from discord import app_commands

def is_staff():
    """Check if the user has a staff role or administrator permission"""
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
            
        staff_roles = ["Founder / CEO", "CTO", "COO", "Product Lead", "Engineering Lead", "Community Lead", "Community Manager"]
        user_roles = [role.name for role in interaction.user.roles]
        
        return any(role in user_roles for role in staff_roles)
    return app_commands.check(predicate)

def is_reviewer():
    """Check if the user has permission to review tasks"""
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
            
        reviewer_roles = ["Founder / CEO", "CTO", "COO", "Product Lead", "Engineering Lead", "Senior Engineer"]
        user_roles = [role.name for role in interaction.user.roles]
        
        return any(role in user_roles for role in reviewer_roles)
    return app_commands.check(predicate)
