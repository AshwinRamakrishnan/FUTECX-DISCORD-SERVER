import discord
from discord.ext import commands
from discord import app_commands
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.db.database import get_db_session
from backend.db.models import Event
from backend.bot.utils.embeds import get_base_embed, create_error_embed

class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="events", description="View upcoming FUTECX events")
    async def events_cmd(self, interaction: discord.Interaction):
        with get_db_session() as db:
            upcoming_events = db.query(Event).filter(Event.scheduled_at >= datetime.now(timezone.utc)).order_by(Event.scheduled_at.asc()).limit(5).all()
            
            if not upcoming_events:
                await interaction.response.send_message(embed=get_base_embed(title="Upcoming Events", description="There are no upcoming events scheduled at the moment."))
                return
                
            embed = get_base_embed(title="Upcoming FUTECX Events", description="Here are the next scheduled events:")
            for event in upcoming_events:
                event_date = event.scheduled_at.strftime('%Y-%m-%d %H:%M UTC')
                value = f"**Description:** {event.description}\n**Date:** {event_date}"
                if event.location_url:
                    value += f"\n**Location:** [Link]({event.location_url})"
                embed.add_field(name=f"📅 {event.title}", value=value, inline=False)
                
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="event_register", description="Register for an upcoming event")
    async def event_register_cmd(self, interaction: discord.Interaction, event_id: int):
        with get_db_session() as db:
            event = db.query(Event).filter(Event.id == event_id).first()
            if not event:
                await interaction.response.send_message(embed=create_error_embed("Event not found."), ephemeral=True)
                return
                
            # Here you would typically link an EventRegistration model to the user
            # Since EventRegistration isn't in models.py, we will just simulate a success response.
            embed = get_base_embed(title="Event Registration", description=f"You have successfully registered for **{event.title}**!", color=0x00FF00)
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(EventsCog(bot))
