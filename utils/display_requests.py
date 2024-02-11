###############################################################################
#
# File:      display_requests.py
# Author(s): Nico
# Scope:     The buttons to show details or buy clothes
#
# Created:   07 February 2024
#
###############################################################################
import discord


class Buttons(discord.ui.View):
    """
    Represents buttons to show details or buy clothes
    """
    def __init__(self, url: str) -> None:
        """
        Inits the 'Détails' buttons in a view and parses attributes to enable 'AutoBuy' to work
        Args:
            url: str, clothe url
            (More to come)
        """
        super().__init__()
        self.url = url
        self.add_item(discord.ui.Button(label="Détails", url=self.url))

    @discord.ui.button(label="✅ AutoBuy", style=discord.ButtonStyle.blurple)
    async def autobuy(self, interaction: discord.Interaction) -> None:
        """
        'AutoBuy' button
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        await interaction.response.defer()

        # TODO: here add autobuy, and if works, save purchase in MongoDB

        await interaction.followup.send(self.url, ephemeral=True)