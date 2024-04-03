import ast
import base64
import json
import os
from datetime import datetime, timedelta

import requests


weekday_mapping = {
    "Sunday": f"Domingo",
    "Monday": "Lunes",
    "Tuesday": "Martes",
    "Wednesday": "Miércoles",
    "Thursday": "Jueves",
    "Friday": "Viernes",
    "Saturday": f"Sábado"
}

month_mapping = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}


def get_today_str() -> str:
    current_date = get_now_arg()
    weekday = current_date.strftime("%A")
    day = current_date.day
    month = current_date.month
    year = current_date.year
    return f"{weekday_mapping.get(weekday, '')} {day} de {month_mapping.get(month, '')} de {year}"


def get_ytd_inflation(month_inflation: float) -> float:
    current_date = get_now_arg()
    current_month = current_date.month

    # Read ytd inflation file
    with open("datasets/ytd-inflation.json") as file:
        ytd_inflation_json = json.load(file)

    # Modify file with new monthly inflation and save
    ytd_inflation_json[current_date.strftime("%Y-%m")] = month_inflation
    with open("datasets/ytd-inflation.json", "w") as file:
        json.dump(ytd_inflation_json, file)

    year_months_list = [(current_date - timedelta(days=30 * i)).strftime("%Y-%m") for i in range(current_month)][::-1]

    ytd_inflation = 1
    for year_month in year_months_list:
        month_inflation = 1 + ytd_inflation_json[year_month] / 100
        ytd_inflation *= month_inflation

    ytd_inflation -= 1
    ytd_inflation *= 100

    return round(ytd_inflation, 2)


def get_now_arg():
    # Get the current UTC time
    utc_now = datetime.utcnow()

    # Define a timedelta for UTC - 3 hours
    utc_minus_3_delta = timedelta(hours=-3)

    # Calculate the UTC - 3 time by subtracting the timedelta
    utc_minus_3_time = utc_now + utc_minus_3_delta

    return utc_minus_3_time


def get_access_token():
    client_id = os.environ.get("MELI_CLIENT_ID")
    client_secret = os.environ.get("MELI_CLIENT_SECRET")
    secret_key = os.environ.get("SUPER_SECRET_KEY")

    # Define the endpoint URL
    url = 'https://api.mercadolibre.com/oauth/token'

    # Define headers
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded'
    }

    # Define the payload data
    with open("meli_refresh_token") as f:
        encoded_refresh_token = f.read()
    refresh_token = decode_token(encoded_refresh_token, secret_key)

    payload = {
        'grant_type': 'refresh_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token
    }

    response = requests.post(url, data=payload, headers=headers).text

    response_dict = ast.literal_eval(response)

    with open("meli_refresh_token", "w") as f:
        f.write(encode_token(response_dict["refresh_token"], secret_key))

    return response_dict["access_token"]


def decode_token(encoded_message, secret_key):
    # Decode the base64-encoded message
    encoded_bytes = base64.b64decode(encoded_message)

    # Convert the secret key to bytes
    secret_key_bytes = secret_key.encode('utf-8')

    # XOR each byte of the encoded message with the corresponding byte of the secret key
    decoded_bytes = bytearray()
    for i in range(len(encoded_bytes)):
        decoded_byte = encoded_bytes[i] ^ secret_key_bytes[i % len(secret_key_bytes)]
        decoded_bytes.append(decoded_byte)

    # Decode the result as a UTF-8 string
    decoded_message = decoded_bytes.decode('utf-8')
    return decoded_message


def encode_token(message, secret_key):
    # Convert the message and secret key to bytes
    message_bytes = message.encode('utf-8')
    secret_key_bytes = secret_key.encode('utf-8')

    # XOR each byte of the message with the corresponding byte of the secret key
    encoded_bytes = bytearray()
    for i in range(len(message_bytes)):
        encoded_byte = message_bytes[i] ^ secret_key_bytes[i % len(secret_key_bytes)]
        encoded_bytes.append(encoded_byte)

    # Encode the result using base64
    encoded_message = base64.b64encode(encoded_bytes).decode('utf-8')
    return encoded_message
