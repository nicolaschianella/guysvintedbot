###############################################################################
#
# File:      login.py
# Author(s): Nico
# Scope:     Login modal
#
# Created:   16 February 2024
#
###############################################################################
import discord

from utils.utils import notify_something_went_wrong


class Login(discord.ui.Modal,
            title="Connexion à Vinted"):
    """
    Represents the form sent to the user to log in
    """

    # Bearer
    bearer = discord.ui.TextInput(
        label="Token",
        placeholder="eyJraWQiOiJFNTdZZHJ1SHBsQWp1MmNObzFEb3JIM2oyN0J1NS1zX09QNVB3UGlobjVNIiwiYWxnIjoiUFMyNTYifQ.eyJhcHB"
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
            await notify_something_went_wrong("Login",
                                              "on_submit",
                                              10,
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
        await notify_something_went_wrong("Login",
                                          "on_error",
                                          11,
                                          e,
                                          interaction)
