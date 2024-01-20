from datetime import timedelta
from typing import List, Dict
import pandas as pd
import requests

from util import get_now_arg


def make_csv() -> None:
    """
    Create a csv file with the data of the items for the following month's analysis
    :return: None
    """
    # Get the data needed
    prices = get_items_prices(get_items_ids(get_categories()))

    # Get the current date
    today = get_now_arg().strftime("%Y-%m-%d")

    # Create a Dataframe from the data
    month_df = pd.DataFrame(
        {
            'id': prices.keys(),
            today: prices.values(),
         }
    )

    # Create the csv file
    csv_name = (get_now_arg() + timedelta(days=1)).strftime("%Y-%m")
    month_df.to_csv(f'datasets/{csv_name}.csv', index=False)


def get_categories() -> List[str]:
    """
    Get all the 2nd level categories from the MercadoLibre API
    :return: a list containing the id's of all the 2nd level categories
    """
    with open("datasets/categories.txt") as file:
        categories = file.read().splitlines()

    return categories


def get_items_ids(categories: List[str]) -> List[str]:
    """
    Get all the approved items from the categories passed as a parameter
    :param categories: a list containing the id's of the categories
    :return: a list containing the id's of all the approved items
    """
    ids = []
    for category in categories:
        json = requests.get(f'https://api.mercadolibre.com/sites/MLA/search?category={category}').json()
        for item in json['results']:
            if item["shipping"]["logistic_type"] == "fulfillment" and item["condition"] == "new":
                ids.append(item["id"])

    return ids


def get_items_prices(items: List[str]) -> Dict[str, float]:
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
            if item["code"] == 200 and "price" in item["body"]:
                item_id = item["body"]["id"]
                price = item["body"]["price"]
                prices[item_id] = price
            else:
                item_id = item["body"]["id"]
                prices[item_id] = -1

    return prices


def get_updated_month_df() -> pd.DataFrame:
    # Get the csv name
    csv_name = get_now_arg().strftime("%Y-%m")

    # Load csv to a dataframe
    month_df = pd.read_csv(f'datasets/{csv_name}.csv')

    # Get ID's to check today's prices
    ids = month_df['id'].tolist()

    # Get today's prices
    prices = get_items_prices(ids)

    # Get the current date
    today = get_now_arg().strftime("%Y-%m-%d")

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

    return month_df


if __name__ == "__main__":
    print('Starting')
    make_csv()
    print('Finishing')
    get_updated_month_df()
