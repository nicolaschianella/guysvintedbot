###############################################################################
#
# File:      commands.py
# Author(s): Nico
# Scope:     File defining all available bot commands
#
# Created:   07 February 2024
#
###############################################################################
import os

import discord
import requests
import json
import logging

from utils.add_requests import AddRequestsForm
from utils.login import Login
from utils.pickup import PickUpModal, PickUpSelectView
from utils.utils import reformat_list_strings
from utils.defines import API_HOST, UPDATE_REQUESTS_ROUTE, ADD_ASSOCIATION_ROUTE, LOGIN_ROUTE, PER_PAGE, CATEGORY, \
                            PICKUP_GET_ROUTE, PICKUP_POST_ROUTE


def define_commands(client, port) -> None:
    """
    Small function adding all the slash commands to the bot.
    :param client: discord.Client, our bot
    :param port: int, API port to use
    :return: None
    """

    @client.tree.command(name="add_request", description="Ajout d'une nouvelle recherche de vêtements")
    async def add_request(interaction: discord.Interaction) -> None:
        """
        Add a new clothe request and run it in background.
        :param interaction: discord.Interaction
        :return: None
        """

        logging.info(f"Adding new clothe request by user: {interaction.user} (id: {interaction.user.id})")

        add_requests_form = AddRequestsForm()
        await interaction.response.send_modal(add_requests_form)
        await add_requests_form.wait()

        # Get info
        name = add_requests_form.name.value
        channel_name = add_requests_form.channel_name.value
        search_text = add_requests_form.search_test.value
        price_from = add_requests_form.price_from.value
        price_to = add_requests_form.price_to.value
        brand = add_requests_form.brand.values[0]
        clothes_states = add_requests_form.clothes_states

        # Reformat clothes_states
        clothes_states = reformat_list_strings(clothes_states)

        # Build dict to be sent to the API
        request = {
            "name": name,
            "per_page": PER_PAGE,
            "search_text": search_text,
            "brand_ids": brand,
            "price_from": price_from,
            "price_to": price_to,
            "status_ids": clothes_states
        }

        logging.info(f"Attempting insertion of request: {request}")

        try:
            # Attempt the request save
            save_request = requests.post(f"{API_HOST}:{port}/{UPDATE_REQUESTS_ROUTE}",
                                         data=json.dumps({"added": [request]}))

            # Success
            if save_request.status_code == 200:
                # Get request inserted id
                inserted_id = json.loads(save_request.json()["data"])["added"][0]

                logging.info(f"Success - request {request} successfully inserted in DBi (inserted id: {inserted_id})")

                # Create new channel
                guild = client.guilds[0]
                channel = await guild.create_text_channel(channel_name,
                                                          category=discord.utils.get(guild.categories, name=CATEGORY))

                # Associate request id and channel id
                association = {"request_id": inserted_id,
                               "request_name": name,
                               "channel_id": channel.id,
                               "channel_name": channel.name}

                logging.info(f"Corresponding association: {association} (request: {request})")

                logging.info(f"Attempting insertion of association: {association}")

                # Call the API to insert the association
                add_association = requests.post(f"{API_HOST}:{port}/{ADD_ASSOCIATION_ROUTE}",
                                                data=json.dumps(association))

                # Health check and run task
                if add_association.status_code == 200:
                    await interaction.followup.send(f"✅ Insertion réussie !\nRecherche: {request}\n"
                                                    f"Association: {association}", ephemeral=True)
                    await client.logs_channel.send(f"✅ Insertion réussie !\nRecherche: {request}\n"
                                                    f"Association: {association}")

                    logging.info(f"Success - association {association} successfully inserted in DB (request {request})")

                    # Check if main loop is running and send custom message
                    if client.task:
                        # Final step: run the task - add to requests dict to be stoppable
                        request["_id"] = inserted_id
                        client.requests[inserted_id] = request
                        client.channels[inserted_id] = channel

                        logging.info(f"Running task for channel: {channel}, request: {request}")
                        await interaction.followup.send(f"✅ Recherche: {request}, association: {association} tourne désormais "
                                                        f"en tâche de fond.", ephemeral=True)

                    else:
                        logging.info(f"Main loop is off. Request: {request}, channel: {channel} registered but not "
                                     f"running yet.")
                        await interaction.followup.send(f"ℹ️ La boucle principale est arrêtée. Veuillez lancer "
                                                        f"les recherches (avec /start_requests) pour appliquer les "
                                                        f"modifications.", ephemeral=True)

                else:
                    error_code = 2
                    logging.error(f"Could not insert association: {association} in DB (displayed error code "
                                  f"[{error_code}])")
                    await interaction.followup.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                                    f"de données, veuillez réessayer. [{error_code}]", ephemeral=True)
                    await client.logs_channel.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                                    f"de données, veuillez réessayer. [{error_code}]")

            else:
                error_code = 1
                logging.error(f"Could not insert request: {request} in DB (displayed error code [{error_code}])")
                await interaction.followup.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                                f"de données, veuillez réessayer. [{error_code}]", ephemeral=True)
                await client.logs_channel.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                                f"de données, veuillez réessayer. [{error_code}]")

        except Exception as e:
            error_code = 3
            logging.error(f"There was an exception while saving request {request} in DB: {e}")
            logging.error(f"Displayed error code [{error_code}]")
            await interaction.followup.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                            f"de données, veuillez réessayer. [{error_code}]", ephemeral=True)
            await client.logs_channel.send("⚠️ Il y a eu un souci avec l'insertion dans la base "
                                            f"de données, veuillez réessayer. [{error_code}]")


    @client.tree.command(name="get_running_requests", description="Voir les recherches en cours")
    async def get_running_requests(interaction: discord.Interaction) -> None:
        """
        Small command showing all the current clothes requests running
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        await interaction.response.defer()

        logging.info(f"Getting all running requests (user: {interaction.user}, user_id: {interaction.user.id})")

        msg = ""

        for request, channel in zip(client.requests.values(), client.channels.values()):
            channel_name = channel.name
            msg += f"ℹ️ Nom de salon: {channel_name}, nom de recherche: {request['name']}\n"

        if not msg:
            msg = "ℹ️ Aucune recherche active."

        logging.info(f"Msg: {msg}")

        await interaction.followup.send(msg)

    @client.tree.command(name="hello", description="Check si bot vivant")
    async def hello(interaction: discord.Interaction) -> None:
        """
        Small ping to bot to check whether he's alive or not.
        :param interaction: discord.Interaction
        :return: None
        """
        logging.info(f"Hello! (user: {interaction.user}, user_id: {interaction.user.id})")
        await interaction.response.send_message("Hello !", ephemeral=True)

    @client.tree.command(name="start_requests", description="Démarre toutes les recherches")
    async def start_requests(interaction: discord.Interaction) -> None:
        """
        Starts all the requests
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        logging.info(f"Starting all requests - user: {interaction.user} (user_id: {interaction.user.id})")
        await interaction.response.defer()

        if not client.task:
            await client.setup_hook()
            await interaction.followup.send("✅ Toutes les recherches sont lancées.")

            logging.info("All requests started successfully")

        else:
            await interaction.followup.send("ℹ️ Les recherches sont déjà lancées.")

    @client.tree.command(name="stop_requests", description="Arrête toutes les recherches")
    async def stop_requests(interaction: discord.Interaction) -> None:
        """
        Stops all the requests
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        logging.info(f"Stopping all requests - user: {interaction.user} (user_id: {interaction.user.id})")

        await interaction.response.defer()

        # Reset dicts and task
        client.reset_global_task()

        await interaction.followup.send("✅ Toutes les recherches sont arrêtées.")

    @client.tree.command(name="login", description="Se connecter à Vinted")
    async def login(interaction: discord.Interaction) -> None:
        """
        Login using Bearer token
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        logging.info(f"Login - user: {interaction.user} (user_id: {interaction.user.id})")

        login_form = Login()
        await interaction.response.send_modal(login_form)
        await login_form.wait()

        # Get bearer
        bearer = login_form.bearer.value

        # Build dict to be sent to the API
        request = {
            "bearer": bearer
        }

        logging.info("Attempting to log in")

        try:
            # Attempt the request save
            save_request = requests.post(f"{API_HOST}:{port}/{LOGIN_ROUTE}",
                                         data=json.dumps(request))

            if save_request.status_code == 200:
                await interaction.followup.send("✅ Login réussi !", ephemeral=True)
                await client.logs_channel.send("✅ Login réussi !")
                logging.info("Successfully logged in using bearer")

            else:
                code = save_request.status_code

                error_code = 10 if code == 500 else 11 if code == 501 else 12 if code == 502 else 13
                logging.error(f"Could not log in (displayed error code [{error_code}])")
                await interaction.followup.send("⚠️ Il y a eu un souci avec le login, veuillez réessayer. "
                                                f"[{error_code}]", ephemeral=True)
                await client.logs_channel.send("⚠️ Il y a eu un souci avec le login, veuillez réessayer. "
                                                f"[{error_code}]")

        except Exception as e:
            error_code = 9
            logging.error(f"There was an exception while logging in: {e}")
            logging.error(f"Displayed error code [{error_code}]")
            await interaction.followup.send("⚠️ Il y a eu un souci avec la connexion à Vinted, "
                                            f"veuillez réessayer. [{error_code}]", ephemeral=True)
            await client.logs_channel.send("⚠️ Il y a eu un souci avec la connexion à Vinted, "
                                            f"veuillez réessayer. [{error_code}]")

    @client.tree.command(name="pickup", description="Choix des points relais")
    async def pickup(interaction: discord.Interaction) -> None:
        """
        Choose pickup points
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        logging.info(f"Pickup - user: {interaction.user} (user_id: {interaction.user.id})")

        pickup_form = PickUpModal()
        await interaction.response.send_modal(pickup_form)
        await pickup_form.wait()

        # Get variables
        number = pickup_form.number.value
        street = pickup_form.street.value
        zipcode = pickup_form.zipcode.value
        city = pickup_form.city.value
        country = pickup_form.country.value

        # Format API input
        request = {
            "number": number,
            "street": street,
            "zipcode": zipcode,
            "city": city,
            "country": country
        }

        logging.info("Getting closest pickup points")

        try:
            get_pickup = requests.get(f"{API_HOST}:{port}/{PICKUP_GET_ROUTE}",
                                      data=json.dumps(request))

            if get_pickup.status_code == 200:

                user_misc = json.loads(get_pickup.json()["data"])["user_misc"]
                col = json.loads(get_pickup.json()["data"])["col"]
                mon = json.loads(get_pickup.json()["data"])["mon"]

                logging.info(f"Received col pickups: {col}")
                logging.info(f"Received mon pickups: {mon}")

                pickup_view = PickUpSelectView(col, mon)
                await interaction.followup.send(view=pickup_view)
                await pickup_view.wait()

                # Get results
                col_chosen = col[int(pickup_view.col_chosen)]
                mon_chosen = mon[int(pickup_view.mon_chosen)]

                logging.info(f"Pickup chosen (col): {col_chosen}")
                logging.info(f"Pickup chosen (mon): {mon_chosen}")

                # Save pickup points
                request = {"col": col_chosen,
                           "mon": mon_chosen,
                           "user_position": user_misc}

                save_pickup = requests.post(f"{API_HOST}:{port}/{PICKUP_POST_ROUTE}",
                                           data=json.dumps(request))

                if save_pickup.status_code == 200:
                    await interaction.followup.send("✅ Enregistrement des points relais réussi !", ephemeral=True)
                    await client.logs_channel.send("✅ Enregistrement des points relais réussi !")
                    logging.info("Successfully saved pickup points")

                else:
                    error_code = 17
                    logging.error(f"There was an exception while saving pickup points: {e}")
                    logging.error(f"Displayed error code [{error_code}]")
                    await interaction.followup.send("⚠️ Il y a eu un souci avec les points relais, "
                                                    f"veuillez réessayer. [{error_code}]", ephemeral=True)
                    await client.logs_channel.send("⚠️ Il y a eu un souci avec les points relais, "
                                                   f"veuillez réessayer. [{error_code}]")

            else:
                code = get_pickup.status_code

                error_code = 15 if code == 501 else 16
                logging.error(f"Could not get pickup points (displayed error code [{error_code}])")
                await interaction.followup.send("⚠️ Il y a eu un souci avec les points relais, veuillez réessayer. "
                                                f"[{error_code}]", ephemeral=True)
                await client.logs_channel.send("⚠️ Il y a eu un souci avec les points relais, veuillez réessayer. "
                                               f"[{error_code}]")

        except Exception as e:
            error_code = 14
            logging.error(f"There was an exception while getting pickup points: {e}")
            logging.error(f"Displayed error code [{error_code}]")
            await interaction.followup.send("⚠️ Il y a eu un souci avec les points relais, "
                                            f"veuillez réessayer. [{error_code}]", ephemeral=True)
            await client.logs_channel.send("⚠️ Il y a eu un souci avec les points relais, "
                                           f"veuillez réessayer. [{error_code}]")



    @client.tree.command(name="sync", description="Admin seulement")
    async def sync(interaction: discord.Interaction) -> None:
        """
        Sync slash commands.
        :param interaction: discord.Interaction
        :return: None
        """
        if interaction.user.id == int(os.getenv("NEEKO_ID")):
            logging.info(f"Neeko syncing command tree")
            await interaction.response.defer()
            await client.tree.sync()
            logging.info('Command tree synced')
            await interaction.followup.send("✅ Sync done.", ephemeral=True)
        else:
            logging.warning(f"Command tree sync attempted by user: {interaction.user} (user_id: {interaction.user.id})")
            await interaction.response.send_message("⚠️ Vous n'êtes pas Neeko (:",
                                                    ephemeral=True)
