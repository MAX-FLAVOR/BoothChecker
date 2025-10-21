# main.py
import json
import logging
import booth_sqlite
import booth_discord

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    # Load configuration
    with open("config.json") as file:
        config_json = json.load(file)
    
    # Read configuration values
    discord_bot_token = config_json['discord_bot_token']
    selenium_url = config_json['selenium_url'] 

    # Initialize database and bot
    booth_db = booth_sqlite.BoothSQLite('./version/db/booth.db', logger)
    bot = booth_discord.DiscordBot(booth_db, logger)
    selumin = booth.BoothCrawler(selenium_url)
    bot.run(discord_bot_token)

if __name__ == "__main__":
    main()