import asyncio
import discord
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

def normalize(name):
    return name.lower().strip()

def normalize_channel(name):
    return name.lower().replace(" ", "-").strip()

REQUIRED_CATEGORIES = {
    "📌 FUTECX HQ": ["announcements", "company-updates", "product-releases", "security-updates", "privacy-updates", "events", "rules-and-guidelines"],
    "🌐 COMMUNITY": ["welcome", "general", "lobby", "introductions", "networking", "ideas", "help", "community-showcase", "community-moments"],
    "👨💻 DEVELOPER HUB": ["dev-general", "python", "javascript", "web-development", "artificial-intelligence", "machine-learning", "cloud", "databases", "devops", "mobile-development", "open-source", "tools-and-resources"],
    "🧠 AI & INNOVATION": ["ai-discussion", "generative-ai", "ai-agents", "rag-and-llm", "voice-ai", "computer-vision", "ai-experiments", "innovation-lab"],
    "🚀 PROJECTS": ["project-board", "project-ideas", "find-a-team", "team-formation", "active-projects", "project-help", "testing", "releases", "project-showcase", "project-archive"],
    "📚 LEARNING CENTER": ["learning-hub", "learning-roadmaps", "resources", "study-room", "coding-challenges", "technical-discussions", "assignments", "certifications"],
    "⚡ FUTECX CONTRIBUTIONS": ["daily-tasks", "task-submissions", "task-review", "contribution-log", "xp-alerts", "achievements", "badges", "monthly-leaderboard", "yearly-leaderboard", "global-leaderboard", "hall-of-fame"],
    "💼 CAREERS & OPPORTUNITIES": ["jobs", "internships", "hackathons", "startup-opportunities", "open-roles", "collaboration", "career-resources"],
    "🎤 EVENTS": ["event-announcements", "tech-talks", "workshops", "coding-events", "hackathons", "recordings", "event-gallery"],
    "🏆 RECOGNITION": ["member-of-the-month", "contributor-of-the-month", "project-of-the-month", "top-developers", "achievement-wall", "certificate-gallery"],
    "🛡️ TRUST & SAFETY": ["community-policy", "privacy", "security-report", "report", "moderation-info", "safety-announcements"]
}

REQUIRED_ROLES = [
    # Staff
    {"name": "Founder / CEO", "color": 0xFFD700, "hoist": True},
    {"name": "CTO", "color": 0xFF8C00, "hoist": True},
    {"name": "COO", "color": 0xFF8C00, "hoist": True},
    {"name": "Product Lead", "color": 0xFF4500, "hoist": True},
    {"name": "Engineering Lead", "color": 0xFF4500, "hoist": True},
    {"name": "Community Manager", "color": 0x32CD32, "hoist": True},
    {"name": "Moderator", "color": 0x00FF00, "hoist": True},
    
    # Ranks
    {"name": "Tech Titan", "color": 0x8A2BE2, "hoist": True},
    {"name": "Code Wizard", "color": 0x9370DB, "hoist": True},
    {"name": "Senior Developer", "color": 0x1E90FF, "hoist": False},
    {"name": "Developer", "color": 0x00BFFF, "hoist": False},
    {"name": "Junior Developer", "color": 0x87CEEB, "hoist": False},
    {"name": "Tech Enthusiast", "color": 0x00FFFF, "hoist": False},
    {"name": "Newbie", "color": 0xA9A9A9, "hoist": False},
    
    # Specialties
    {"name": "AI Engineer", "color": 0xFF69B4, "hoist": False},
    {"name": "Frontend Dev", "color": 0xFF1493, "hoist": False},
    {"name": "Backend Dev", "color": 0xC71585, "hoist": False},
    {"name": "Fullstack Dev", "color": 0xDB7093, "hoist": False},
    {"name": "DevOps", "color": 0xFF00FF, "hoist": False},
    {"name": "Data Scientist", "color": 0x8B008B, "hoist": False},
    {"name": "UI/UX Designer", "color": 0x9400D3, "hoist": False},
    {"name": "Mobile Dev", "color": 0x9932CC, "hoist": False},
    {"name": "Cybersecurity", "color": 0x4B0082, "hoist": False},
    
    # Achievements / Status
    {"name": "Project Maintainer", "color": 0x00FA9A, "hoist": False},
    {"name": "Top Contributor", "color": 0x00FF7F, "hoist": False},
    {"name": "Event Speaker", "color": 0x3CB371, "hoist": False},
    {"name": "Hackathon Winner", "color": 0x2E8B57, "hoist": False},
    {"name": "Bug Hunter", "color": 0x228B22, "hoist": False},
    {"name": "Verified", "color": 0x008000, "hoist": False},
    {"name": "Beta Tester", "color": 0x556B2F, "hoist": False},
    {"name": "Contributor", "color": 0x6B8E23, "hoist": False},
    {"name": "Mentor", "color": 0x808000, "hoist": True},
    {"name": "Mentee", "color": 0xBDB76B, "hoist": False},
    
    # External / Integrations
    {"name": "GitHub Verified", "color": 0x708090, "hoist": False},
    {"name": "Server Booster", "color": 0xFF69B4, "hoist": True},
    {"name": "FUTECX Bot", "color": 0x5865F2, "hoist": True}
]

class SetupClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        guild = self.get_guild(GUILD_ID)
        
        for run_num in range(1, 4):
            print(f"\n--- RUN {run_num} ---")
            roles_created, roles_reused = 0, 0
            categories_created, categories_reused = 0, 0
            channels_created, channels_reused = 0, 0
            
            # Roles
            role_objects = {}
            for role_data in REQUIRED_ROLES:
                role_name = role_data["name"]
                norm_role = normalize(role_name)
                existing_roles = [r for r in guild.roles if normalize(r.name) == norm_role]
                if not existing_roles:
                    try:
                        new_role = await guild.create_role(name=role_name, reason="FUTECX Architecture Setup")
                        role_objects[role_name] = new_role
                        roles_created += 1
                    except discord.Forbidden:
                        pass
                else:
                    role_objects[role_name] = existing_roles[0]
                    roles_reused += 1

            # Categories & Channels
            for cat_name, channels in REQUIRED_CATEGORIES.items():
                norm_cat = normalize(cat_name)
                existing_categories = [c for c in guild.categories if normalize(c.name) == norm_cat]
                
                overwrites = {}
                
                if not existing_categories:
                    try:
                        category = await guild.create_category(name=cat_name, overwrites=overwrites)
                        categories_created += 1
                    except discord.Forbidden:
                        continue
                else:
                    category = existing_categories[0]
                    categories_reused += 1
                    
                for channel_name in channels:
                    norm_chan = normalize_channel(channel_name)
                    existing_channels = [c for c in category.text_channels if normalize_channel(c.name) == norm_chan]
                    
                    if not existing_channels:
                        try:
                            await guild.create_text_channel(name=channel_name, category=category)
                            channels_created += 1
                        except discord.Forbidden:
                            pass
                    else:
                        channels_reused += 1

            print(f"Roles: Created {roles_created}, Reused {roles_reused}")
            print(f"Categories: Created {categories_created}, Reused {categories_reused}")
            print(f"Channels: Created {channels_created}, Reused {channels_reused}")

        print("\nSetup test complete.")
        await self.close()

intents = discord.Intents.default()
client = SetupClient(intents=intents)
client.run(TOKEN)
