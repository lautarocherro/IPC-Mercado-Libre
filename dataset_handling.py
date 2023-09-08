from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
import requests


def make_csv() -> None:
    """
    Create a csv file with the data of the items for the following month's analysis
    :return: None
    """
    # Get the data needed
    prices = get_item_prices(get_items(get_categories()))

    # Get the current date
    today = datetime.now().strftime("%Y-%m-%d")

    # Create a Dataframe from the data
    month_df = pd.DataFrame(
        {
            'id': prices.keys(),
            today: prices.values(),
         }
    )

    # Create the csv file
    csv_name = (datetime.now() + timedelta(days=1)).strftime("%Y-%m")
    month_df.to_csv(f'datasets/{csv_name}.csv', index=False)


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
    :return: a dictionary containing the id's of the items as keys and their prices as values
    """
    items = []
    for category in categories:
        json = requests.get(f'https://api.mercadolibre.com/sites/MLA/search?category={category}').json()
        for item in json['results']:
            if item["shipping"]["logistic_type"] == "fulfillment" and item["condition"] == "new":
                items.append(item["id"])

    return items


def get_item_prices(items: List[str]) -> Dict[str, float]:
    """
    Get the prices of all the items passed as a parameter
    :param items: a list containing the id's of the items
    :return: a dictionary containing the id's of the items as keys and their prices as values
    """
    # Split the items dict into chunks of 20
    items = [items[i:i + 20] for i in range(0, len(items), 20)]

    prices = {}
    for items_chunk in items:
        # Create a string with the id's of the items separated by commas
        items_str = ','.join(items_chunk)
        json = requests.get(f'https://api.mercadolibre.com/items?ids={items_str}'
                            f'&attributes=id,price,shipping.logistic_type').json()
        for item in json:
            if item["code"] == 200:
                item_id = item["body"]["id"]
                price = item["body"]["price"]
                prices[item_id] = price
            else:
                item_id = item["body"]["id"]
                prices[item_id] = -1

    return prices


def update_csv() -> None:
    # Get the csv name
    csv_name = datetime.now().strftime("%Y-%m")

    # Load csv to a dataframe
    month_df = pd.read_csv(f'datasets/{csv_name}.csv')

    # Get ID's to check today's prices
    ids = month_df['id'].tolist()

    # Get today's prices
    prices = get_item_prices(ids)

    # Get the current date
    today = datetime.now().strftime("%Y-%m-%d")

    # Make new df out of the prices
    new_prices_df = pd.DataFrame(
        {
            'id': prices.keys(),
            today: prices.values(),
        }
    )

    # Merge both dataframes by the id column
    month_df = pd.merge(month_df, new_prices_df, on='id')

    # Save the dataframe to the csv file
    month_df.to_csv(f'datasets/{csv_name}.csv', index=False)


print('Starting')
make_csv()
print('Finishing')
update_csv()
