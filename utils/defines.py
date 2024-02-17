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
# Route to get user infos
USER_INFOS_ROUTE = "api/operations/get_user_infos"
# Route to scrape clothes images
GET_IMAGES_URL_ROUTE = "api/operations/get_images_url"
# Route to get {requests: channel_ids}
REQUESTS_CHANNEL_IDS_ROUTE = "api/operations/get_active_requests_and_channels"
# Route to add clothe in stock
ADD_CLOTHE_IN_STOCK_ROUTE = "api/operations/add_clothe_in_stock"
# Route to get clothes from stock
GET_CLOTHES_FROM_STOCK_ROUTE = "api/operations/get_clothes_from_stock"
# Route to register clothes as sold
SELL_CLOTHES_ROUTE ="api/operations/sell_clothes"
# Route to delete clothes from stock
DELETE_CLOTHES_ROUTE = "api/operations/delete_clothes"
# Route to log in
LOGIN_ROUTE = "api/operations/login"
# Route to get closest pickup points
PICKUP_GET_ROUTE = "api/operations/get_close_pickup_points"
# Route to save pickup points
PICKUP_POST_ROUTE = "api/operations/save_pickup_points"
# In which category we create new text channel upon saving a clothe request
CATEGORY = "buybuybuybuy"
# Time in seconds to wait for a new API call to get_clothes
WAIT_TIME = "1"
# API parameter, in case too low can be increased up to 96
PER_PAGE = "96"
# Minimal matching ratio between found clothe and search text if provided (0 to 100)
FUZZ_RATIO = 60
# In case we could not retrieve clothe images
NO_IMAGE_AVAILABLE_URL = "https://upload.wikimedia.org/wikipedia/commons/1/14/No_Image_Available.jpg"
# Define referenced brands
BRANDS = {
    "adidas": "14",
    "Arc'teryx": "319730",
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
