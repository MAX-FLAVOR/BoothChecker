# main.py
import json
import logging
import booth as booth_module
import booth_sql
import booth_discord
from logging_setup import attach_syslog_handler

LOG_FORMAT = '[%(asctime)s] - [%(levelname)s] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

logger = logging.getLogger('BoothDiscord')
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.hasHandlers():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

def main():
    # Load configuration
    with open("config.json") as file:
        config_json = json.load(file)

    logging_config = config_json.get('logging', {})
    syslog_config = logging_config.get('syslog', {})
    attach_syslog_handler(logger, syslog_config, formatter)
    if syslog_config.get('enabled') and syslog_config.get('address'):
        port_value = syslog_config.get('port', 514)
        try:
            port = int(port_value)
        except (TypeError, ValueError):
            port = port_value
        logger.info("Syslog logging enabled: sending logs to %s:%s", syslog_config.get('address'), port)
    
    # Read configuration values
    discord_bot_token = config_json['discord_bot_token']
    selenium_url = config_json['selenium_url'] 
    fbx_only = config_json['fbx_only']

    # Initialize database and bot
    booth_crawler = booth_module.BoothCrawler(selenium_url)
    postgres_config = dict(config_json['postgres'])
    booth_db = booth_sql.BoothPostgres(postgres_config, booth_crawler, logger)
    bot = booth_discord.DiscordBot(booth_db, logger)
    bot.run(discord_bot_token)

if __name__ == "__main__":
    main()
