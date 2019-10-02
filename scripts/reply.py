import tweepy
from datetime import datetime, timedelta, timezone
import pytz
from philly_311_bot.request_id import RequestIDHandler
from philly_311_bot.db import CartoDB
from philly_311_bot.config import *

if __name__ == "__main__":

    # setup the tweepy API
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    # time
    est = pytz.timezone("US/Eastern")
    last_hour_date_time = datetime.now(est) - timedelta(hours=1)

    # database
    db = CartoDB()

    # loop over any mentions
    for status in tweepy.Cursor(api.mentions_timeline).items():

        # the time created
        created_at = status.created_at.replace(tzinfo=timezone.utc).astimezone(est)

        # only examine new tweets
        if created_at > last_hour_date_time:

            # respond
            response = RequestIDHandler.get_response(db, status.text)
            if response:
                api.update_status(f"@{status.user.screen_name} {response}", status.id)
