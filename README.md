# 🎬 Editorium Bot V2.0 - The Most Advanced Discord Bot

> **The ultimate Discord bot for editor communities** featuring profiles, jobs, gamification, premium tiers, and 45+ advanced features with interactive UI.

## ✨ Features Overview

### 🏆 Core Systems (Fully Implemented)
- ✅ **Profile System** - Create rich profiles with bio, specialty, software, portfolios, and banners
- ✅ **Showcase Channel** - Auto-post profiles with bump functionality (24h free / 6h premium cooldown)
- ✅ **Jobs & Applications** - Complete job posting system with interactive apply buttons and DM notifications
- ✅ **Premium Management** - 3-tier premium system (Basic, Pro, Elite) with exclusive perks
- ✅ **XP & Levels** - Earn XP for activities, level up, and unlock perks
- ✅ **Leaderboards** - Compete on XP, jobs, and ratings leaderboards
- ✅ **Badges & Achievements** - Unlock collectible badges for milestones
- ✅ **Interactive UI** - Modern button-based interfaces for all interactions
- ✅ **Admin Tools** - Comprehensive server configuration and management commands
- ✅ **Help System** - Interactive help menu with category buttons

### 🌟 Premium Features
**Basic Premium ($5/month)**
- Unlimited portfolio links (vs 1 for free)
- Custom banner on profile
- Gold profile embed color
- 6h bump cooldown (vs 24h)
- 🌟 Premium badge

**Pro Premium ($10/month)**
- All Basic features
- Priority job recommendations
- Advanced analytics dashboard
- Custom profile themes

**Elite Premium ($20/month)**
- All Pro features
- Verified Creator badge ✅
- Priority support
- Featured profile placement

### 📊 Database Architecture
Built on SQLite with 13+ tables:
- `profiles` - User profiles with stats
- `premium` - Premium subscriptions
- `config` - Server configuration
- `gamification` - XP, levels, badges
- `jobs` - Job postings
- `applications` - Job applications
- `ratings` - User ratings and reviews
- `collaborations` - Collaboration requests
- `marketplace_listings` - Service marketplace
- `follows` - Social following system
- `challenges` - Weekly challenges
- `referrals` - Referral program
- `leaderboard_cache` - Cached rankings

## 🚀 Quick Start

### Installation

1. **Clone and navigate to directory**
```powershell
cd "C:\Users\Shiraz Mirza\Downloads\THE EDITORIUM BOT V2.0"
```

2. **Create virtual environment**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Configure environment**
Create a `.env` file:
```env
DISCORD_TOKEN=your_bot_token_here
```

5. **Run the bot**
```powershell
python bot.py
```

### First-Time Setup

1. Invite bot to your server with required permissions:
   - Manage Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Manage Roles (optional for role automation)

2. Configure channels:
```
/set_profile_channel #profiles
/set_jobs_channel #jobs
```

3. Grant premium to test:
```
/premium_add @user 30 basic
```

## 📖 Command Reference

### 👤 Profile Commands
- `/create_profile` - Create/edit profile with interactive modal
- `/profile [@user]` - View any user's profile
- `/bump_profile` - Refresh profile in showcase (cooldown applies)
- `/delete_profile` - Delete your profile
- `/browse_profiles` - Browse all profiles (coming soon)

### 💼 Jobs & Applications
- `/create_job` - Post a job with interactive modal (+30 XP)
- `/my_jobs` - View your posted jobs
- `/my_applications` - View jobs you've applied to
- `/close_job <job_id>` - Close a job posting
- **Apply Button** - Click on job posts to apply (+20 XP)

### 🏆 Gamification
- `/level [@user]` - Check level, XP, and progress
- `/leaderboard [category]` - View top 10 (categories: xp, jobs, rating)
- `/badges` - View your earned badges

### 👥 Social Features
- `/follow <user>` - Follow users for activity updates (coming soon)
- `/collab` - Create collaboration requests (coming soon)
- `/dashboard` - View your personal stats dashboard
- `/marketplace` - Browse marketplace (coming soon)

### ⚙️ Admin Commands (Requires Manage Server)
- `/set_profile_channel <channel>` - Configure profile showcase
- `/set_jobs_channel <channel>` - Configure job postings
- `/premium_add <user> <days> [tier]` - Grant premium
- `/premium_remove <user>` - Remove premium
- `/premium_list` - View active premium users
- `/config` - View server configuration

