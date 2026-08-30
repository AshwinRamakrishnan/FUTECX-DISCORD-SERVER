# FUTECX Discord Community Ecosystem

FUTECX is a production-grade Discord community ecosystem encompassing a Discord bot, backend API, and a React Admin Dashboard.

## Project Structure
- `backend/`: FastAPI + discord.py monorepo. Handles all business logic (XP, tasks, projects).
- `dashboard/`: React + Vite + Tailwind CSS admin dashboard.

## Technologies Used
- **Backend:** Python 3, FastAPI, discord.py, SQLAlchemy (ORM)
- **Database:** PostgreSQL (Production), SQLite (Local Dev fallback)
- **Frontend:** React, Vite, Tailwind CSS, Lucide React

## Prerequisites
1. Python 3.10+
2. Node.js 18+
3. PostgreSQL (or you can use the default SQLite fallback for quick testing)

## Environment Variables
Copy `.env.example` to `.env` in the root of the `futecx` folder.

```env
DISCORD_TOKEN=your_discord_bot_token_here
DATABASE_URL=sqlite:///./futecx.db  # Use postgresql://user:pass@localhost:5432/db for production
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
```

## Discord Developer Portal Setup
1. Create an application in the [Discord Developer Portal](https://discord.com/developers/applications).
2. Go to "Bot" and enable **Message Content Intent** and **Server Members Intent**.
3. Invite the bot using the URL Generator (OAuth2 -> URL Generator). Select `bot` and `applications.commands` scopes.
4. Set required permissions: `Send Messages`, `Embed Links`, `Manage Roles` (for later role updates).

## Bot & API Deployment
1. Navigate to `backend/` and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the unified Backend + Bot server:
   ```bash
   python main.py
   ```
   *This will automatically initialize the database schema.*

## Dashboard Deployment
1. Navigate to `dashboard/`:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```

## Remaining External Configuration
- Discord Tokens must be populated in the `.env` file for the bot to come online.
- PostgreSQL should be spun up via Docker for production deployment (`docker run --name futecx-db -e POSTGRES_PASSWORD=password -d postgres`).
- ReportLab and specific certificate PDF template designs need to be finalized in `certificate_service.py`.
