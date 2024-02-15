###############################################################################
#
# File:      stock_views.py
# Author(s): Nico
# Scope:     Buttons and modal to manage the stock channel
#
# Created:   15 February 2024
#
###############################################################################
import discord

from utils.utils import notify_something_went_wrong


class SellClotheView(discord.ui.Modal,
                     title="Vente d'un vêtement"):
    """
    Represents the form sent to the user to sell an item
    """

    # Date of sale
    sale_date = discord.ui.TextInput(
        label="Date de vente",
        placeholder="JJ-MM-AAAA HH:MM, ex: 07-02-2024 09:03"
    )
    # Selling price
    selling_price = discord.ui.TextInput(
        label="Prix de vente [€]",
        placeholder="Ex: 30"
    )

    # Called when the form is sent
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Called when the user submits the form. Registers sale in DB
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        try:
            # TODO: register sale
            await interaction.response.send_message(f'Prix de vente: {self.selling_price}', ephemeral=True)

        except Exception as e:
            await notify_something_went_wrong("SellClotheView",
                                              "on_submit",
                                              6,
                                              e,
                                              interaction)

    # Called if error of any kind
    async def on_error(self,
                       interaction: discord.Interaction,
                       e: Exception) -> None:
        """
        Called when something when wrong in the form. Notifies the user.
        Args:
            interaction: discord.Interaction
            e: Exception

        Returns: None

        """
        await notify_something_went_wrong("SellClotheView",
                                          "on_error",
                                          7,
                                          e,
                                          interaction)
