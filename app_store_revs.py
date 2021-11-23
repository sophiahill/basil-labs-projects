# -*- coding: utf-8 -*-
"""
@author: sophi
"""

###################################################################
# IMPORT LIBS
###################################################################
#%%
import pandas as pd
from app_store_scraper import AppStore
import os
#%%
###################################################################
# APP STORE FUNCTIONS
###################################################################

# get big df from google drive, return random sample of 20000 apps
def app_get_df():
    # from google drive
    url = "https://drive.google.com/file/d/19ypsg_CG_BZuVbjwwzr0mvmuuS_0ud53/view"
    url2='https://drive.google.com/uc?id=' + url.split('/')[-2]
    df = pd.read_csv(url2)
    df = df[df["app_names"].str.isalnum() == True]
    df = df.sample(n = 20000) 
    return(df)

# returns df of review information for one app, given the app name
def one_app(name):
    try:
        app = AppStore(country = "us", app_name = name)
        app.review(how_many = 500, sleep = 0.1) # get 500 reviews
        revs_df = pd.DataFrame.from_dict(app.reviews) # turn to dict
        # if we have reviews, write them to csv
        if len(revs_df) > 0:
            revs_df.to_csv(name + ".csv", index = False,
                           encoding = "utf-8-sig") # write
    except:
        pass
    
#%%
df = app_get_df()

folder_path = "D:/vnineteenDD/app_store/"
# folder_path = "C:/Users/sophi/Documents/basil_labs"
os.chdir(folder_path)

# make folder to save files into
if not os.path.exists("app_store_revs"):
    os.makedirs("app_store_revs")
os.chdir("app_store_revs")

# code for all reviews in the google play store:
parts_to_run = 5000
intervals = len(df) // parts_to_run

# get reviews in intervals, map list of app names (size intervals) to one_app fn
for i in range(0, parts_to_run):
    print(i)
    print()
    apps_list = df[intervals * i : intervals * (i + 1)].iloc[:, 0].tolist()
    try:
        list(map(one_app, apps_list)) 
    except:
        pass


