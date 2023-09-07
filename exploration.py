from typing import List

import requests


def get_categories() -> List[str]:
    """
    Get all the 2nd level categories from the MercadoLibre API
    :return: a list containing the id's of all the 2nd level categories
    """
    json = requests.get('https://api.mercadolibre.com/sites/MLA/categories').json()

    major_categories = []
    for category_dict in json:
        major_categories.append(category_dict['id'])

    children_categories = []
    for category in major_categories:
        request = requests.get(f'https://api.mercadolibre.com/categories/{category}')
        json = request.json()
        for subcategory in json['children_categories']:
            children_categories.append(subcategory['id'])

    return children_categories


def get_items(categories: List[str]) -> List[str]:
    """
    Get all the approved items from the categories passed as a parameter
    :param categories: a list containing the id's of the categories
    :return: a list containing the id's of all the items
    """

    items = {}
    for category in categories:
        json = requests.get(f'https://api.mercadolibre.com/sites/MLA/search?category={category}').json()
        for item in json['results']:
            if item["shipping"]["logistic_type"] == "fulfillment" and item["condition"] == "new":
                items[item["id"]] = item["price"]

    return items


def get_item_prices(items: List[str]) -> List[str]:
    """
    Get the prices of all the items passed as a parameter
    :param items: a list containing the id's of the items
    :return: a list containing the prices of all the items
    """
    # Split the items list into chunks of 20
    items = [items[i:i + 20] for i in range(0, len(items), 20)]

    prices = {}
    for items_chunk in items:
        # Create a string with the id's of the items separated by commas
        items_str = ','.join(items_chunk)
        json = requests.get(f'https://api.mercadolibre.com/items?ids={items_str}'
                            f'&attributes=id,price,shipping.logistic_type').json()
        print(json)

    return items


categories = get_categories()
get_items(categories)
