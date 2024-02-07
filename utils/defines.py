###############################################################################
#
# File:      defines.py
# Author(s): Nico
# Scope:     Global variables
#
# Created:   07 February 2024
#
###############################################################################
# API Host (port handled in entry point parameters)
API_HOST = "http://127.0.0.1"
# Route to get_clothes
GET_CLOTHES_ROUTE = "api/operations/get_clothes"
# Route to get_requests
GET_REQUESTS_ROUTE = "api/operations/get_requests"
# Route to update_requests
UPDATE_REQUESTS_ROUTE = "api/operations/update_requests"
# Route to add_association
ADD_ASSOCIATION_ROUTE = "api/operations/add_association"
# In which category we create new text channel upon saving a clothe request
CATEGORY = "buybuybuybuy"
# Time in seconds to wait for a new API call to get_clothes
WAIT_TIME = "10"
# API parameter, in case too low can be increased up to 96
PER_PAGE = "10"
# Define referenced brands
BRANDS = {
    "adidas": "14",
    "Arc'Teryx": "319730",
    "arte": "271932",
    "Burberry": "364",
    "Carhartt": "362",
    "C.P. Company": "73952",
    "Lacoste": "304",
    "Nike": "53",
    "Ralph Lauren": "88",
    "Stone Island": "73306",
    "Stüssy": "441",
    "The North Face": "2319",
}
# Define references clothes states
CLOTHES_STATES = {
    "Neuf avec étiquette": "6",
    "Neuf sans étiquette": "1",
    "Très bon état": "2",
    "Bon état": "3"
}
