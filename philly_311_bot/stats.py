import pandas as pd
import geopandas as gpd
import abc
import os

MAX_LENGTH = 230
YESTERDAY = (pd.Timestamp.today(tz="US/Eastern") - pd.Timedelta("1 day")).strftime(
    "%m/%d/%Y"
)
TODAY = pd.Timestamp.today(tz="US/Eastern").strftime("%m/%d/%Y")


def load_neighborhoods():
    """
    Load polygons for Philadelphia neighborhoods.
    """
    curr_dir = os.path.dirname(__file__)
    filename = os.path.join(curr_dir, "data", "neighborhoods.geojson")
    return gpd.read_file(filename)


def yesterdays_date():
    """
    Return a formatted version of yesterday's date.
    """

    def suffix(d):
        return "th" if 11 <= d <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")

    def custom_strftime(format, t):
        return t.strftime(format).replace("{S}", str(t.day) + suffix(t.day))

    yesterday = pd.to_datetime("today") - pd.Timedelta("1 day")
    return custom_strftime("%B {S}", yesterday)


class SummaryTweets(object):
    def __init__(self, db, include_all=False):
        self.db = db
        self.include_all = include_all

    @abc.abstractproperty
    def label(self):
        pass

    @abc.abstractmethod
    def first_tweet(self, df):
        pass

    @abc.abstractmethod
    def get_data(self):
        pass

    def geocode(self, df):

        df = df.dropna(subset=["lat", "lon"])
        hoods = load_neighborhoods()
        return gpd.sjoin(df.to_crs(hoods.crs), hoods, op="within")

    def __call__(self):

        # get the data
        df = self.get_data()

        # get all of the tweets
        tweets = [self.first_tweet(df)]

        # group by type and hood
        if self.include_all:
            by_type = df.groupby(["service_name"]).size()
            header = f"Yesterday's {self.label} cases by type:"
            tweets += [make_tweets(by_type, header=header)]

            # geocoded
            geocoded = self.geocode(df)
            args = (len(geocoded), len(df), self.label.lower())
            header = "{:,d} out of {:,d} yesterday's {} cases have locations. The top 15 neighborhoods are:".format(
                *args
            )
            by_hood = (
                geocoded.groupby(["neighborhood"]).size().sort_values(ascending=False)
            )
            tweets += [make_tweets(by_hood.iloc[:15], header=header)]

        for t in tweets:
            yield t


class OpenedRequests(SummaryTweets):
    """
    Opened 311 requests from the past day.
    """

    @property
    def label(self):
        return "still open"

    def first_tweet(self, df):
        N_open = len(df)
        date_str = yesterdays_date()
        N = self.db.count(where=f"requested_datetime >= '{YESTERDAY}'")
        return f"On {date_str}, there were {N:,} new requests and {N_open:,} are still open."

    def get_data(self):
        return self.db.query(
            where=f"requested_datetime >= '{YESTERDAY}' AND status = 'Open'"
        )


class DelayedRequests(SummaryTweets):
    """
    Delayed 311 requests from the past day.
    """

    @property
    def label(self):
        return "delayed"

    def first_tweet(self, df):
        N = len(df)
        date_str = yesterdays_date()
        return (
            f"On {date_str}, {N:,} requests were expected to be closed but remain open."
        )

    def get_data(self):
        query = [
            "status = 'Open'",
            f"expected_datetime >= '{YESTERDAY}'",
            f"expected_datetime < '{TODAY}'",
        ]
        query = " AND ".join(query)
        return self.db.query(where=query)


class ClosedRequests(SummaryTweets):
    """
    Closed 311 requests from the past day.
    """

    @property
    def label(self):
        return "closed"

    def first_tweet(self, df):
        N = len(df)
        date_str = yesterdays_date()
        return f"On {date_str}, {N:,} requests were updated and are marked as closed."

    def get_data(self):
        query = [
            "status = 'Closed'",
            f"updated_datetime >= '{YESTERDAY}'",
            f"updated_datetime < '{TODAY}'",
        ]
        query = " AND ".join(query)
        return self.db.query(where=query)


def make_tweets(df, header=""):

    tweets = []
    tweet = str(header) + "\n\n"
    for i, (tag, N) in enumerate(df.sort_values(ascending=False).iteritems()):
        this_tweet = f"{i+1}. {tag} {N}\n"
        if len(tweet) + len(this_tweet) < MAX_LENGTH - 5:
            tweet += this_tweet
        else:
            tweets.append(tweet)
            tweet = this_tweet
    tweets.append(tweet)

    for i in range(len(tweets)):
        tweets[i] += "(%d/%d)" % (i + 1, len(tweets))
    return tweets
