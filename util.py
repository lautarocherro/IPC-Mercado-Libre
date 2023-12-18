import json
from datetime import datetime, timezone, timedelta
from time import sleep
from os import environ

import pandas as pd


def sleep_until_next_tweet():
    # Get the current datetime in UTC-3
    current_datetime = datetime.now(timezone(timedelta(hours=-3)))

    # Set the target datetime for the next day at 8 PM
    target_datetime = current_datetime.replace(hour=20, minute=0, second=0, microsecond=0)

    # if 20hs have past, make tweet tomorrow
    if current_datetime.hour >= 20:
        target_datetime += timedelta(days=1)

    # Calculate the time difference between the current and target datetime
    time_difference = target_datetime - current_datetime

    # Convert the time difference to seconds
    sleep_duration = time_difference.total_seconds()

    print(f"Sleeping for {sleep_duration} seconds. Next tweet will be at {target_datetime}")
    # Sleep until the target datetime
    sleep(sleep_duration)


def load_env_variables():
    with open(".env", 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                environ[key] = value


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
    current_date = datetime.now()
    weekday = current_date.strftime("%A")
    day = current_date.day
    month = current_date.month
    year = current_date.year
    return f"{weekday_mapping.get(weekday, '')} {day} de {month_mapping.get(month, '')} de {year}"


def get_ytd_inflation(month_inflation: float) -> float:
    current_date = datetime.now()
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

    return round(ytd_inflation, 2)
