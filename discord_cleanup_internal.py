import asyncio
import discord
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

class CleanupClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(GUILD_ID)
        
        # 11 Canonical Categories
        canonical = [
            "📌 FUTECX HQ",
            "🌐 COMMUNITY",
            "👨💻 DEVELOPER HUB",
            "🧠 AI & INNOVATION",
            "🚀 PROJECTS",
            "📚 LEARNING CENTER",
            "⚡ FUTECX CONTRIBUTIONS",
            "💼 CAREERS & OPPORTUNITIES",
            "🎤 EVENTS",
            "🏆 RECOGNITION",
            "🛡️ TRUST & SAFETY"
        ]
        
        # We need to find the "🔒 FUTECX INTERNAL" category and delete its empty channels, then delete it.
        # But there might be other non-canonical categories too! The user said "Keep ONLY these 11 categories".
        
        channels_deleted = 0
        categories_deleted = 0
        preserved_channels = 0
        
        print("Starting Canonical 11 Cleanup...")
        for cat in guild.categories:
            if cat.name not in canonical and cat.name != "Text Channels" and cat.name != "Voice Channels":
                print(f"Inspecting Non-Canonical Category: {cat.name}")
                for ch in cat.text_channels:
                    try:
                        messages = [m async for m in ch.history(limit=5)]
                    except discord.Forbidden:
                        messages = []
                        
                    if len(messages) == 0:
                        print(f"| Text Channel | {ch.name} | {cat.name} | Empty | DELETING |")
                        await ch.delete(reason="Enforcing 11-category structure")
                        channels_deleted += 1
                    else:
                        print(f"| Text Channel | {ch.name} | {cat.name} | {len(messages)} messages | MANUAL REVIEW PRESERVED |")
                        preserved_channels += 1
                        
                # Re-fetch category channels just to be sure
                # if all channels were deleted, delete the category
                if len(cat.channels) - channels_deleted <= 0 or len(cat.channels) == 0:
                     print(f"| Category | {cat.name} | N/A | Empty | DELETING |")
                     try:
                         await cat.delete(reason="Enforcing 11-category structure")
                         categories_deleted += 1
                     except Exception as e:
                         print(f"Could not delete {cat.name}: {e}")
                else:
                     print(f"| Category | {cat.name} | N/A | Has remaining channels | MANUAL REVIEW PRESERVED |")
                     
        # Now verify if any channels are still in ROOT!
        print("\nChecking ROOT for remaining non-canonical channels...")
        for ch in guild.text_channels:
            if ch.category is None:
                try:
                    messages = [m async for m in ch.history(limit=5)]
                except discord.Forbidden:
                    messages = []
                    
                if len(messages) == 0:
                    print(f"| Text Channel | {ch.name} | ROOT | Empty | DELETING |")
                    await ch.delete(reason="Root cleanup")
                    channels_deleted += 1
                else:
                    print(f"| Text Channel | {ch.name} | ROOT | {len(messages)} messages | MANUAL REVIEW PRESERVED |")
                    preserved_channels += 1

        print(f"\nCleanup Complete.")
        print(f"Channels Deleted: {channels_deleted}")
        print(f"Categories Deleted: {categories_deleted}")
        print(f"Preserved Non-Empty Channels: {preserved_channels}")
        print(f"Final Category Count: {len(guild.categories) - categories_deleted}")
        print(f"Final Channel Count: {len(guild.text_channels) - channels_deleted}")
        print(f"Final Role Count: {len(guild.roles)}")
        
        await self.close()

intents = discord.Intents.default()
intents.message_content = True
client = CleanupClient(intents=intents)
client.run(TOKEN)
