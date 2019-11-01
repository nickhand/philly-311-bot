# 311 Twitter Bot

## Package workflow

The main script that updates the accounts' Twitter status is the `scripts/update.py` file. It is executed from the
command-line / Terminal application using:

```bash
python scripts/update.py
```

First, this script imports the packages it needs to run:

```python
from philly_311_bot.db import CartoDB
from philly_311_bot.config import *
from philly_311_bot import stats
import pandas as pd
import tweepy
import time
```

- the CartoDB object handles pulling data from the OpenDataPhilly 311 databases in the cloud
- the "config" line imports your authentication variables: `CONSUMER_KEY`, `CONSUMER_SECRET`, `ACCESS_KEY`, `ACCESS_SECRET`
- the "stats" line imports the main module that generates the text of the tweets
- tweepy is the package that does the main work of sending the tweets to Twitter

When executing the script everything indented below the `if __name__ == "__main__":` part will be executed:

#### Step 1: setup up authentication for Twitter and tweepy

```python
# setup the tweepy API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)
```

#### Step 2: initialize the connection to the CARTO database

```python
# initialize the CARTO database
db = CartoDB()
```

#### Step 3: Create the list of tweets we want to send.

- This creates three "categories" of tweets, for newly opened,
  delayed, and closed requests, respectively.
- The specifics of how these tweets are created are in the `stats.py` file.

```python
# the summary tweets we'll print
summarys = [
    list(stats.OpenedRequests(db, include_all=True)()),
    list(stats.DelayedRequests(db)()),
    list(stats.ClosedRequests(db)()),
]
```

#### Step 4: Send the first "summary" tweet for each catagory

- Each item in the "summarys" list above is a list of tweets to send
- The first item in the list of tweets provides a high-level summary of the data. For example
  - Opened tweets: `On October 31st, there were 2,110 new requests and 983 are still open.`
  - Delayed tweets: `On October 31st, 935 requests were expected to be closed but remain open.`
  - Closed tweets: `On October 31st, 2,370 requests were updated and are marked as closed.`

```python
# tweet each summary
for summary in summarys:
    api.update_status(summary[0])
    time.sleep(60)
```

#### Step 5: Send the more detailed tweets about the opened requests, giving breakdowns by type and neighborhood

- The more detailed breakdown includes the top requests by type and neighborhood.
- This tweets those lists out as a threaded list
- To do a threaded list of tweets, you have to tell Twitter the "status_id" of the previous tweet that you want to attach the new tweet to.

```python
# tweet detailed breakdown
for thread in summarys[0][1:]:
    status_id = None
    for tweet in thread:
        s = api.update_status(tweet, status_id)
        status_id = s.id
    time.sleep(60)
```

## Concepts

- object oriented programming (classes in Python)
    - writing Python objects as "classes" and initializing them
    - see, e.g., https://realpython.com/python3-object-oriented-programming/
- carto2gpd: custom Python library we use to pull data down from the CARTO cloud database
    - https://github.com/PhiladelphiaController/carto2gpd
- tweepy: handles the interface to Twitter from Python
    - A lot of functionality, but we only use the "update_status" function
- geopandas and adding neighborhood information
    - the 311 data comes with latitude/longitude. I am identifying the neighborhood of the request by taking boundaries of all the neighborhoods
    and testing if the lat/lng is inside the boundary until I find the right one
    - the code to do that uses `geopandas`, and is done in this function: https://github.com/nickhand/philly-311-bot/blob/master/philly_311_bot/stats.py#L54
