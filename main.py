###############################################################################
#
# File:      main.py
# Author(s): Nico
# Scope:     Entry point
#
# Created:   07 February 2024
#
###############################################################################
import discord
import os
import argparse
import time
import logging

from dotenv import load_dotenv
from bot import GuysvintedBot
from commands import define_commands

if __name__ == "__main__":
    # Get arguments
    parser = argparse.ArgumentParser(description="GuysVintedBot")
    parser.add_argument(
        "-p",
        "--port",
        action="store",
        default=8000,
        help="Specify API port",
        required=False
    )
    parser.add_argument(
        "-l",
        "--log",
        action="store",
        default="guysvintedbot.log",
        help="Specify output log file",
        required=False
    )

    args = parser.parse_args()

    # Set timezone to UTC
    os.environ["TZ"] = "UTC"
    time.tzset()

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s -- %(filename)s -- %(funcName)s -- %(levelname)s -- %(message)s"
    )

    load_dotenv()
    TOKEN, GUILD_ID = os.getenv('DISCORD_TOKEN'), os.getenv('GUILD_ID')
    client = GuysvintedBot(intents=discord.Intents.all(), guild_id=GUILD_ID, port=args.port)
    define_commands(client, args.port)
    client.run(TOKEN)
