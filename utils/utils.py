###############################################################################
#
# File:      utils.py
# Author(s): Nico
# Scope:     Utils functions
#
# Created:   07 February 2024
#
###############################################################################

def reformat_clothes_states(clothes_states):
    """
    Reformats clothes states from ['1', '2', ...] to '1,2,...'
    :param clothes_states: list of clothes states
    :return: list of reformatted clothes states
    """
    concat_values = ""
    for state in clothes_states:
        concat_values += state
        concat_values += ","
    concat_values = concat_values[:-1]

    return concat_values
