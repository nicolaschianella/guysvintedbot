###############################################################################
#
# File:      commands.py
# Author(s): Nico
# Scope:     File defining all available bot commands
#
# Created:   07 February 2024
#
###############################################################################
import discord
import requests
import json
from datetime import datetime

from utils.add_requests import AddRequestsForm
from utils.utils import reformat_clothes_states, serialize_datetime
from utils.defines import API_HOST, UPDATE_REQUESTS_ROUTE, ADD_ASSOCIATION_ROUTE, PER_PAGE, CATEGORY


def define_commands(client, port) -> None:
    """
    Small function adding all the slash commands to the bot.
    :param client: discord.Client, our bot
    :param port: int, API port to use
    :return: None
    """

    @client.tree.command()
    async def add_request(interaction: discord.Interaction) -> None:
        """
        Add a new clothe request and run it in background.
        :param interaction: discord.Interaction
        :return: None
        """

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
        clothes_states = reformat_clothes_states(clothes_states)

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

        # Attempt the request save
        save_request = requests.post(f"{API_HOST}:{port}/{UPDATE_REQUESTS_ROUTE}",
                                     data=json.dumps({"added": [request]}))

        # Success
        if save_request.status_code == 200:
            # Get request inserted id
            inserted_id = json.loads(save_request.json()["data"])["added"][0]

            # Create new channel
            guild = client.guilds[0]
            channel = await guild.create_text_channel(channel_name,
                                                      category=discord.utils.get(guild.categories, name=CATEGORY))

            # Associate request id and channel id
            association = {"request_id": inserted_id,
                           "request_name": name,
                           "channel_id": channel.id,
                           "channel_name": channel.name,
                           "creation_date": datetime.now()}

            # Call the API to insert the association
            add_association = requests.post(f"{API_HOST}:{port}/{ADD_ASSOCIATION_ROUTE}",
                                            data=json.dumps(association, default=serialize_datetime))

            # Health check and run task
            if add_association.status_code == 200:
                await interaction.followup.send("Insertion réussie !", ephemeral=True)

                # Final step: run the task
                await client.loop.create_task(client.get_clothes(request, channel.id))

            else:
                await interaction.followup.send("Il y a eu un souci avec l'insertion dans la base "
                                                "de données, veuillez réessayer. [2]", ephemeral=True)

        else:
            await interaction.followup.send("Il y a eu un souci avec l'insertion dans la base "
                                            "de données, veuillez réessayer. [1]", ephemeral=True)
