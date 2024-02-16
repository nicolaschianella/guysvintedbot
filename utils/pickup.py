###############################################################################
#
# File:      pickup.py
# Author(s): Nico
# Scope:     Pickup points modal
#
# Created:   16 February 2024
#
###############################################################################
import discord

from utils.utils import notify_something_went_wrong


class PickUp(discord.ui.Modal,
            title="Choix des points relais"):
    """
    Represents the form sent to the user to choose pickup points
    """

    # Number
    number = discord.ui.TextInput(
        label="Numéro",
        placeholder="142"
    )

    # Street
    street = discord.ui.TextInput(
        label="Rue",
        placeholder="Rue Gallieni"
    )

    # Zipcode
    zipcode = discord.ui.TextInput(
        label="Code postal",
        placeholder="92100"
    )

    # City
    city = discord.ui.TextInput(
        label="Ville",
        placeholder="Boulogne-Billancourt"
    )

    # Country
    country = discord.ui.TextInput(
        label="Pays",
        placeholder="France"
    )

    # Called when the form is sent
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Called when the user submits the form.
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        try:
            await interaction.response.defer()

        except Exception as e:
            await notify_something_went_wrong("PickUp",
                                              "on_submit",
                                              12,
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
        await notify_something_went_wrong("PickUp",
                                          "on_error",
                                          13,
                                          e,
                                          interaction)