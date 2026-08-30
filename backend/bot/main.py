import discord
from discord.ext import commands
import logging
from backend.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('futecx-bot')

class FutecxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        import os
        # Load cogs
        cogs = [
            "backend.bot.cogs.setup",
            "backend.bot.cogs.core",
            "backend.bot.cogs.admin",
            "backend.bot.cogs.events",
            "backend.bot.cogs.certificates",
            "backend.bot.cogs.onboarding",
            "backend.bot.cogs.profile",
            "backend.bot.cogs.tasks",
            "backend.bot.cogs.projects",
            "backend.bot.cogs.leaderboard"
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded extension {cog}")
            except Exception:
                logger.exception(f"Failed to load extension {cog}")
                
        # Sync slash commands
        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} slash commands to guild {guild_id}.")
        else:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands globally.")
            
        for cmd in synced:
            logger.info(f"Synced command: {cmd.name}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        logger.info("FUTECX Bot is ready.")

async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    logger.error(f"Command Error ({interaction.command.name}): {str(error)}")
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
    elif isinstance(error, discord.app_commands.CheckFailure):
        await interaction.response.send_message("You do not have the required role or permissions for this command.", ephemeral=True)
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message("An unexpected error occurred while processing this command.", ephemeral=True)

def run_bot():
    if not settings.discord_token:
        logger.warning("No DISCORD_TOKEN found. Bot cannot start.")
        return
    bot = FutecxBot()
    bot.tree.on_error = on_app_command_error
    bot.run(settings.discord_token)

if __name__ == "__main__":
    run_bot()
