from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

from textblob import TextBlob

import numpy as np
import pandas as pd
import re

# # # # TWITTER CLIENT # # # #
class TwitterClient() :
    def __init__(self, twitter_user=None) :
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self) :
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets) :
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).pages(num_tweets) :
            tweets.append(tweet)
        return tweets

# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator() :
   
    def authenticate_twitter_app(self) :
        ACCESS_TOKEN = ""
        ACCESS_TOKEN_SECRET = ""
        CONSUMER_KEY = ""
        CONSUMER_SECRET = ""
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        return auth


# # # # TWITTER STREAMER # # # #
class TwitterStreamer() :
    """
    Class for streaming and processing live tweets.
    """

    def __init__(self) :
        self.twitter_autenticator = TwitterAuthenticator()

    def stream_tweets(self, fetched_tweets_filename, hash_tag_list) :
        # This handles Twitter authetification and the connection to Twitter Streaming API
        listener = TwitterListener(fetched_tweets_filename)
        auth = self.twitter_autenticator.authenticate_twitter_app()
        stream = Stream(auth, listener)

        # This line filter Twitter Streams to capture data by the keywords:
        stream.filter(track=hash_tag_list)


# # # # TWITTER STREAM LISTENER # # # #
class TwitterListener(StreamListener) :
    """
    This is a basic listener that just prints received tweets to stdout.
    """

    def __init__(self, fetched_tweets_filename) :
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data) :
        try :
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf :
                tf.write(data)
            return True
        except BaseException as e :
            print("Please ,enter Correct Username")
        return True

    def on_error(self, status) :
        if status == 420 :
            # Returning False on_data method in case rate limit occurs.
            return False
        print("Please ,enter Correct Username")


class TweetAnalyzer() :

    """
    Functionality for analyzing and categorizing content from tweets.
    """

    def clean_tweet(self, tweet) :
        return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", tweet).split())

    def analyze_sentiment(self, tweet) :
        analysis = TextBlob(self.clean_tweet(tweet))

        if analysis.sentiment.polarity > 0 :
            return "Positive"
        elif analysis.sentiment.polarity == 0 :
            return "Neutral"
        else :
            return "Controversial"

    def tweets_to_data_frame(self, tweets) :
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['Tweets'])

        df['Name'] = np.array([tweet._json['user']['name'] for tweet in tweets])
        df['Length'] = np.array([len(tweet.text) for tweet in tweets])
        df['Date'] = np.array([tweet.created_at for tweet in tweets])
        df['Source'] = np.array([tweet.source for tweet in tweets])
        df['location'] = np.array([tweet._json['user']['location'] for tweet in tweets])
        df['Followers'] = np.array([tweet._json['user']['followers_count'] for tweet in tweets])
        df['Followings'] = np.array([tweet._json['user']['friends_count'] for tweet in tweets])
        df['Hashtags'] = np.array([tweet._json['entities']['hashtags'][0]['text'] if(tweet._json['entities']['hashtags']!=[]) else "" for tweet in tweets])
        df['Language'] = np.array([tweet.lang for tweet in tweets])
        df['Likes'] = np.array([tweet.favorite_count for tweet in tweets])
        df['Retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df


