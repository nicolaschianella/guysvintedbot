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
