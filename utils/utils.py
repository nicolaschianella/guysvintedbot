###############################################################################
#
# File:      utils.py
# Author(s): Nico
# Scope:     Utils functions
#
# Created:   07 February 2024
#
###############################################################################
import logging

import discord


def reformat_list_strings(list_strings: list, format_type: str="clothes_states") -> str:
    """
    Reformats a generic list of strings from ['1', '2', ...] to '1,2,...'
    Args:
        list_strings: list of str, list to reformat
        format_type: str, formatted in logs

    Returns: str, concatenated values

    """

    logging.info(f"Received {format_type}: {list_strings}")
    concat_values = ""
    for state in list_strings:
        concat_values += state
        concat_values += ","
    concat_values = concat_values[:-1]

    logging.info(f"Successfully formatted {format_type} to {concat_values}")

    return concat_values


async def notify_something_went_wrong(class_name: str,
                                      method_name: str,
                                      error_code: int,
                                      e: Exception,
                                      interaction: discord.Interaction) -> None:
    """
    Small util function to notify the user something went wrong
    Args:
        class_name: str, name of class where the issue occurred
        method_name: str, name of method where the issue occurred
        error_code: int, custom error code to format in error message/log
        e: Exception, ecption that occurred
        interaction: discord.Interaction, interaction to respond

    Returns: None

    """
    logging.error(f"There was an exception with {class_name} ({method_name}): {e}")

    # Need try/except cause we don't know if it's a interaction.response.send_message or followup.send
    try:
        await interaction.response.send_message(f"⚠️ Oops! Quelque chose s'est mal passé. [{error_code}]",
                                                ephemeral=True)

    except Exception:
        await interaction.followup.send(f"⚠️ Oops! Quelque chose s'est mal passé. [{error_code}]", ephemeral=True)
