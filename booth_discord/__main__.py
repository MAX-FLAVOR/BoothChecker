# main.py
import os
import logging
import booth_sqlite
import booth_discord

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    booth_db = booth_sqlite.BoothSQLite('./version/booth.db')
    bot = booth_discord.DiscordBot(booth_db, logger)
    bot.run(os.getenv("discord_bot_token"))

if __name__ == "__main__":
    main()