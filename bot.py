###############################################################################
#
# File:      bot.py
# Author(s): Nico
# Scope:     The bot itself
#
# Created:   07 February 2024
#
###############################################################################
import discord
import asyncio
import requests
import json
import os
import sys
import datetime
import logging

from discord import app_commands
from utils.defines import API_HOST, GET_CLOTHES_ROUTE, REQUESTS_CHANNEL_IDS_ROUTE, WAIT_TIME, PER_PAGE, \
                            USER_INFOS_ROUTE, GET_IMAGES_URL_ROUTE, NO_IMAGE_AVAILABLE_URL
from utils.display_requests import Buttons


class GuysVintedBot(discord.Client):
    """
    The GuysVintedBot hehe.
    All the bot functionalities all located here.
    Thanks, Hugo and Riccardo, for being the way you are.
    """
    def __init__(self, guild_id, port, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Guild id to sync
        self.guild_id = guild_id
        self.port = port
        self.requests = {}
        self.channels = {}
        self.running_requests = {}
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """
        Called when the bot starts. Launches all clothes requests and associated channels to post.
        :return: None
        """
        # Acquire requests and channel_ids
        clothe_requests, channel_ids = await self.load_all_active_requests_and_channels()

        # Run tasks
        for request, channel_id in zip(clothe_requests, channel_ids):
            logging.info(f"Running task for channel: {channel_id}, request: {request}")
            self.running_requests[str(request["_id"])] = self.loop.create_task(self.get_clothes(request, int(channel_id)))

    async def on_ready(self) -> None:
        """
        Called when the bot starts. Simple log message.
        :return: None
        """
        logging.info(f"Ready & logged in as {self.user}")

    async def get_clothes(self, request: dict, channel_id: int) -> None:
        """
        Sends new clothes using request and post in channels.
        :param request: dict, request dictionary
        :param channel_id: int, channel_id where posts are going to be located (we add one more per default
        where everything is centralised)
        :return:
        """
        # Wait to have everything set up
        await self.wait_until_ready()

        # Add keys in dicts
        self.requests[str(request["_id"])] = request
        self.channels[str(request["_id"])] = channel_id

        # Define cache - using clothes ids
        cache = []

        # Define channels where we are going to post messages
        channel = self.get_channel(channel_id)
        all_clothes_channel = self.get_channel(int(os.getenv("ALL_CLOTHES_CHANNEL_ID")))

        try:
            # Infinite loop
            while not self.is_closed():
                # Request the API to get new clothes
                response = requests.get(f"{API_HOST}:{self.port}/{GET_CLOTHES_ROUTE}",
                                        data=json.dumps(request))

                if response.status_code != 200:
                    logging.error(f"Could not retrieve clothes for request: {request} (channel_id: {channel_id})")
                    raise Exception(f"Could not retrieve clothes for request: {request} (channel_id: {channel_id})")

                # Load clothes
                data = json.loads(response.json()["data"])

                # To prevent the bot to post multiple messages on startup
                if not cache:
                    cache = [clothe["id"] for clothe in data]

                # Now compare to cache
                new_clothes = [clothe for clothe in data if clothe["id"] not in cache]

                # Reverse list to post from oldest to newest
                new_clothes.reverse()

                # If new clothes we post and update cache
                if new_clothes:
                    logging.info(f"Found {len(new_clothes)} new clothe(s) for request: {request} "
                                 f"(channel_id: {channel_id})")

                    for clothe in new_clothes:
                        # Call the API to get user infos
                        user_infos = requests.get(f"{API_HOST}:{self.port}/{USER_INFOS_ROUTE}",
                                                  data=json.dumps({"user_id": clothe["seller_id"]}))

                        if user_infos.status_code != 200:
                            logging.error(f"Could not retrieve user infos for user_id: {clothe['seller_id']} "
                                          f"(channel_id: {channel_id})")
                            raise Exception(f"Could not retrieve user infos for user_id: {clothe['seller_id']} "
                                            f"(channel_id: {channel_id})")

                        logging.info(f"Found user_infos: {user_infos.json()} for request: {request} "
                                     f"(channel_id: {channel_id})")

                        # Get result
                        user_reviews = json.loads(user_infos.json()["data"])["number_reviews"]
                        user_stars = json.loads(user_infos.json()["data"])["number_stars"]

                        # Call the API to get images
                        images_url = requests.get(f"{API_HOST}:{self.port}/{GET_IMAGES_URL_ROUTE}",
                                                  data=json.dumps({"clothe_url": clothe["url"]}))

                        # Handle case where we have no images (internal server error)
                        if images_url.status_code != 200:
                            logging.warning(f"No status_code 200 but {images_url.status_code} for request: {request} "
                                            f"(channel_id: {channel_id}) - forcing default no image available image")
                            # Default no image available image
                            url_list = [NO_IMAGE_AVAILABLE_URL]

                        else:
                            # Retrieve images
                            url_list = images_url.json()["data"]["images_url"]

                            # Case no image received
                            if not url_list:
                                logging.warning(f"No image found for request: {request} (channel_id: {channel_id}) - "
                                                f"forcing default no image available image")
                                # Default no image available image
                                url_list = [NO_IMAGE_AVAILABLE_URL]

                            else:
                                logging.info(f"Found {len(url_list)} images for request: {request} "
                                             f"(channel_id: {channel_id})")
                                logging.info(f"Images URLs: {url_list}")

                        # Convert publish date to timestamp for dynamic display (drop milliseconds)
                        api_time = datetime.datetime.strptime(clothe["created_at_ts"], "%Y-%m-%dT%H:%M:%S%z")
                        api_time_ts = int(datetime.datetime.timestamp(api_time))

                        # Custom title in case we may have suspicious pictures
                        title = clothe["title"] if not clothe["is_photo_suspicious"] \
                            else clothe["title"] + " - PHOTOS SUSPICIEUSES"

                        # Build reviews display
                        reviews = "⭐" * user_stars if user_stars != 0 else "⛔"

                        # Build embedded message
                        embeds = []

                        for url in url_list:
                            # We force URL to everytime the product url
                            embed = discord.Embed(title=title,
                                                  color=discord.Color.dark_blue(),
                                                  url=clothe["url"]).set_image(url=url)
                            embed.add_field(name="⌛ Publié", value=f"<t:{api_time_ts}:R>", inline=True)
                            embed.add_field(name="👕️ Marque", value=clothe["brand_title"], inline=True)
                            embed.add_field(name="📏 Taille", value=clothe["size_title"], inline=True)
                            embed.add_field(name="🌟 Avis", value=reviews + f" ({user_reviews})", inline=True)
                            embed.add_field(name="💎 État", value=clothe["status"], inline=True)
                            embed.add_field(name="💰 Prix", value=f"{clothe['total_item_price']} € | "
                                                                 f"{clothe['price_no_fee']} € + "
                                                                 f"{clothe['service_fee']} € fees",
                                            inline=True)
                            embeds.append(embed)

                        # Post in local and global channels - add buttons with parameters needed for visiting item
                        # and autobuy
                        await channel.send(embeds=embeds, view=Buttons(url=clothe["url"]))
                        await all_clothes_channel.send(embeds=embeds, view=Buttons(url=clothe["url"]))

                        logging.info(f"Message posted successfully for request: {request} (channel_id: {channel_id})")

                        # Update cache (newest to oldest)
                        cache.insert(0, clothe["id"])

                    # Security for cache length
                    if len(cache) > 4 * int(PER_PAGE):
                        logging.info(f"Cache size pruned from {len(cache)} to {len(cache[:3 * int(PER_PAGE)])} "
                                     f"for request: {request} (channel_id: {channel_id})")
                        cache = cache[:3 * int(PER_PAGE)]

                # Finally wait for another API call
                logging.info(f"Waiting {int(WAIT_TIME)} seconds for request: {request} (channel_id: {channel_id})")
                await asyncio.sleep(int(WAIT_TIME))

        except Exception as e:
            # Remove keys from the dicts
            self.running_requests.pop(str(request["_id"]))
            self.requests.pop(str(request["_id"]))
            self.channels.pop(str(request["_id"]))

            logging.error(f"There was an issue with request: {request} (channel_id: {channel_id}): {e}")
            logging.error(f"Removed task - request: {request} (channel_id: {channel_id})")

            # Write a message in the request channel (local only)
            await channel.send(f"Il y a eu un souci avec cette recherche. Erreur: {e}")

    async def load_all_active_requests_and_channels(self) -> tuple:
            """
            Loads all the active requests existing in the DB and associated channels ids.
            :return: tuple, two elements, first one is a list of requests (dict) and the second one the list
            of associated channels ids (int) in the same order.
            """
            try:
                # Request the API to get {requests: channel_ids}
                response = requests.get(f"{API_HOST}:{self.port}/{REQUESTS_CHANNEL_IDS_ROUTE}")

                # Case success - return requests and tasks
                if response.status_code == 200:
                    # Get data and return
                    response_json = json.loads(response.json()["data"])

                    clothe_requests = response_json["requests"]
                    channel_ids = response_json["channel_ids"]

                    logging.info(f"Found existing requests: {clothe_requests} (corresponding channel_ids: "
                                 f"{channel_ids})")

                    return clothe_requests, channel_ids

                # Case no success - end the program
                else:
                    logging.error(f"There was an issue while retrieving active requests and corresponding channels "
                                  f"- ending program (API status_code: {response.status_code})")
                    sys.exit(1)

            except Exception as e:
                logging.error(f"There was an exception while retrieving active requests and corresponding channels "
                              f"- ending program (exception: {e})")
                sys.exit(1)

