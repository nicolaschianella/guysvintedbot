###############################################################################
#
# File:      buttons.py
# Author(s): Nico
# Scope:     The buttons to show details, buy clothes and manage stock
#
# Created:   07 February 2024
#
###############################################################################
import logging
import discord
import requests
import json

from utils.defines import API_HOST, ADD_CLOTHE_IN_STOCK_ROUTE, GET_CLOTHES_FROM_STOCK_ROUTE, SELL_CLOTHES_ROUTE, \
    DELETE_CLOTHES_ROUTE, AUTOBUY_ROUTE
from utils.utils import notify_something_went_wrong
from utils.stock_views import SellClotheView, DeleteClotheView
from typing import Union


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
        super().__init__(timeout=None)
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
        try:
            await interaction.response.defer()

            # Check if clothe in stock already
            clothes_in_stock = requests.get(f"{API_HOST}:{self.port}/{GET_CLOTHES_FROM_STOCK_ROUTE}",
                                            data=json.dumps({"which": "in_stock"}))

            if clothes_in_stock.status_code == 200:
                stock_clothes = json.loads(clothes_in_stock.json()["data"])["found_clothes"]
                clothes_ids = [clothe["clothe_id"] for clothe in stock_clothes]

                # Case clothe already in stock
                if str(self.clothe["id"]) in clothes_ids:
                    logging.warning(f"Clothe already in stock (id: {self.clothe['id']})")

                    await interaction.followup.send(f"ℹ️ Vêtement déjà en stock: (nom: {self.clothe['title']}, "
                                                    f"url: {self.clothe['url']})", ephemeral=True)

                    return

            else:
                # Case API error
                error_code = 18
                logging.error(f"Error getting clothes from stock, full response: {clothes_in_stock.text}")
                logging.error(f"Displayed error code [{error_code}]")

                await interaction.followup.send(f"⚠️ Vêtement non acheté (id: {self.clothe['id']}, "
                                                f"nom: {self.clothe['title']}) car erreur du programme [{error_code}]",
                                                ephemeral=True)
                await self.logs_channel.send(f"⚠️ Vêtement non acheté (id: {self.clothe['id']}, "
                                                f"nom: {self.clothe['title']}) car erreur du programme [{error_code}]")
                return

            logging.info(f"Processing autobuy for clothe: {self.clothe}")

            request = {"item_id": self.clothe["id"],
                       "seller_id": self.clothe["seller_id"],
                       "item_url": self.clothe["url"]}

            autobuy = requests.post(f"{API_HOST}:{self.port}/{AUTOBUY_ROUTE}", data=json.dumps(request))

            if autobuy.status_code != 200:
                # Case item already bought
                if autobuy.status_code == 501:
                    logging.warning(f"Clothe already sold:")
                    await interaction.followup.send(f"ℹ️ Vêtement déjà vendu: (id: {self.clothe['id']}, "
                                                 f"nom: {self.clothe['title']}, url: {self.clothe['url']})",
                                                    ephemeral=True)
                    return

                # Case error
                else:
                    error_code = 19
                    logging.error(f"Could not autobuy clothe: {self.clothe}. Full response: {autobuy.text}")
                    logging.error(f"Displayed error code [{error_code}]")

                    await interaction.followup.send(f"⚠️ Vêtement non acheté (id: {self.clothe['id']}, "
                                                    f"nom: {self.clothe['title']}) car erreur du programme: "
                                                    f"{autobuy.json()['message']} [{error_code}]",
                                                    ephemeral=True)
                    await self.logs_channel.send(f"⚠️ Vêtement non acheté (id: {self.clothe['id']}, "
                                                 f"nom: {self.clothe['title']}) car erreur du programme: "
                                                 f"{autobuy.json()['message']} [{error_code}]")
                    return

            logging.info(f"Autobuy OK, inserting clothe in DB (id: {self.clothe['id']})")

            # Case purchase OK
            # Add missing keys
            self.clothe["request_id"] = self.request_id
            self.clothe["clothe_id"] = self.clothe["id"]
            self.clothe["ratio"] = self.ratio

            # Register clothe in stock through the API
            add_in_stock = requests.post(f"{API_HOST}:{self.port}/{ADD_CLOTHE_IN_STOCK_ROUTE}",
                                         data=json.dumps(self.clothe))

            # Status OK - post in channels
            if add_in_stock.status_code == 200:
                logging.info(f"Successfully added clothe to stock (id: {self.clothe['id']})")

                await interaction.followup.send(f"✅ Achat bien effectué: {self.clothe['title']}", ephemeral=True)
                await self.logs_channel.send(f"✅ Vêtement mis en stock: (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}, url: {self.clothe['url']})")
                await self.stock_channel.send(embeds=self.embeds,
                                              view=StockButtons(clothe_id=self.clothe["id"],
                                                                port=self.port,
                                                                logs_channel=self.logs_channel))

            # Status not OK - issue with the API, post in logs channel
            else:
                error_code = 20
                logging.error(f"Could not add clothe to DB: {self.clothe}. Full response: {add_in_stock.text}")
                logging.error(f"Displayed error code [{error_code}]")

                await interaction.followup.send(f"⚠️ Vêtement bien acheté (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}) mais non mis en stock [{error_code}]",
                                                ephemeral=True)
                await self.logs_channel.send(f"⚠️ Vêtement bien acheté (id: {self.clothe['id']}, "
                                             f"nom: {self.clothe['title']}) mais non mis en stock [{error_code}]")

        except Exception as e:
            error_code = 4
            logging.error(f"There was an exception while buying clothe {self.clothe}: {e}")
            logging.error(f"Displayed error code [{error_code}]")
            await interaction.followup.send(f"⚠️ Il y a eu un souci avec l'achat du vêtement (id: {self.clothe['id']}, "
                                                 f"nom: {self.clothe['title']}, url: {self.clothe['url']}), veuillez "
                                            f"réessayer. [{error_code}]", ephemeral=True)
            await self.logs_channel.send(f"⚠️ Il y a eu un souci avec l'achat du vêtement (id: {self.clothe['id']}, "
                                                 f"nom: {self.clothe['title']}, url: {self.clothe['url']}), veuillez "
                                            f"réessayer. [{error_code}]")

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
        try:
            await interaction.response.defer()

            logging.warning(f"Bad fuzz ratio: {self.ratio}")

            await interaction.followup.send("Merci du feedback !", ephemeral=True)
            await self.logs_channel.send(f"ℹ️ Fuzz ratio non pertinent: {self.ratio}")

        except Exception as e:
            await notify_something_went_wrong("BuyButtons",
                                              "not_pertinent",
                                              5,
                                              e,
                                              interaction)


