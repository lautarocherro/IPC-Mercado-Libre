from calendar import monthrange
from datetime import datetime, timedelta
import os
import util
from dataset_handling import make_csv, get_updated_month_df

import requests

from util import get_today_str
from requests_oauthlib import OAuth1Session


class IPCMeli:
    def __init__(self):
        self.ytd_inflation = None
        self.last_day_of_month = None
        self.today_inflation = None
        self.month_inflation = None
        self.tweet_content = None
        self.consumer_key = os.environ.get("TW_CONSUMER_KEY")
        self.consumer_secret = os.environ.get("TW_CONSUMER_SECRET")
        self.oauth_token = os.environ.get("TW_OAUTH_TOKEN")
        self.oauth_token_secret = os.environ.get("TW_OAUTH_TOKEN_SECRET")
        self.webhook_url = os.environ.get("DISCORD_WEBHOOK")

    def run(self):
        print("Running...")
        try:
            # Check if it's the last day of month and make tweet
            self.last_day_of_month = datetime.now().day == monthrange(datetime.now().year, datetime.now().month)[1]
            self.make_tweet()

            # Make csv for next month
            if self.last_day_of_month:
                make_csv()
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

        if response.status_code == 201:
            print("Tweet generated successfully")
        else:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

    def set_tweet_content(self):
        self.tweet_content = ""
        self.calculate_inflation()

        if self.today_inflation > 0:
            emoji = "📈"
            month_message = "asciende al"
        elif self.today_inflation < 0:
            emoji = "📉"
            month_message = "desciende al"
        else:
            emoji = "👌"
            month_message = "se mantiene en"

        # Get tweet content
        self.tweet_content += f'🇦🇷 Inflación según Mercado Libre del {get_today_str()}\n\n'
        self.tweet_content += f'{emoji} Se registró una inflación del {self.today_inflation}%\n'

        # Check wheter it's the last day of month
        if self.last_day_of_month:
            self.tweet_content += f'🗓️ El mes cerró con una tasa de inflación del {self.month_inflation}%\n\n'
        else:
            self.tweet_content += f'🗓️ La tasa mensual {month_message} {self.month_inflation}%\n\n'

        # Add yearly inflation
        if datetime.now().year >= 2024:
            self.tweet_content += f'🔺 La tasa anual acumulada es del {self.ytd_inflation}%\n'

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

        if datetime.now().year >= 2024:
            self.ytd_inflation = util.get_ytd_inflation(self.month_inflation)

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
