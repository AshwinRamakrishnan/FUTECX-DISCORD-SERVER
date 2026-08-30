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
        
        channels_by_name = {}
        for ch in guild.text_channels:
            name = ch.name
            if name not in channels_by_name:
                channels_by_name[name] = []
            channels_by_name[name].append(ch)
            
        print("| Resource | Name | Category | Status | Action |")
        print("|---|---|---|---|---|")
        
        for name, channels in channels_by_name.items():
            if len(channels) > 1:
                categorized = [c for c in channels if c.category is not None]
                uncategorized = [c for c in channels if c.category is None]
                
                if categorized:
                    duplicates = uncategorized + categorized[1:]
                else:
                    duplicates = channels[1:]
                    
                for dup in duplicates:
                    cat_name = dup.category.name if dup.category else 'ROOT'
                    
                    try:
                        messages = [m async for m in dup.history(limit=5)]
                    except discord.Forbidden:
                        messages = []
                        
                    if len(messages) == 0:
                        print(f"| Text Channel | {dup.name} | {cat_name} | Empty Duplicate | DELETED |")
                        await dup.delete(reason="Duplicate cleanup")
                    else:
                        print(f"| Text Channel | {dup.name} | {cat_name} | Has {len(messages)} msgs | MANUAL REVIEW |")

        # Cleanup duplicate categories
        categories_by_name = {}
        for cat in guild.categories:
            name = cat.name
            if name not in categories_by_name:
                categories_by_name[name] = []
            categories_by_name[name].append(cat)
            
        for name, cats in categories_by_name.items():
            if len(cats) > 1:
                duplicates = cats[1:]
                for dup in duplicates:
                    if len(dup.channels) == 0:
                        print(f"| Category | {dup.name} | N/A | Empty Duplicate | DELETED |")
                        await dup.delete(reason="Duplicate cleanup")
                    else:
                        print(f"| Category | {dup.name} | N/A | Has {len(dup.channels)} channels | MANUAL REVIEW |")

        # Cleanup duplicate roles
        roles_by_name = {}
        for r in guild.roles:
            name = r.name
            if name not in roles_by_name:
                roles_by_name[name] = []
            roles_by_name[name].append(r)
            
        for name, roles in roles_by_name.items():
            if len(roles) > 1:
                duplicates = roles[1:]
                for dup in duplicates:
                    if len(dup.members) == 0:
                        print(f"| Role | {dup.name} | N/A | Empty Duplicate | DELETED |")
                        try:
                            await dup.delete(reason="Duplicate cleanup")
                        except Exception as e:
                            print(f"| Role | {dup.name} | N/A | Error Deleting | {e} |")
                    else:
                        print(f"| Role | {dup.name} | N/A | Has {len(dup.members)} members | MANUAL REVIEW |")
                        
        print("Cleanup execution complete.")
        await self.close()

intents = discord.Intents.default()
intents.message_content = True
client = CleanupClient(intents=intents)
client.run(TOKEN)