class StockButtons(discord.ui.View):
    def __init__(self, clothe_id: Union[str, int], port: int, logs_channel: discord.TextChannel):
        """
        Represents buttons in stock - to cancel purchase or to change clothe state to "sold"
        Args:
            clothe_id: Union[str, int], Vinted clothe id
            port: int, API port to use
            logs_channel: discord.TextChannel, lohs channel to post in
        """
        self.clothe_id = clothe_id
        self.port = port
        self.logs_channel = logs_channel
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
            sell_clothes_form = SellClotheView()
            await interaction.response.send_modal(sell_clothes_form)
            await sell_clothes_form.wait()

            sale_date, selling_price = sell_clothes_form.sale_date.value, sell_clothes_form.selling_price.value

            # Register sale
            try:
                sell_clothes = requests.post(f"{API_HOST}:{self.port}/{SELL_CLOTHES_ROUTE}",
                                             data=json.dumps({"clothe_id": str(self.clothe_id),
                                                              "sale_date": sale_date,
                                                              "selling_price": selling_price}))

                if sell_clothes.status_code == 200:
                    logging.info(f"Successfully registered clothe as sold: (id: {self.clothe_id}, "
                                                 f"selling_price: {selling_price}€, "
                                                 f"sale_date: {sale_date})")
                    await interaction.followup.send(f"✅ Vente bien enregistrée: {self.clothe_id}", ephemeral=True)
                    await self.logs_channel.send(f"✅ Vêtement vendu: (id: {self.clothe_id}, "
                                                 f"prix de vente: {selling_price}€, "
                                                 f"date de vente: {sale_date})")

                    # Delete the stock entry
                    await interaction.message.delete()

                elif sell_clothes.status_code == 501:
                    logging.warning(f"Bad date format: {sale_date}, full API response: {sell_clothes.text}")
                    await interaction.followup.send(f"ℹ️ Vente non enregistrée: {self.clothe_id}, car la date "
                                                    f"n'est pas au bon format.", ephemeral=True)

                else:
                    error_code = 6
                    logging.error(f"There was an issue while registering clothe as sold {self.clothe_id}")
                    logging.error(f"Displayed error code [{error_code}]")
                    await interaction.followup.send(
                        f"⚠️ Il y a eu un souci avec la vente du vêtement (id: {self.clothe_id}), veuillez "
                        f"réessayer. [{error_code}]", ephemeral=True)
                    await self.logs_channel.send(
                        f"⚠️ Il y a eu un souci avec la vente du vêtement (id: {self.clothe_id}), veuillez "
                        f"réessayer. [{error_code}]")

            except Exception as e:
                error_code = 5
                logging.error(f"There was an exception while registering clothe as sold {self.clothe_id}: {e}")
                logging.error(f"Displayed error code [{error_code}]")
                await interaction.followup.send(
                    f"⚠️ Il y a eu un souci avec la vente du vêtement (id: {self.clothe_id}), veuillez "
                    f"réessayer. [{error_code}]", ephemeral=True)
                await self.logs_channel.send(
                    f"⚠️ Il y a eu un souci avec la vente du vêtement (id: {self.clothe_id}), veuillez "
                    f"réessayer. [{error_code}]")

        async def delete(interaction: discord.Interaction):
            """
            Performs delete operation
            Args:
                interaction: discord.Iteraction

            Returns: None

            """
            delete_clothes_form = DeleteClotheView()
            await interaction.response.send_modal(delete_clothes_form)
            await delete_clothes_form.wait()

            deletion_confirmation = delete_clothes_form.deletion_confirmation.value

            # Check confirmation validity
            if deletion_confirmation.lower() != "oui":
                logging.warning(f"Confirmation undone - skipping clothe deletion: {self.clothe_id}")
                await interaction.followup.send(f"ℹ️ Suppression non effectuée: {self.clothe_id}", ephemeral=True)
                return

            # Else we delete the item in stock
            try:
                delete_clothes = requests.post(f"{API_HOST}:{self.port}/{DELETE_CLOTHES_ROUTE}",
                                               data=json.dumps({"clothe_id": str(self.clothe_id)}))

                if delete_clothes.status_code == 200:
                    logging.info(f"Successfully deleted clothe from stock: (id: {self.clothe_id})")
                    await interaction.followup.send(f"✅ Suppression du vêtement effectuée: {self.clothe_id}",
                                                    ephemeral=True)
                    await self.logs_channel.send(f"✅ Suppression du vêtement effectuée: {self.clothe_id}")

                    # Delete the stock entry
                    await interaction.message.delete()

                else:
                    error_code = 7
                    logging.error(f"There was an issue while deleting clothe from stock {self.clothe_id}")
                    logging.error(f"Displayed error code [{error_code}]")
                    await interaction.followup.send(
                        f"⚠️ Il y a eu un souci avec la suppression du vêtement du stock (id: {self.clothe_id}), "
                        f"veuillez réessayer. [{error_code}]", ephemeral=True)
                    await self.logs_channel.send(f"⚠️ Il y a eu un souci avec la suppression du vêtement du stock "
                                                 f"(id: {self.clothe_id}), veuillez réessayer. [{error_code}]")

            except Exception as e:
                error_code = 8
                logging.error(f"There was an exception while deleting clothe from stock {self.clothe_id}: {e}")
                logging.error(f"Displayed error code [{error_code}]")
                await interaction.followup.send(
                    f"⚠️ Il y a eu un souci avec la suppression du vêtement du stock (id: {self.clothe_id}), "
                    f"veuillez réessayer. [{error_code}]", ephemeral=True)
                await self.logs_channel.send(f"⚠️ Il y a eu un souci avec la suppression du vêtement du stock "
                                             f"(id: {self.clothe_id}), veuillez réessayer. [{error_code}]")

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
