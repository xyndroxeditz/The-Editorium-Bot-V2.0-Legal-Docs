# ⚡ Quick Start Guide - Editorium Bot V2.0

Get your bot running in **5 minutes**!

## Step 1: Get Your Bot Token (2 minutes)

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name it "Editorium Bot"
3. Go to "Bot" tab → Click "Add Bot"
4. Under "Token" → Click "Reset Token" → Copy the token
5. **Save this token** - you'll need it in Step 3

## Step 2: Invite Bot to Your Server (1 minute)

1. In Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Attach Files
   - ✅ Manage Messages
   - ✅ Use Slash Commands
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

## Step 3: Configure Bot (2 minutes)

1. Create `.env` file in the bot directory:
```env
DISCORD_TOKEN=paste_your_token_here
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Run the bot:
```powershell
python bot.py
```

You should see:
```
INFO:EditoriumBot:EditoriumBot#1234 is now online!
INFO:EditoriumBot:Synced 30+ slash commands
```

## Step 4: Configure Your Server (30 seconds)

In Discord, run these commands:

```
/set_profile_channel #profiles
/set_jobs_channel #jobs
```

## Step 5: Test It! (30 seconds)

```
/help              # View all commands
/create_profile    # Create your profile
/level             # Check your XP
```

## 🎉 You're Done!

Your bot is now fully operational with:
- ✅ Profile system with showcase
- ✅ Job postings and applications
- ✅ XP and leaderboards
- ✅ Premium management
- ✅ 30+ slash commands
- ✅ Interactive buttons and modals

## 🔥 Power User Tips

### Grant Yourself Premium
```
/premium_add @YourName 999 elite
```

### Check Bot Stats
```
/info
```

### View All Commands
```
/help
```
Then click the category buttons!

## ❓ Troubleshooting

**Commands not showing?**
- Wait 1 hour for global sync, OR
- Kick and re-invite bot

**Permission errors?**
- Make sure bot role is high in hierarchy
- Check channel permissions

**Database errors?**
- Database auto-creates on first run
- Check file permissions

## 📚 Next Steps

- Read the full [README.md](README.md) for all features
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for what's included

## 🚀 Start Building Your Community!

Announce the bot to your server:
```
🎬 **Editorium Bot is now live!**

Create your profile: /create_profile
Post a job: /create_job
Check your level: /level
View help: /help

Let's build the best editor community on Discord! 🚀
```

---

**Need help?** Check `/help` in Discord or read the docs!
