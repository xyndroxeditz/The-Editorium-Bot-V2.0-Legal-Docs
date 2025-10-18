"""
Editorium Bot V2.0 - The Most Advanced Discord Bot
Complete implementation with profiles, jobs, gamification, marketplace, and more.
"""
import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import asyncio
import logging
from db.sqlite_helper import init_db
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('EditoriumBot')

# Load environment
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DB_PATH = os.path.join(os.path.dirname(__file__), "editorium.db")

# Debug token
if not TOKEN:
    logger.error("DISCORD_TOKEN not found in .env file!")
    exit(1)
elif len(TOKEN) < 50:
    logger.error(f"DISCORD_TOKEN seems too short ({len(TOKEN)} chars). Check your .env file!")
    exit(1)
else:
    logger.info(f"Token loaded successfully ({len(TOKEN)} chars)")

# Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
bot.db_path = DB_PATH

@bot.event
async def on_ready():
    logger.info(f'{bot.user} is now online!')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Initialize database
    init_db(DB_PATH)
    logger.info('Database initialized')
    
    # Sync commands
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'Failed to sync commands: {e}')
    
    # Start background tasks
    if not premium_expiry_check.is_running():
        premium_expiry_check.start()
    if not leaderboard_update.is_running():
        leaderboard_update.start()
    
    # Set status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="/help | Editorium V2.0"
    ))

@tasks.loop(hours=1)
async def premium_expiry_check():
    """Check and downgrade expired premium users"""
    from db.sqlite_helper import list_active_premium, remove_premium
    try:
        now = int(time.time())
        active = list_active_premium(DB_PATH, now)
        # Already filtered by active, but double check
        for user in active:
            if user['expiry_date'] <= now:
                remove_premium(DB_PATH, user['user_id'])
                logger.info(f"Downgraded expired premium for user {user['user_id']}")
    except Exception as e:
        logger.error(f"Premium expiry check failed: {e}")

@tasks.loop(hours=6)
async def leaderboard_update():
    """Update leaderboard cache"""
    from db.gamification_helper import update_leaderboard_cache
    try:
        for category in ['xp', 'jobs', 'rating']:
            update_leaderboard_cache(DB_PATH, 'weekly', category)
        logger.info("Leaderboards updated")
    except Exception as e:
        logger.error(f"Leaderboard update failed: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f'Command error: {error}')

async def load_cogs():
    """Load all cogs"""
    cogs = [
        'cogs.profiles_cog',
        'cogs.jobs_cog',
        'cogs.gamification_cog',
        'cogs.social_cog',
        'cogs.marketplace_cog',
        'cogs.admin_cog',
        'cogs.premium_cog',
        'cogs.help_cog',
        'cogs.media_cog',
        'cogs.teams_cog'
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'Loaded {cog}')
        except Exception as e:
            logger.error(f'Failed to load {cog}: {e}')

async def main():
    logger.info("Starting Editorium Bot V2.0...")
    try:
        async with bot:
            logger.info("Loading cogs...")
            await load_cogs()
            logger.info("All cogs loaded, starting bot...")
            await bot.start(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())