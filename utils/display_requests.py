###############################################################################
#
# File:      display_requests.py
# Author(s): Nico
# Scope:     The buttons to show details or buy clothes
#
# Created:   07 February 2024
#
###############################################################################
import logging
import discord
import requests
import json

from utils.defines import API_HOST, ADD_CLOTHE_IN_STOCK_ROUTE


class BuyButtons(discord.ui.View):
    """
    Represents buttons to show details, buy clothes or not pertinent
    """
    def __init__(self,
                 request_id: str,
                 clothe: dict,
                 embeds: list[discord.Embed],
                 ratio: int,
                 logs_channel: discord.TextChannel,
                 stock_channel: discord.TextChannel,
                 port: int) -> None:
        """
        Inits the 'Détails' buttons in a view and parses attributes to enable 'AutoBuy' to work
        Args:
            request_id: str, request id in our DB used to find this clothe
            clothe: dict, clothe dict
            embeds: list[discord.Embed], list of embeds to post in the stock channel (when autobuy button is pressed)
            ratio: int, fuzz ratio
            logs_channel: discord.TextChannel, channel to post in if "Non pertinent" is pressed
            stock_channel: discord.TextChannel, channel to post in when autobuy button is pressed
            port: int, API port to use
        """
        super().__init__()
        self.request_id = request_id
        self.clothe = clothe
        self.embeds = embeds
        self.ratio = ratio
        self.logs_channel = logs_channel
        self.stock_channel = stock_channel
        self.port = port
        # Add "Détails" button
        self.add_item(discord.ui.Button(label="Détails", url=self.clothe["url"]))

    @discord.ui.button(label="✅ AutoBuy", style=discord.ButtonStyle.blurple)
    async def autobuy(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        'AutoBuy' button
        Performs autobuy action
        Args:
            interaction: discord.Interaction
            button: button: discord.ui.Button

        Returns: None

        """
        await interaction.response.defer()

        logging.info(f"Processing autobuy for clothe: {self.clothe}")

        # TODO: here add check if clothe already in stock
        # TODO: here add autobuy
        bought = True  # change with API response for autobuy

        # Case purchase OK
        if bought:
            # Add missing keys
            self.clothe["request_id"] = self.request_id
            self.clothe["clothe_id"] = self.clothe["id"]
            self.clothe["ratio"] = self.ratio

            # Register clothe in stock through the API
            add_in_stock = requests.post(f"{API_HOST}:{self.port}/{ADD_CLOTHE_IN_STOCK_ROUTE}",
                                         data=json.dumps(self.clothe))

            # Article already in stock? (duplicate clothe_id?) - notify the user and post in logs channel
            if add_in_stock.status_code == 501:
                logging.warning(f"Clothe already in stock (id: {self.clothe['id']})")
                await interaction.followup.send(f"⚠️ [CRITIQUE] Vêtement déjà en stock: (nom: {self.clothe['title']}, "
                                                f"url: {self.clothe['url']})", ephemeral=True)
                await self.logs_channel.send(f"⚠️ [CRITIQUE] Vêtement déjà en stock: (nom: {self.clothe['title']}, "
                                                f"url: {self.clothe['url']})")

            # Status OK - post in channels
            elif add_in_stock.status_code == 200:
                logging.info(f"Successfully added clothe to stock (id: {self.clothe['id']})")

                await interaction.followup.send(f"✅ Achat bien effectué: {self.clothe['title']}", ephemeral=True)
                await self.logs_channel.send(f"✅ Vêtement mis en stock: (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}, url: {self.clothe['url']})")
                await self.stock_channel.send(embeds=self.embeds,
                                              view=StockButtons(clothe_id=self.clothe["id"],
                                                                port=self.port))

            # Status not OK - issue with the API, post in logs channel
            else:
                logging.error(f"Could not add clothe to DB: {self.clothe}. Full response: {add_in_stock.text}")

                await interaction.followup.send(f"⚠️ Vêtement bien acheté (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}) mais non mis en stock.", ephemeral=True)
                await self.logs_channel.send(f"⚠️ Vêtement bien acheté (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}) mais non mis en stock.")

        # Case purchase gone wrong
        else:
            # TODO: if doesn't work, logs + write in log_channel and ephemeral for user
            pass

    @discord.ui.button(label="Non pertinent", style=discord.ButtonStyle.red)
    async def not_pertinent(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        """
        'Non pertinent' button
        Adds fuzz ratio to log file for non pertinent items. Also posts result in logs channel
        Args:
            interaction: discord.Interaction
            button: button: discord.ui.Button

        Returns: None

        """
        await interaction.response.defer()

        logging.warning(f"Bad fuzz ratio: {self.ratio}")

        await interaction.followup.send("Merci du feedback !", ephemeral=True)
        await self.logs_channel.send(f"ℹ️ Fuzz ratio non pertinent: {self.ratio}")


class StockButtons(discord.ui.View):
    def __init__(self, clothe_id, port: int):
        """
        Represents buttons in stock - to cancel purchase or to change clothe state to "sold"
        Args:
            clothe_id: Union[str, int], Vinted clothe id
            port: int, API port to use
        """
        self.clothe_id = clothe_id
        self.port = port
        super().__init__(timeout=None)
        self.display_stock_buttons()

    def display_stock_buttons(self):
        """
        Adds "Vendu" and "Supprimer" buttons, to either sell or delete clothe in stock.
        Defines their respective callbacks
        Returns: None

        """
        async def sold(interaction: discord.Interaction):
            """
            Performs sell operation
            Args:
                interaction: discord.Iteraction

            Returns: None

            """
            # TODO: pop-up and register sale in DB
            await interaction.response.send_message(f'Sell: {self.clothe_id}', ephemeral=True)

        async def delete(interaction: discord.Interaction):
            """
            Performs delete operation
            Args:
                interaction: discord.Iteraction

            Returns: None

            """
            # TODO: confirmation button and delete from DB
            await interaction.response.send_message(f'Delete: {self.clothe_id}', ephemeral=True)

        # "Vendu"
        sold_button = discord.ui.Button(label="✅ Vendu",
                                        style=discord.ButtonStyle.green,
                                        custom_id=f"{self.clothe_id}:sold")
        sold_button.callback = sold
        self.add_item(sold_button)

        # "Supprimer"
        delete_button = discord.ui.Button(label="⚠️ Supprimer",
                                          style=discord.ButtonStyle.red,
                                          custom_id=f"{self.clothe_id}:delete")
        delete_button.callback = delete
        self.add_item(delete_button)
