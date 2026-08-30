import asyncio
import discord
import os
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

class CleanupClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(GUILD_ID)
        
        channels_by_name = {}
        for ch in guild.text_channels:
            name = ch.name
            if name not in channels_by_name:
                channels_by_name[name] = []
            channels_by_name[name].append(ch)
            
        print("DUPLICATE CHANNELS REPORT")
        print("| Resource | Name | Category | Status | Action |")
        print("|---|---|---|---|---|")
        
        for name, channels in channels_by_name.items():
            if len(channels) > 1:
                categorized = [c for c in channels if c.category is not None]
                uncategorized = [c for c in channels if c.category is None]
                
                if categorized:
                    canonical = categorized[0]
                    duplicates = uncategorized + categorized[1:]
                else:
                    canonical = channels[0]
                    duplicates = channels[1:]
                    
                for dup in duplicates:
                    cat_name = dup.category.name if dup.category else 'ROOT'
                    print(f"| Text Channel | {dup.name} | {cat_name} | Duplicate | MANUALLY REVIEW/DELETE |")
        
        categories_by_name = {}
        for cat in guild.categories:
            name = cat.name
            if name not in categories_by_name:
                categories_by_name[name] = []
            categories_by_name[name].append(cat)
            
        for name, cats in categories_by_name.items():
            if len(cats) > 1:
                canonical = cats[0]
                duplicates = cats[1:]
                for dup in duplicates:
                    print(f"| Category | {dup.name} | N/A | Duplicate | MANUALLY REVIEW/DELETE |")
                    
        roles_by_name = {}
        for r in guild.roles:
            name = r.name
            if name not in roles_by_name:
                roles_by_name[name] = []
            roles_by_name[name].append(r)
            
        for name, roles in roles_by_name.items():
            if len(roles) > 1:
                canonical = roles[0]
                duplicates = roles[1:]
                for dup in duplicates:
                    print(f"| Role | {dup.name} | N/A | Duplicate | MANUALLY REVIEW/DELETE |")
                    
        print(f"Total Categories: {len(guild.categories)}")
        print(f"Total Text Channels: {len(guild.text_channels)}")
        print(f"Total Roles: {len(guild.roles)}")
        
        print("Inspection complete. Closing.")
        await self.close()

intents = discord.Intents.default()
intents.message_content = True
client = CleanupClient(intents=intents)
client.run(TOKEN)
