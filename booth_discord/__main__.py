# main.py
import json
import logging
import booth as booth_module
import booth_sql
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
    booth_crawler = booth_module.BoothCrawler(selenium_url)
    postgres_config = dict(config_json['postgres'])
    booth_db = booth_sql.BoothPostgres(postgres_config, booth_crawler, logger)
    bot = booth_discord.DiscordBot(booth_db, logger)
    bot.run(discord_bot_token)

if __name__ == "__main__":
    main()
