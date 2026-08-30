import asyncio
import discord
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(GUILD_ID)
        
        data = {
            "categories": [],
            "text_channels": [],
            "voice_channels": [],
            "roles": []
        }
        
        for cat in guild.categories:
            data["categories"].append({"id": cat.id, "name": cat.name, "position": cat.position})
            
        for ch in guild.text_channels:
            data["text_channels"].append({
                "id": ch.id, 
                "name": ch.name, 
                "category_id": ch.category.id if ch.category else None,
                "category_name": ch.category.name if ch.category else None,
                "position": ch.position
            })
            
        for role in guild.roles:
            data["roles"].append({"id": role.id, "name": role.name})
            
        with open("guild_dump.json", "w") as f:
            json.dump(data, f, indent=2)
            
        print("Dump complete. Closing.")
        await self.close()

intents = discord.Intents.default()
client = MyClient(intents=intents)
client.run(TOKEN)
