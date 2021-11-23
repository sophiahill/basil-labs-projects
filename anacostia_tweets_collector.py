# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 16:38:17 2021

@author: sophi
"""
# get tweets using:
    # contains "anacostia"/"anacostia BID" AND
    # a keyword AND
    # by one of our usernames  
#%%
# IMPORT LIBS AND DATA #
import pandas as pd
import json
import tweepy
from datetime import datetime
from pymongo import MongoClient
import threading

#import dns

#%%
users = pd.read_csv("C:/Users/sophi/Documents/basil_labs/actual_users.csv")
keywords = pd.read_csv("C:/Users/sophi/Documents/basil_labs/keywords.csv")

user_list = [item for sublist in users.values for item in sublist]
keyword_list = [item for sublist in keywords.values for item in sublist]

#print(user_list)
#print(keyword_list)

#%%
# to avoid duplicates
tweet_list = []
#%%
# TOKENS/KEYS FROM TWITTER DEV PORTAL #
CONSUMER_KEY = "Cu2wfCU3ZJboZMIyB6343UFOX"
CONSUMER_SECRET = "ej1ruEhm3uMRe85msTMVkOwW4FF8VyMoZYHTGYNJL10hM437Nb"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANkxLAEAAAAARuGKV2rN6QNsO90ezGXUfZthnro%3DkZ58FWK0NIQXjcX3v9aCT8TD4O5aaBBAd9eg8h7tfRnGlbcFmE"
ACCESS_TOKEN = "3573720317-Viv7GabRZ54mRJiCHUAPIVDrIEOgWimuLKI7pfL"
ACCESS_SECRET = "bdvTZviqyfh39CCckXS7jH1xLXqkvX3QqPERJmfPeix4K"
#%%
# set tokens and keys
authentication = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
authentication.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(authentication, wait_on_rate_limit = True,
                 wait_on_rate_limit_notify = True)
#%%
# building filter
    # 1. contains "anacostia" or "anacostia bid"
        # anacostia OR (anacostia BID) lang:en -is:retweet 
    # 2. contains a keyword - make a string of keywords + OR
    # 3. by one of the usernames (from:username OR ...)

# get AnacostiaBID's friends and add them to users
#ana_name = "AnacostiaBID"
#for friend in tweepy.Cursor(api.friends, ana_name).items(1040):
    #user_list.append(friend.screen_name)
#user_list = set(user_list)
#pd.DataFrame(user_list).to_csv("C:/Users/sophi/Documents/basil_labs/actual_users.csv")
#%%
# TRYING TWEEPY #

# adding to db
def mongo(data_all):
    # get info we need
    text = data_all["text"] # text
    screen_name = data_all["user"]["screen_name"] # screen_name
    created_at = datetime.now() # timestamp
    id_str = data_all["id_str"] # tweet ID -> url
    retweet = data_all["retweeted"] # retweet (bool)
    reply = data_all["in_reply_to_status_id"] # reply to other tweet
    quoted = data_all["is_quote_status"] # False means not quoted
    
    # get url
    tweet_url = "https://twitter.com/" + screen_name + "/status/" + id_str
    
    add = False
    # if reply == None and retweet == False and not a quote tweet
        # and if we haven't already seen the tweet
        # filter for topics and add to db
    if (reply == None and retweet == False and ("RT" not in text) 
        and quoted == False and text not in tweet_list
        and screen_name != "AnacostiaBID" and "Scylla" not in text
        and "Motherland" not in text and "Raelle" not in text
        and screen_name != "metroherobot_gr"):
        # check if the text contains a keyword
        found = ""
        if any(word in text.lower() for word in keyword_list):
            for word in keyword_list:
                # if word or its plural are in the text, found keyword
                if ((word in text.lower()) or (word + "s" in text.lower())
                or (word + "ing" in text.lower() and word != "park"
                    and word != "fall")):
                    found = word
                    add = True
                    break
            
    if add: 
        add_dict = {"Headline/Tweet": text,
                    "Link": tweet_url,
                    "Timestamp": created_at,
                    "Screen_name": screen_name,
                    "Keyword": found, 
                    "Source (News/Twitter)": "Twitter"}
        
        # insert tweets into mongo db
        db = client["Anacostia"]
        collection = db["Tweets"]
        
        add_now = pd.DataFrame(add_dict, index = [0]).to_dict("records")
        collection.insert_many(add_now)
        
        tweet_list.append(text)
    
        print(text)
        print(screen_name)
        print("Added!")
        print("\n")
    
# make sure still running
def run_check():
  threading.Timer(600.0, run_check).start()
  print("Yup... still going")
#%%
# stream class
class MyStreamListener(tweepy.StreamListener):
    # when successful
    def on_data(self, data):
        data_all = json.loads(data)
        mongo(data_all)
        
        return True
        
    # when failed
    def on_failure(self, data):
        print(data)
        
if __name__ == "__main__":
    # connect to database
    client = MongoClient("mongodb+srv://soph15:h1q6Gb4t4knqxMOT@cluster0.1w9sb.mongodb.net/Anacostia?retryWrites=true&w=majority")
    
    # run stream
    # create instance of stream listener
    myStreamListener = MyStreamListener()
    
    # create instance of stream
    myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)
    
    # check still running every 5 min
    run_check()
    
    # search for tweets
    myStream.filter(track = ["anacostia", "anacostiaBID"],
    #follow = user_list,
    languages = ["en"],
    stall_warnings = True)
#%%
#myStream.disconnect()
#%%
# remove users? trying just anacostia + a keyword


#%%

