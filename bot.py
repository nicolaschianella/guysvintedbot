###############################################################################
#
# File:      bot.py
# Author(s): Nico
# Scope:     The bot itself
#
# Created:   07 February 2024
#
###############################################################################
import time

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
                            USER_INFOS_ROUTE, GET_IMAGES_URL_ROUTE, NO_IMAGE_AVAILABLE_URL, BRANDS, CLOTHES_STATES, \
                              FUZZ_RATIO, GET_CLOTHES_FROM_STOCK_ROUTE
from utils.buttons import BuyButtons, StockButtons
from utils.utils import reformat_list_strings
from concurrent.futures import ThreadPoolExecutor
from thefuzz import fuzz


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
        self.all_clothes_channel = ""
        self.logs_channel = ""
        self.stock_channel = ""
        self.clothes_ids = self.get_clothes_ids_in_stock()
        self.task = ""
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        """
        Called when the bot starts. Launches all clothes requests and associated channels to post.
        :return: None
        """
        # Acquire requests and channel_ids
        clothe_requests, channel_ids = self.load_all_active_requests_and_channels()

        if clothe_requests:
            # Run tasks
            logging.info(f"Running tasks for requests: {clothe_requests}, channel_ids: {channel_ids}")
            self.task = self.loop.create_task(self.get_clothes(clothe_requests, channel_ids))

        else:
            # Log message
            logging.info("No requests found - loop not started")

    async def on_ready(self) -> None:
        """
        Called when the bot starts. Simple log message.
        :return: None
        """
        # Channels need to be defined here to not get NoneType
        self.all_clothes_channel = self.get_channel(int(os.getenv("ALL_CLOTHES_CHANNEL_ID")))
        self.logs_channel = self.get_channel(int(os.getenv("LOGS_CHANNEL_ID")))
        self.stock_channel = self.get_channel(int(os.getenv("STOCK_CHANNEL_ID")))

        # Enable stock buttons on startup
        for clothe_id in self.clothes_ids:
            self.add_view(StockButtons(clothe_id=clothe_id,
                                       port=self.port,
                                       logs_channel=self.logs_channel))

        logging.info(f"Ready & logged in as {self.user}")

    def get_clothes_ids_in_stock(self) -> list[str]:
        """
        Get all ids of clothes in stock
        Returns: list[str], list of found clothes ids

        """
        # API call
        clothes_in_stock = requests.get(f"{API_HOST}:{self.port}/{GET_CLOTHES_FROM_STOCK_ROUTE}",
                                        data=json.dumps({"which": "in_stock"}))

        # Case success
        if clothes_in_stock.status_code == 200:
            stock_clothes = json.loads(clothes_in_stock.json()["data"])["found_clothes"]
            clothes_ids = [clothe["clothe_id"] for clothe in stock_clothes if clothe["state"] == "in_stock"]

            logging.info(f"Found following clothes ids (in_stock mode): {clothes_ids}")

            return clothes_ids

        # Case no success - end the program
        else:
            logging.error(f"There was an issue while retrieving in_stock clothes (API status_code: "
                          f"{clothes_in_stock.status_code})")
            sys.exit(1)

    def get_clothes_api(self, brand_ids, status_ids) -> requests.Response:
        """
        Embedded function to be executed in a separated thread. Performs a global clothe request to the API
        The used request contains all the referenced brands and clothes states

        Returns: requests.Response, API response

        """
        logging.info("Sending global clothes request")
        # Request the API to get new clothes
        response = requests.get(f"{API_HOST}:{self.port}/{GET_CLOTHES_ROUTE}",
                                data=json.dumps({"per_page": PER_PAGE,
                                                 "brand_ids": brand_ids,
                                                 "status_ids": status_ids}))

        return response

    async def find_matching_and_post(self, request, new_clothes) -> None:
        """
        Find matching between a given request and new_clothes
        Matching = (same brand) + (clothe state matching) + (price matching) + (search_text matching)
        Args:
            request: dict, clothe request
            new_clothes: list, new clothes found

        Returns: None

        """
        # Matching clothes to return
        matching = []

        # Build embedded message if matching found
        all_embeds = []
        embeds = []

        # Get channel_id
        channel = self.channels[str(request["_id"])]

        # We need to format new_clothes to find matching
        for clothe in new_clothes:
            # Brand matching
            if clothe["brand_title"] not in BRANDS.keys():
                continue
            if BRANDS[clothe["brand_title"]] != request["brand_ids"]:
                continue

            # Clothe state matching
            if CLOTHES_STATES[clothe["status"]] not in request["status_ids"]:
                continue

            # Price matching
            if not ((float(clothe["price_no_fee"]) >= float(request["price_from"])) and
                    (float(clothe["price_no_fee"]) <= float(request["price_to"]))):
                continue

            # Search text matching - use Levenshtein Distance
            if request["search_text"]:
                ratio = fuzz.partial_ratio(clothe["title"], request["search_text"])

                if not ratio >= FUZZ_RATIO:
                    continue

                logging.info(f"Selected clothe: {clothe}, fuzz_ratio: {ratio}")

            logging.info(f"Matching found between request: {request} and clothe: {clothe}")

            # Once here, clothe has been selected to be posted
            matching.append(clothe)

            # Call the API to get user infos
            user_infos = requests.get(f"{API_HOST}:{self.port}/{USER_INFOS_ROUTE}",
                                      data=json.dumps({"user_id": clothe["seller_id"]}))

            if user_infos.status_code != 200:
                logging.error(f"Could not retrieve user infos for user_id: {clothe['seller_id']} "
                              f"(channel: {channel})")
                raise Exception(f"Could not retrieve user infos for user_id: {clothe['seller_id']} "
                                f"(channel: {channel})")

            logging.info(f"Found user_infos: {user_infos.json()} for request: {request} "
                         f"(channel: {channel})")

            # Get result
            user_reviews = json.loads(user_infos.json()["data"])["number_reviews"]
            user_stars = json.loads(user_infos.json()["data"])["number_stars"]

            # Call the API to get images
            images_url = requests.get(f"{API_HOST}:{self.port}/{GET_IMAGES_URL_ROUTE}",
                                      data=json.dumps({"clothe_url": clothe["url"]}))

            # Handle case where we have no images (internal server error)
            if images_url.status_code != 200:
                logging.warning(f"No status_code 200 but {images_url.status_code} for request: {request} "
                                f"(channel: {channel}) - forcing default no image available image")
                # Default no image available image
                url_list = [NO_IMAGE_AVAILABLE_URL]

            else:
                # Retrieve images
                url_list = images_url.json()["data"]["images_url"]

                # Case no image received
                if not url_list:
                    logging.warning(f"No image found for request: {request} (channel: {channel}) - "
                                    f"forcing default no image available image")
                    # Default no image available image
                    url_list = [NO_IMAGE_AVAILABLE_URL]

                else:
                    logging.info(f"Found {len(url_list)} images for request: {request} "
                                 f"(channel: {channel})")
                    logging.info(f"Images URLs: {url_list}")

            # Convert publish date to timestamp for dynamic display (drop milliseconds)
            try:
                api_time = datetime.datetime.strptime(clothe["created_at_ts"], "%Y-%m-%dT%H:%M:%S%z")
                api_time_ts = int(datetime.datetime.timestamp(api_time))
            except Exception as e:
                logging.warning(f"Exception for clothe {clothe} encountered during date formatting: {e}")
                api_time_ts = "NA"

            # Custom title in case we may have suspicious pictures
            title = clothe["title"] if not clothe["is_photo_suspicious"] \
                else clothe["title"] + " - PHOTOS SUSPICIEUSES"

            # Build reviews display
            reviews = "⭐" * user_stars if user_stars != 0 else "⛔"

            for url in url_list:
                # We force URL to everytime the product url
                embed = discord.Embed(title=title,
                                      color=discord.Color.dark_blue(),
                                      url=clothe["url"]).set_image(url=url)
                if api_time_ts != "NA":
                    embed.add_field(name="⌛ Publié", value=f"<t:{api_time_ts}:R>", inline=True)
                else:
                    embed.add_field(name="⌛ Publié", value=f"{api_time_ts}", inline=True)
                embed.add_field(name="👕️ Marque", value=clothe["brand_title"], inline=True)
                embed.add_field(name="📏 Taille", value=clothe["size_title"], inline=True)
                embed.add_field(name="🌟 Avis", value=reviews + f" ({user_reviews})", inline=True)
                embed.add_field(name="💎 État", value=clothe["status"], inline=True)
                embed.add_field(name="💰 Prix", value=f"{clothe['total_item_price']} € | "
                                                     f"{clothe['price_no_fee']} € + "
                                                     f"{clothe['service_fee']} € fees",
                                inline=True)
                embeds.append(embed)

            await channel.send(embeds=embeds,
                               view=BuyButtons(request_id=str(request["_id"]),
                                               clothe=clothe,
                                               embeds=embeds,
                                               ratio=ratio,
                                               logs_channel=self.logs_channel,
                                               stock_channel=self.stock_channel,
                                               port=self.port))
            await self.all_clothes_channel.send(embeds=embeds,
                                                view=BuyButtons(request_id=str(request["_id"]),
                                                                clothe=clothe,
                                                                embeds=embeds,
                                                                ratio=ratio,
                                                                logs_channel=self.logs_channel,
                                                                stock_channel=self.stock_channel,
                                                                port=self.port))

            all_embeds.append(embeds)

            embeds = []

    async def get_clothes(self, clothe_requests: list[dict], channel_ids: list[str]) -> None:
        """
        Sends new clothes using request and post in channels.
        :param clothe_requests: list[dict], list of request dictionaries
        :param channel_ids: list[str], corresponding channel_ids where posts are going to be located
        (we add one more per default where everything is centralised)
        :return:
        """
        # Wait to have everything set up
        await self.wait_until_ready()

        # Add keys in dicts = running tasks
        for request, channel_id in zip(clothe_requests, channel_ids):
            self.requests[str(request["_id"])] = request
            self.channels[str(request["_id"])] = self.get_channel(int(channel_id))

        # Define global cache
        cache = []

        # Minimal waiting time
        wait_time = int(WAIT_TIME)

        # Define filters on brands and clothes status
        brand_ids = reformat_list_strings(list(BRANDS.values()))
        status_ids = reformat_list_strings(list(CLOTHES_STATES.values()))

        try:
            # Infinite loop
            while not self.is_closed():
                # To not get rate limited
                start = time.time()
                # Run in a separate thread to not freeze the bot - global clothes search
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(ThreadPoolExecutor(), self.get_clothes_api, brand_ids, status_ids)

                if response.status_code != 200:
                    logging.error(f"Could not retrieve clothes for global request, response: {response.text}")
                    await self.logs_channel.send("⚠️ Les recherches ont été interrompues après un souci - erreur [1]")
                    raise Exception(f"Could not retrieve clothes for global request")

                # Load clothes
                data = json.loads(response.json()["data"])

                # To prevent the bot to post multiple messages on startup
                if not cache:
                    cache = [clothe["id"] for clothe in data]

                # Now compare to cache
                new_clothes = [clothe for clothe in data if clothe["id"] not in cache]

                # Reverse list to post from oldest to newest
                new_clothes.reverse()

                # If new clothes we find if there are matching requests (coded in separate threads)
                # If yes we post clothes in the corresponding channel (and global one) and update cache
                if new_clothes:
                    logging.info(f"Found {len(new_clothes)} new clothe(s) matching global filters in this API call")

                    await asyncio.gather(*[self.find_matching_and_post(request, new_clothes)
                                           for request in list(self.requests.values())])

                    for clothe in new_clothes:
                        # Update global cache
                        cache.insert(0, clothe["id"])

                    # Security for cache length
                    if len(cache) > 4 * len(clothe_requests) * int(PER_PAGE):
                        previous_size = len(cache)
                        cache = cache[:3 * len(clothe_requests) * int(PER_PAGE)]
                        logging.info(f"Cache size pruned from {previous_size} to {len(cache)}")

                # To not get API rate limited
                end = time.time()
                waiting_time = wait_time - (end - start)

                if waiting_time > 0:
                    logging.info(f"Waiting for {waiting_time} seconds before next API call")
                    await asyncio.sleep(waiting_time)

        except Exception as e:
            logging.error(f"There was an exception with the global request: {e}")

            # Reset dicts and task
            self.reset_global_task()

            # Write a message in the request channel (local only)
            await self.logs_channel.send("⚠️ Les recherches ont été interrompues après un souci - erreur [2]")

    def load_all_active_requests_and_channels(self) -> tuple:
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

    def reset_global_task(self) -> None:
        """
        Resets global task
        Returns: None

        """
        # Try to stop the running task (if launched)
        try:
            self.task.cancel()
            logging.info("Removed global clothes requests task")

        except Exception as e:
            logging.warning(f"Global clothes requests task was never launched. Error: {e}")

        self.task = ""
        self.requests = {}
        self.channels = {}

        logging.info("All requests stopped successfully")
