"""__init__.py

Set up the program and what will be imported by main.py.
"""

import os

import dotenv

from .client import MyBot

# Load environment variables from .env if running locally
# Has no effect when running remotely with no .env file
dotenv.load_dotenv(override=True)

# Variables to export
BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = MyBot(os.environ["BOT_VERSION"])