### 📚 Help & Info
- `/help` - Interactive help menu with category buttons
- `/info` - Bot information and statistics

## 🎯 XP & Rewards System

### Earning XP
- Create profile: **+50 XP** 🎉
- Create job: **+30 XP** 💼
- Apply to job: **+20 XP** 📝
- Job accepted: **+50 XP** ✅
- Bump profile: **+10 XP** ⬆️
- Complete job: **+100 XP** 🏆

### Level Perks
- **Level 5** - Unlock custom themes
- **Level 10** - Special badge + faster bump cooldown
- **Level 20** - Featured on leaderboard
- **Level 50** - Legendary status

### Badges & Achievements
- 📝 **Profile Creator** - Create your first profile
- 💼 **First Job** - Get your first job accepted
- 🏆 **Top 10** - Reach top 10 on leaderboard
- ✅ **Verified** - Verified creator status
- ⭐ **Level 10** - Reach level 10

## 🗄️ Database Structure

The bot uses a modular SQLite database located at `editorium.db` with comprehensive schema:

- **Profiles**: Bio, specialty, software, portfolio links, banner, stats
- **Premium**: User ID, tier, expiry date
- **Gamification**: XP, levels, points, badges, achievements
- **Jobs**: Job posts with creator, status, applications
- **Applications**: Job applications with status tracking
- **Ratings**: User ratings and reviews
- Plus 7 more tables for advanced features

## 🔧 Architecture

```
THE EDITORIUM BOT V2.0/
├── bot.py                     # Main bot file with event handlers
├── .env                       # Environment configuration
├── editorium.db              # SQLite database (auto-created)
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── bot_backup_before_reset.py # Original implementation backup
├── db/
│   ├── sqlite_helper.py      # Core database operations
│   ├── gamification_helper.py # XP, levels, leaderboards
│   └── jobs_helper.py        # Jobs and applications
├── cogs/
│   ├── profiles_cog.py       # Profile system
│   ├── jobs_cog.py           # Jobs & applications
│   ├── gamification_cog.py   # XP, levels, leaderboards
│   ├── social_cog.py         # Social features
│   ├── marketplace_cog.py    # Marketplace (placeholder)
│   ├── admin_cog.py          # Admin commands
│   └── help_cog.py           # Help system
└── tests/
    └── test_sqlite_helper.py # Unit tests
```

## 🎨 Design Philosophy

- **Interactive First**: All features use Discord's modern UI components (buttons, selects, modals)
- **User-Friendly**: Clear feedback, helpful error messages, ephemeral responses
- **Gamified**: XP, levels, badges keep users engaged
- **Modular**: Clean cog architecture for easy maintenance
- **Scalable**: Efficient database design with indexes
- **Premium-Ready**: Built-in monetization with tiered perks

## 🔐 Security & Best Practices

- ✅ URL validation for portfolio links
- ✅ Permission checks for admin commands
- ✅ Rate limiting (via Discord's built-in system)
- ✅ Thread-safe database operations
- ✅ Ephemeral responses for sensitive data
- ✅ Input validation on all modals
- ✅ Background tasks for maintenance

## 🚧 Roadmap

### Coming Soon
- [ ] Advanced search & filtering for profiles
- [ ] Weekly challenges with voting
- [ ] Collaboration matching system
- [ ] Full marketplace with escrow
- [ ] Analytics dashboard
- [ ] YouTube/Twitch integration
- [ ] Referral program
- [ ] Custom profile themes
- [ ] Role automation based on levels
- [ ] API endpoints for external integrations

## 🐛 Troubleshooting

### Bot not responding
1. Check bot is online: `bot.py` is running
2. Verify slash commands are synced
3. Ensure bot has required permissions
4. Check `.env` token is correct

### Commands not showing
- Wait 1 hour for Discord to sync globally
- Or use guild-specific sync for instant testing

### Database errors
- Ensure `editorium.db` is writable
- Check file permissions
- Database auto-initializes on first run

## 📄 License

This project is private and proprietary. All rights reserved.

## 💬 Support

For support, feature requests, or bug reports:
- Use `/help` in Discord
- Contact server administrators
- Check command documentation with `/info`

---

**Editorium Bot V2.0** - Built with ❤️ for editor communities
*Powered by discord.py | Version 2.0.0 | © 2025*
