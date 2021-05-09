from bot import Bot
from dotenv import load_dotenv
import os
import logging
load_dotenv()


logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)

if __name__ == "__main__":
    bot = Bot()
    bot.logging = log
    bot.run(os.environ.get("BOT_TOKEN"), reconnect=True)
