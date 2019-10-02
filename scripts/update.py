from philly_311_bot.db import CartoDB
from phily_311_bot.config import *
import pandas as pd
import tweepy
import time
import stats

if __name__ == "__main__":

    # setup the tweepy API
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    # initialize the CARTO database
    db = CartoDB()

    # the summary tweets we'll print
    summarys = [
        list(stats.OpenedRequests(db, include_all=True)()),
        list(stats.DelayedRequests(db)()),
        list(stats.ClosedRequests(db)()),
    ]

    # tweet each summary
    for summary in summarys:
        api.update_status(summary[0])
        time.sleep(60)

    # tweet detailed breakdown
    for thread in summarys[0][1:]:
        status_id = None
        for tweet in thread:
            s = api.update_status(tweet, status_id)
            status_id = s.id
        time.sleep(60)
