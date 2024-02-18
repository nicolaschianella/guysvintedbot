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


class PickUpModal(discord.ui.Modal,
            title="Adresse actuelle"):
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


class PickUpSelectView(discord.ui.View):
    """
    Represents the view of the pickup points selection
    """
    def __init__(self, col_list, mon_list) -> None:
        """
        Adds first selector to view, parses attributes
        Args:
            col_list: list, list of found colissimo pickup points
            mon_list: list, list of found mondial pickup points
        """
        super().__init__()
        self.col_list = col_list
        self.mon_list = mon_list
        self.col_chosen = None
        self.mon_chosen = None
        self.add_item(ColissimoSelect(self.col_list))

    async def display_mondial(self,
                              interaction: discord.Interaction) -> None:
        """
        Called when the colissimo pickup points selector is closed
        Deactivates it and displays the mondial pickup points selector
        Returns: None

        """
        try:
            # Disable the selector
            self.children[0].disabled = True
            # Add the mondial one
            self.add_item(MondialSelect(self.mon_list))
            await interaction.message.edit(view=self)
            await interaction.response.defer()

        except Exception as e:
            await notify_something_went_wrong("PickUpSelectView",
                                              "display_mondial",
                                              14,
                                              e,
                                              interaction)

    async def close_view(self, interaction: discord.Interaction) -> None:
        """
        Closes the view
        Args:
            interaction: discord.Interaction

        Returns:

        """
        try:
            # Disable second selector
            self.children[1].disabled = True
            await interaction.message.edit(view=self)
            await interaction.response.defer()
            # Clear everything
            self.clear_items()
            self.stop()

            await interaction.message.edit(view=self,
                                           content="Insertion dans la base de données en cours...",
                                           delete_after=5)

        except Exception as e:
            await notify_something_went_wrong("PickUpSelectView",
                                              "close_view",
                                              15,
                                              e,
                                              interaction)


class PickUpSelect(discord.ui.Select):
    """
    Abstract class representing pickup points selection
    """
    def __init__(self, pickup_list, name):
        """
        Represents the pickup points selector
        Args:
            pickup_list: list, list of found pickup points
            name: str, name of the service provider
        """
        # Generate options based on pickup_list
        options = [discord.SelectOption(label=pickup["user_display"], value=index) for (index, pickup)
                   in enumerate(pickup_list)]
        super().__init__(placeholder=f"Point relais {name}",
                         max_values=1,
                         min_values=1,
                         options=options)


class ColissimoSelect(PickUpSelect):
    def __init__(self, col_list, name="Chronopost") -> None:
        """
        Represents the colissimo pickup points selector
        Args:
            col_list: list, list of found colissimo pickup points
        """
        super().__init__(col_list, name)

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Called when colissimo pickup points selector is closed
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        try:
            self.view.col_chosen = self.values[0]
            await self.view.display_mondial(interaction)

        except Exception as e:
            await notify_something_went_wrong("ColissimoSelect",
                                              "callback",
                                              16,
                                              e,
                                              interaction)


class MondialSelect(PickUpSelect):
    def __init__(self, mon_list) -> None:
        """
        Represents the mondial pickup points selector
        Args:
            mon_list: list, list of found mondial pickup points
        """
        super().__init__(mon_list, name="Mondial")

    async def callback(self, interaction: discord.Interaction) -> None:
        """
        Called when mondial pickup points selector is closed
        Args:
            interaction: discord.Interaction

        Returns: None

        """
        try:
            self.view.mon_chosen = self.values[0]
            await self.view.close_view(interaction)

        except Exception as e:
            await notify_something_went_wrong("MondialSelect",
                                              "callback",
                                              17,
                                              e,
                                              interaction)
