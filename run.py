from calendar import monthrange
from datetime import datetime, timedelta
from json import dumps
from os import getenv

from dataset_handling import make_csv, get_updated_month_df

import requests

from util import sleep_until_next_tweet, load_env_variables, get_today_str
from requests_oauthlib import OAuth1Session


class IPCMeli:
    def __init__(self):
        self.today_inflation = None
        self.month_inflation = None
        self.tweet_content = None
        load_env_variables()
        self.consumer_key = getenv("TW_CONSUMER_KEY")
        self.consumer_secret = getenv("TW_CONSUMER_SECRET")
        self.oauth_token = getenv("TW_OAUTH_TOKEN")
        self.oauth_token_secret = getenv("TW_OAUTH_TOKEN_SECRET")
        self.webhook_url = getenv("DISCORD_WEBHOOK")

    def run(self):
        print("Running...")
        while True:
            try:
                sleep_until_next_tweet()
                self.make_tweet()
            except Exception as e:
                print(e)
                self.send_discord_message()

    def make_tweet(self):
        # Set Tweet's content
        self.set_tweet_content()

        payload = {"text": self.tweet_content}

        # Make the request
        oauth = OAuth1Session(
            self.consumer_key,
            client_secret=self.consumer_secret,
            resource_owner_key=self.oauth_token,
            resource_owner_secret=self.oauth_token_secret,
        )

        # Making the request
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code != 201:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

        print("Response code: {}".format(response.status_code))

        # Saving the response as JSON
        json_response = response.json()
        print(dumps(json_response, indent=4, sort_keys=True))

    def set_tweet_content(self):
        self.tweet_content = ""
        self.calculate_inflation()

        if self.today_inflation > 0:
            emoji = "📈"
            month_message = "asciende a"
        elif self.today_inflation < 0:
            emoji = "📉"
            month_message = "desciende a"
        else:
            emoji = "👌"
            month_message = "se mantiene en"

        # Get tweet content
        self.tweet_content += f'🇦🇷 La inflación según Mercado Libre del día {get_today_str()} {emoji}\n\n'
        self.tweet_content += f'⁉️ Se registró una inflación del {self.today_inflation}%\n'
            
        # Check wheter it's the last day of month
        last_day_of_month = datetime.now().day == monthrange(datetime.now().year, datetime.now().month)[1]
        if last_day_of_month:
            # Make csv for next month
            make_csv()
            self.tweet_content += f'🗓️ El mes cerró con una tasa de inflación del {self.month_inflation}%\n'
        else:
            self.tweet_content += f'🗓️ La tasa mensual {month_message} {self.month_inflation}%\n'

    def calculate_inflation(self):
        # Get updated month df
        month_df = get_updated_month_df()

        # Get current date
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Get yesterday to compare with current date
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Get comparable df (remove deleted posts)
        month_df = month_df[month_df[today_str] > 0]

        # Compare prices
        yesterday_price = month_df[yesterday_str].sum()
        today_price = month_df[today_str].sum()

        # Get today's percentage change
        self.today_inflation = round((today_price - yesterday_price) / yesterday_price * 100, 2)

        # Get column with index 1
        first_month_day_price = month_df.iloc[:, 1:2].sum().iloc[0]

        self.month_inflation = round((today_price - first_month_day_price) / first_month_day_price * 100, 2)

    def send_discord_message(self):
        try:
            message_content = 'Falló la generación de un tweet :('

            data = {
                'content': message_content
            }

            requests.post(self.webhook_url, json=data)
        except:
            pass


if __name__ == '__main__':
    IPCMeli().run()
