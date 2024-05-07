from datetime import timedelta
from typing import List, Dict
import pandas as pd
import requests
from util import get_access_token, get_now_arg
import json


def make_csv() -> None:
    """
    Create a csv file with the data of the items for the following month's analysis
    :return: None
    """
    # Get the data needed
    items_df = get_items_df(get_items_ids(get_categories()))

    # Create the csv file
    csv_name = (get_now_arg() + timedelta(days=1)).strftime("%Y-%m")
    items_df.to_csv(f'datasets/{csv_name}.csv', index=False)


def get_categories(only_ids=True):
    """
    Get all the 2nd level categories from the MercadoLibre API
    :return: a list containing the id's of all the 2nd level categories
    """
    with open("datasets/categories.txt") as file:
        categories = json.load(file)

    if only_ids:
        categories = list(categories.keys())

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


def get_items_df(items: List[str]) -> pd.DataFrame():
    """
    Get the prices of all the items passed as a parameter
    :param items: a list containing the id's of the items
    :return: a dictionary containing the id's of the items as keys and their prices as values
    """
    access_token = get_access_token()
    today = get_now_arg().strftime("%Y-%m-%d")

    # Split the items list into chunks of 20
    items_chunks = [items[i:i + 20] for i in range(0, len(items), 20)]

    # Initialize an empty list to store DataFrames
    dfs = []

    for items_chunk in items_chunks:
        # Create a string with the ids of the items separated by commas
        items_str = ','.join(items_chunk)
        url = f'https://api.mercadolibre.com/items?ids={items_str}' \
              '&attributes=id,price,title,permalink,thumbnail,category_id'
        json_response = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}).json()

        rows = []  # Initialize an empty list to store rows for the current chunk

        for item in json_response:
            try:
                if item["code"] == 200 and "price" in item["body"]:
                    item_body = item["body"]

                    item_id = item_body["id"]
                    price = item_body["price"]
                    title = item_body["title"]
                    permalink = item_body["permalink"]
                    thumbnail = item_body["thumbnail"]
                    category_id = item_body["category_id"]

                    # Append the row to the list of rows
                    rows.append({
                        "item_id": item_id,
                        "title": title,
                        "permalink": permalink,
                        "thumbnail": thumbnail,
                        "category_id": category_id,
                        today: price,  # Dynamically set column name based on date
                    })
            except KeyError:
                continue

                # Convert the list of rows to a DataFrame for the current chunk
        df_chunk = pd.DataFrame(rows)

        # Append the DataFrame for the current chunk to the list of DataFrames
        dfs.append(df_chunk)

    # Concatenate all DataFrames in the list along rows
    items_df = pd.concat(dfs, ignore_index=True)

    return items_df


def get_month_df() -> pd.DataFrame:
    # Get the csv name
    csv_name = get_now_arg().strftime("%Y-%m")

    # Load csv to a dataframe
    month_df = pd.read_csv(f'datasets/{csv_name}.csv')

    return month_df


def get_items_prices(items: List[str]) -> Dict[str, float]:
    """
    Get the prices of all the items passed as a parameter
    :param items: a list containing the id's of the items
    :return: a dictionary containing the id's of the items as keys and their prices as values
    """
    access_token = get_access_token()

    # Split the items dict into chunks of 20
    items = [items[i:i + 20] for i in range(0, len(items), 20)]

    prices = {}
    for items_chunk in items:
        # Create a string with the id's of the items separated by commas
        items_str = ','.join(items_chunk)
        url = f'https://api.mercadolibre.com/items?ids={items_str}&attributes=id,price'
        json = requests.get(url, headers={'Authorization': f'Bearer {access_token}'}).json()
        for item in json:
            try:
                if item["code"] == 200 and "price" in item["body"]:
                    item_id = item["body"]["id"]
                    price = item["body"]["price"]
                    prices[item_id] = price
                else:
                    item_id = item["body"]["id"]
                    prices[item_id] = -1
            except:
                continue

    return prices


def get_updated_month_df() -> pd.DataFrame:
    # Get the csv name
    csv_name = get_now_arg().strftime("%Y-%m")

    # Get current month's df
    month_df = get_month_df()

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
    from dotenv import load_dotenv

    load_dotenv()
    make_csv()
