###############################################################################
#
# File:      add_requests.py
# Author(s): Nico
# Scope:     Resources needed for the /add_requests command
#
# Created:   07 February 2024
#
###############################################################################
import discord
from utils.defines import BRANDS, CLOTHES_STATES


class AddRequestsForm(discord.ui.Modal,
                      title="Ajout d'une recherche de vêtements"):
    """
    Represents the form sent to the user to add a clothe request - at least for text elements.
    """

    # Clothe request name
    name = discord.ui.TextInput(
        label="Nom de la recherche",
        placeholder="Ex: écharpe Burberry"
    )
    # Name of channel to create
    channel_name = discord.ui.TextInput(
        label="Nom du salon à créer pour poster",
        placeholder="Ex: 🧣Burberry"
    )
    # Clothe request search text
    search_test = discord.ui.TextInput(
        label="Mots clés de la recherche",
        placeholder="Ex: écharpe",
        required=False
    )
    # Minimal price to filter on
    price_from = discord.ui.TextInput(
        label="Prix minimum [€] - hors fees",
        placeholder="Ex: 0",
        required=False
    )
    # Maximal price to filter on
    # Minimal price to filter on
    price_to = discord.ui.TextInput(
        label="Prix maximum [€] - hors fees",
        placeholder="Ex: 100",
        required=False
    )
    # Filtered brand
    brand = None
    # Filtered clothes_states
    clothes_states = None
    # Indicating if the process was OK
    sent = False

    # Called when form is sent
    async def on_submit(self,
                        interaction: discord.Interaction) -> None:
        """
        Called when the user submits the form. Calls the selectors.
        :param interaction: discord.Interaction
        :return: None
        """
        # Call the selectors
        select_view = BrandStateSelectView()
        await interaction.response.send_message(view=select_view)
        await select_view.wait()
        # Get the variables
        self.brand, self.clothes_states = select_view.brand, select_view.clothes_states
        # Process OK
        self.sent = True

    # Called if error of any kind
    async def on_error(self,
                       interaction: discord.Interaction,
                       error: Exception) -> None:
        """
        Called when something when wrong in the form. Notifies the user.
        :param interaction: discord.Interaction
        :param error: Exception
        :return: None
        """
        # Notify the sender
        await interaction.response.send_message("Oops! Quelque chose s'est mal passé.", ephemeral=True)


class BrandStateSelectView(discord.ui.View):
    """
    Represents the view showing the two selectors - for brands and for clothes states.
    """

    brand = None
    clothes_states = None

    @discord.ui.select(
        placeholder="Sélectionner la marque à filtrer",
        options=[discord.SelectOption(label=brand_name, value=brand_id) for (brand_name, brand_id) in BRANDS.items()]
    )
    async def select_brand(self,
                           interaction: discord.Interaction,
                           select_item: discord.ui.Select):
        """
        Calls the brand selector, and once done, the clothes states selector.
        :param interaction:
        :param select_item:
        :return:
        """
        # Get the filtered brand - already as id
        self.brand = select_item
        # Disable the selector
        self.children[0].disabled = True
        # Now call the clothes states selector and add it to the view
        clothes_states = ClothesStatesSelect()
        self.add_item(clothes_states)
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    async def select_clothes_states(self,
                                 interaction: discord.Interaction,
                                 choices: list):
        """
        Calls the clothes selector
        :param interaction:
        :param choices:
        :return:
        """
        # Get the chosen clothes states
        self.clothes_states = choices
        # Disable the selector
        self.children[1].disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        # Clear everything from the view
        self.clear_items()
        self.stop()

        await interaction.message.edit(view=self,
                                       content="Insertion dans la base de données en cours...",
                                       delete_after=10)


class ClothesStatesSelect(discord.ui.Select):
    """
    Represents the cloths states selector.
    """
    def __init__(self):
        options=[discord.SelectOption(label=state, value=state_id) for (state, state_id) in CLOTHES_STATES.items()]
        super().__init__(options=options, placeholder="Sélectionner les états des vêtements", max_values=len(options))

    async def callback(self, interaction: discord.Interaction):
        await self.view.select_clothes_states(interaction, self.values)
