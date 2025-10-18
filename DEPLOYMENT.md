# 🚀 Editorium Bot V2.0 - Deployment Guide

## ✅ Pre-Deployment Checklist

Before deploying, ensure you have:
- [ ] Discord Bot Token from [Discord Developer Portal](https://discord.com/developers/applications)
- [ ] Bot invited to your server with proper permissions
- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)

## 📋 Required Bot Permissions

When creating your bot invite link, select these permissions:
- ✅ Read Messages/View Channels
- ✅ Send Messages
- ✅ Send Messages in Threads
- ✅ Embed Links
- ✅ Attach Files
- ✅ Read Message History
- ✅ Add Reactions
- ✅ Use Slash Commands
- ✅ Manage Messages (for deleting old showcase posts)
- ✅ Manage Roles (optional, for role automation feature)

**Permission Integer:** `414464724032` (or use Discord's permission calculator)

## 🔧 Installation Steps

### 1. Environment Setup

```powershell
# Navigate to project directory
cd "C:\Users\Shiraz Mirza\Downloads\THE EDITORIUM BOT V2.0"

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Bot Token

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_actual_bot_token_here
```

**Important:** Never commit `.env` to version control!

### 3. Database Initialization

The database will auto-initialize on first run. It creates `editorium.db` in the project root with all necessary tables.

### 4. First Run

```powershell
python bot.py
```

Expected output:
```
INFO:EditoriumBot:EditoriumBot#1234 is now online!
INFO:EditoriumBot:Connected to 1 guilds
INFO:EditoriumBot:Database initialized
INFO:EditoriumBot:Synced 30+ slash commands
INFO:EditoriumBot:Loaded cogs.profiles_cog
INFO:EditoriumBot:Loaded cogs.jobs_cog
INFO:EditoriumBot:Loaded cogs.gamification_cog
...
```

## ⚙️ Server Configuration

After bot is online, configure your server:

### 1. Set Channels

```
/set_profile_channel #profiles
/set_jobs_channel #jobs-board
```

### 2. Grant Initial Premium (Optional)

```
/premium_add @YourName 30 basic
```

### 3. Test Commands

```
/help          # View interactive help menu
/info          # View bot information
/create_profile # Create your profile
```

## 🌐 Command Sync

Slash commands sync automatically on bot startup. However:

- **Global Sync:** Takes up to 1 hour to propagate to all servers
- **Guild-Specific Sync:** Instant (dev mode)

For development, you can force guild-specific sync by adding to `.env`:
```env
GUILD_ID=your_dev_guild_id_here
```

Then modify `bot.py` to sync to specific guild during development.

## 📊 Monitoring & Logs

The bot logs to console with INFO level by default. Key events logged:
- Bot startup and cog loading
- Command execution
- Database operations
- Background task execution (premium expiry, leaderboard updates)
- Errors and exceptions

## 🔄 Background Tasks

The bot runs automatic background tasks:

- **Premium Expiry Check:** Every hour
  - Downgrades expired premium users
  
- **Leaderboard Update:** Every 6 hours
  - Refreshes leaderboard cache for better performance

These tasks start automatically when the bot starts.

## 🗄️ Database Maintenance

### Backup Database

```powershell
# Create backup
Copy-Item editorium.db editorium_backup_$(Get-Date -Format 'yyyy-MM-dd').db
```

### Reset Database

```powershell
# Stop bot, delete database, restart
Remove-Item editorium.db
python bot.py  # Will recreate fresh database
```

## 🐛 Troubleshooting

### Commands Not Appearing

**Problem:** Slash commands don't show up

**Solutions:**
1. Wait 1 hour for global sync
2. Kick and re-invite bot with updated permissions
3. Check bot has "Use Slash Commands" permission
4. Verify bot.tree.sync() completes without errors

### Permission Errors

**Problem:** Bot can't delete messages or post embeds

**Solutions:**
1. Verify bot role is high enough in role hierarchy
2. Check channel-specific permissions
3. Ensure bot has "Manage Messages" for showcase cleanup
4. Grant "Embed Links" and "Attach Files"

### Database Locked

**Problem:** `sqlite3.OperationalError: database is locked`

**Solutions:**
1. Ensure only one bot instance is running
2. Check no other process is accessing `editorium.db`
3. Restart bot

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'discord'`

**Solutions:**
1. Ensure virtual environment is activated
2. Run `pip install -r requirements.txt`
3. Verify you're using correct Python interpreter

## 🚀 Production Deployment

### Option 1: VPS/Dedicated Server

```powershell
# Install as systemd service (Linux) or use nssm (Windows)
# Create service that runs: python bot.py
# Enable auto-restart on failure
```

### Option 2: Cloud Hosting (Replit, Heroku, etc.)

1. Add `Procfile`:
```
worker: python bot.py
```

2. Set environment variables in platform dashboard
3. Use platform's database backup/restore features

### Option 3: Docker (Advanced)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

## 🔐 Security Best Practices

- ✅ **Never** commit `.env` or bot token to Git
- ✅ Use environment variables for sensitive data
- ✅ Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- ✅ Regular database backups
- ✅ Monitor bot logs for suspicious activity
- ✅ Restrict admin commands to trusted roles
- ✅ Use Discord's audit log for admin actions

## 📈 Scaling Considerations

If your bot grows to 100+ servers:

1. **Database:** Consider PostgreSQL instead of SQLite
2. **Sharding:** Implement bot sharding for 2500+ guilds
3. **Caching:** Add Redis for frequently accessed data
4. **Rate Limiting:** Implement application-level rate limits
5. **Monitoring:** Add APM tools (Sentry, DataDog, etc.)

## 🎯 Performance Optimization

- Database indexes are already configured
- Leaderboard caching reduces query load
- Ephemeral responses reduce API calls
- Background tasks run on separate schedule

## 📞 Support & Maintenance

### Regular Maintenance Tasks

- **Daily:** Check logs for errors
- **Weekly:** Backup database
- **Monthly:** Update dependencies
- **Quarterly:** Review and clean old data

### Getting Help

1. Check `/help` command in Discord
2. Review this deployment guide
3. Check logs for specific error messages
4. Review Discord.py documentation

## 🎉 You're Ready!

Your Editorium Bot V2.0 is now deployed and ready to serve your community!

Key next steps:
1. Announce bot to your server
2. Create tutorial for your users
3. Monitor first few days closely
4. Gather feedback and iterate

---

**Happy Editing! 🎬**