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


class BuyButtons(discord.ui.View):
    """
    Represents buttons to show details, buy clothes or not pertinent
    """
    def __init__(self, url: str, ratio: int, log_channel: discord.TextChannel) -> None:
        """
        Inits the 'Détails' buttons in a view and parses attributes to enable 'AutoBuy' to work
        Args:
            url: str, clothe url
            ratio: int, fuzz ratio
            log_channel: discord.TextChannel, channel to post if "Non pertinent" is pressed
            (More to come)
        """
        super().__init__()
        self.url = url
        self.ratio = ratio
        self.log_channel = log_channel
        self.add_item(discord.ui.Button(label="Détails", url=self.url))

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

        logging.info(f"Processing autobuy for clothe_url: {self.url}")

        # TODO: here add autobuy, and if works, save purchase in MongoDB + change logs with other inputs

        await interaction.followup.send(self.url, ephemeral=True)

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
        await self.log_channel.send(f"Fuzz ratio non pertinent: {self.ratio}")
