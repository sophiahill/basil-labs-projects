# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 07:01:32 2021

@author: sophi
"""

# %%
### IMPORTING LIBRARIES ###

import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime, date, timedelta
from pymongo import MongoClient
import SessionState
import base64
import streamlit.components.v1 as components
import plotly.express as px

pd.options.mode.chained_assignment = None

# %%
### HELPER FUNCTIONS ###

# Converts datetime to string of the (Month Date) format
def axis_date(dt):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
              'Oct', 'Nov', 'Dec']
    index = dt.month - 1
    month_string = months[index]
    return month_string + ' ' + str(dt.day)

# cleans tweet text before streamlit
def clean_text(tweet):
    new_tweet = tweet.strip()
    new_tweet = re.sub(r"(\t)|(\n)|(\r)", " ", new_tweet, flags = re.S)
    new_tweet = re.sub(r"https:.*", "", new_tweet, flags = re.S)
    new_tweet = re.sub(r"( &amp)|( &amp)|(&amp)", "", new_tweet, flags = re.S)
    return(new_tweet)

# Gets today's date and converts it to a string
def date_to_string(dt_date):
    date_string = str(dt_date.year) + '-' + str(dt_date.month) + '-'
    if len(str(dt_date.day)) == 1:
        date_string += '0' + str(dt_date.day)
    else:
        date_string += str(dt_date.day)
    return date_string

# Creates link to download a dataframe as .csv
def download_dataframe(df, filename, link):
    if isinstance(df, pd.DataFrame):
        df = df.to_csv(index=False)
    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(df.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}">{link}</a>'

# Gets date from n months ago from today
def get_n_months_ago(n):
    assert n <= 12, "Invalid Argument: n must be at most 12"
    today = date.today()
    year = today.year
    month = today.month
    day = today.day
    temp = month - n
    
    if temp <= 0:
        temp += 12
        year -= 1
    return str(year) + '-' + str(temp) + '-' + str(day)

# return df where rows before are summed to get new row
def get_summed(df):
    new_df = df.copy()
    for i in range(new_df.shape[0] - 1, 0, -1):
        summed = new_df.iloc[:i + 1, :-1].sum(axis = 0)
        new_df.iloc[i, :-1] = summed
    return(new_df)

# get list of past 6 days + inputted end date
def get_week(end):
    start = end - timedelta(days = 6)
    start_date, end_date = start.date(), end.date()
    one_week = pd.date_range(start_date, end_date, freq = "d")
    # get list of dates
    week_list = []
    for day in one_week:
        d = td(day)
        week_list.append(d)
    return(week_list)

# links df row
def hyperlink(row):
    text = row["Tweet"]
    link = row["Link"]
    return f'<a target="_blank" href="{link}">{text}</a>'

# includes time
def inc_time(stamp):
    x = str(stamp)[:-7]
    return(datetime.strptime(x, "%Y-%m-%d %H:%M:%S").strftime("%#m/%d/%Y %I:%M%p"))

# get selectbox tweets
def show_table(day, tweets, weekdays):
    tweets_new = tweets.copy()
    t = tweets_new["Timestamp"].apply(lambda x: td(x)) # timestamps to legible
    # initially show week, with selection show day
    if day == "":
        lab = "Tweets from this week:"
        tab = tweets_new[t.isin(weekdays)]
    else:
        tab = tweets_new[t == day]
        lab = "Tweets from: " + day
    return(lab, tab)

# timestamp to "m/d/y"
def td(stamp):
    if not isinstance(stamp, str):
        stamp = str(stamp.date())
    return(datetime.strptime(stamp, "%Y-%m-%d").strftime("%m/%d/%Y"))

# %%
### CREATE NEWS PART OF DASHBOARD ###

def news_dashboard():
    # Connecting to Mongo
    client = MongoClient("mongodb+srv://seanwei2001:7jqxW8chLNuE6qqJ@cluster0.1w9sb.mongodb.net/Anacostia?retryWrites=true&w=majority")
    db = client['Anacostia']
    collection = db['News']
    
    # Making dataframe and dropping '_id' column
    data = pd.DataFrame(list(collection.find())[1:])
    news = data.copy()
    news = news.drop('_id', axis = 1)
    
    # Sorting with the newest stories first
    news = news.sort_values(by = 'datetime', ascending = False)
    news = news.reset_index().drop('index', axis = 1)

    # MOST RECENT ARTICLES WITH HYPERLINKED HEADLINES
    
    # Title and subtitle
    st.title('Anacostia News and Tweets')
    st.markdown('Tracking all relevant news articles and tweets about Anacostia')
    st.markdown("---")
    news_header = "<h1 style='font-size: 25px';>News</h1>"
    st.markdown(news_header, unsafe_allow_html = True)
    
    # Making two columns
    c1, c2 = st.beta_columns((0.8, 1))
    
    # Putting 5 most recent stories in the left column
    c1.subheader("Most recent articles:")
    for i in range(5):
        c1.markdown('[' + news['Headline'].iloc[i] + '](' + news['Link'].iloc[i] + ') ('
                    + news['Timestamp'].iloc[i] + ')')
    
    # Can be used to put recent stories in a table:
    # c1.write(recent[['Headline', 'Link', 'Timestamp']].to_html(escape=False, index = False), unsafe_allow_html=True)

    # PLOTTING ARTICLE TRAFFIC
    
    # Getting all articles from the last month
    one_month_ago = get_n_months_ago(1)
    last_month = news[news['datetime'] >= one_month_ago]
    last_month['Date'] = [i.date() for i in last_month['datetime']]
    
    # Creating dataframe with a column of dates and the number of articles published per date
    news_by_date = pd.DataFrame(last_month.groupby(['Date']).size())
    news_by_date = news_by_date.rename(columns = {0 : 'Number of Articles'})
    news_by_date = news_by_date.sort_values(by = 'Date')
    news_by_date = news_by_date.reset_index()
    news_by_date['Date'] = news_by_date['Date'].apply(axis_date)
    
    # Making bar chart
    fig = px.bar(news_by_date, y = 'Number of Articles', x = 'Date', orientation = 'v',
                 title = "Article Frequency in the Past Month")
    fig.update_traces(marker_color = "rgb(135, 197, 95)")
    fig.update_layout(
        font_family = "sans serif",
        title_x = 0.5)
    
    # Bar chart goes into column 2
    c2.plotly_chart(fig, use_container_width = True)
    
    # Putting in entire news dataframe
    st.subheader('All news articles:')
    st.dataframe(news[['Headline', 'Link', 'Timestamp']], width = 919)
    
    # Making a button to allow for dataframe download
    if st.button('Download News Dataframe as .csv'):
        link = download_dataframe(news, 'anacostia_news.csv', 'Click here to download your data')
        st.markdown(link, unsafe_allow_html=True)
        
    return True
    
#%%
### CREATE TWEETS PART OF DASHBOARD ###

def tweets_dashboard():
    # establish connection to mongo
    client = MongoClient("mongodb+srv://soph15:h1q6Gb4t4knqxMOT@cluster0.1w9sb.mongodb.net/Anacostia?retryWrites=true&w=majority")
    db = client["Anacostia"]
    collection = db["Tweets"]
    
    # get tweets
    tweets = pd.DataFrame(list(collection.find()))
    tweets = tweets.copy()
    tweets = tweets.drop('_id', axis = 1)
    
    # sort by date
    tweets = tweets.sort_values(by = "Timestamp", ascending = False)
    tweets = tweets.reset_index().drop("index", axis = 1)
    
    # MAKE TABLE OF TWEETS FROM CURRENT WEEK, SELECT BY DAY 
    
    st.markdown("---")
    tweets_header = "<h1 style='font-size: 25px';>Tweets</h1>"
    st.markdown(tweets_header, unsafe_allow_html = True)
    # selctbox #
    # get list of past weekdays based on most recent tweet
    last_date = tweets["Timestamp"][0]
    weekdays = get_week(last_date)
    
    weekdays.append("") # add empty string for no selection
    weekdays = list(reversed(weekdays)) # get in right order
    
    day = st.selectbox(label = "Choose tweets by day", options = weekdays)
    lab, tab = show_table(day, tweets, weekdays[1:])
    
    # make timestamps legible
    tab["Timestamp"] = tab["Timestamp"].apply(lambda x: inc_time(x))
    # fix cols - rename and remove last one
    new_tab = tab.iloc[:, :-1] # remove Source col
    new_tab.columns = ["Tweet", "Link", "Timestamp", "Screen Name", "Keyword"]
    # clean tweets
    new_tab["Tweet"] = new_tab["Tweet"].apply(lambda x: clean_text(x))
    
    temp = new_tab.copy() # keep links col for downloadable table
    
    # make links clickable before writing
    new_tab['Tweet'] = new_tab.apply(hyperlink, axis = 1)
    new_tab = new_tab.drop(["Link"], axis = 1) # no longer needed
    # write with to_html
    new_tab = new_tab.to_html(escape = False, index = False)
    
    st.subheader(lab)
    st.write(new_tab, unsafe_allow_html = True, use_container_width = True)
    # make so able to download table
    if st.button('Download Tweets Dataframe as .csv'):
        link = download_dataframe(temp, 'anacostia_tweets.csv', 'Click here to download your data')
        st.markdown(link, unsafe_allow_html=True)
    
    # TOPICS BAR CHART
    
    st.subheader("Top 10 keywords:")
    
    c3, c4 = st.beta_columns(2)
    
    # create new col for just dates called Dates (no times)
    graph_tweets = tweets.copy()
    graph_tweets["Dates"] = graph_tweets["Timestamp"].apply(lambda x: str(x)[:-16])
    
    # get keyword cols for graph_df (add Date) and initialize
    graph_df_cols = sorted(list(graph_tweets["Keyword"].unique()))
    graph_df_cols.append("Date")
    
    graph_df = pd.DataFrame(columns = graph_df_cols)
    
    # group by date, get instances for graph_df
    grouped = graph_tweets.groupby(by = "Dates") # group by Dates
    for name, group in grouped:
        # within each date group, group by keywords
        counts = group.groupby(by = "Keyword").size().to_frame().reset_index()
        counts_trans = counts.transpose()
        # make it so first row (has keywords) is col names
        new_header = counts_trans.iloc[0, :]
        counts_trans = counts_trans[1:]
        counts_trans.columns = new_header
        counts_trans["Date"] = name
        # add this row of the df to graph_
        counts_dict = counts_trans.to_dict("records")
        graph_df = graph_df.append(counts_dict)
        
    # make bar chart of frequenices instead
    summed = graph_df.iloc[:, :-1].sum(axis = 0).to_frame().reset_index()
    summed.columns = ["Keyword", "Count"]
    summed_ordered = summed.sort_values(by = ["Count"], axis = 0, ascending = False)
    top_10 = summed_ordered.iloc[:10, :]
    
    # title and bar graph
    fig_bar = px.bar(top_10, y = "Count", x = "Keyword", orientation = 'v',
                 title = "Overall Frequency")
    fig_bar.update_traces(marker_color = "rgb(47, 138, 196)")
    fig_bar.update_layout(
        font_family = "sans serif",
        title_x = 0.5)
    
    # goes into left col
    c3.plotly_chart(fig_bar, use_container_width = True)
    
    # LINE CHART
    
    # top 10 keyword cols + Date col
    top_10_list = list(top_10["Keyword"])
    top_with_date = top_10_list.copy()
    top_with_date.append("Date")
    # keep only these columns
    g_new = graph_df[top_with_date]
    g = get_summed(g_new)
    # replace nans with 0s
    g = g.fillna(0)
    
    # reshape updated for line chart
    graph_shaped = pd.melt(g, id_vars = ["Date"], 
                              value_vars = top_10_list,
                              value_name = "Count")
    graph_shaped.columns = ["Date", "Keyword", "Count"]
    
    # plot line chart
    fig_line = px.line(graph_shaped, x = "Date", y = "Count", color = "Keyword",
                       title = "Usage Over Time")
    fig_line.update_layout(
        font_family = "sans serif",
        title_x = 0.5)
    fig_line.update_xaxes(
        tickformat = "%m/%d/%Y",
        type = "date",
        tickmode = "linear")
    
    # goes into right col
    c4.plotly_chart(fig_line, use_container_width = True)
    
    return True

#%%
if __name__ == "__main__":
    
    # putting dashboard in wide mode
    st.set_page_config(layout = 'wide')
    
    # use session state to prevent interctive widgets from disappearing
    session_state = SessionState.get(p = "", login = True)
    if session_state.p == "":
        password = st.sidebar.text_input("Password", type = 'password')
    elif session_state.p == "AnacostiaBID":
        password = "AnacostiaBID" 
        
    # in login, change session state of password if correct
    # also use session state for login to make disappear once
        # password is entered correctly
    if session_state.login:
        st.sidebar.button("Login")
        if password == 'AnacostiaBID':
            st.sidebar.success("Password Correct")
            session_state.p = "AnacostiaBID"
        elif password != "":
            st.sidebar.warning('Password Incorrect')  
            
    # if password correct, run dashboard
    if session_state.p == "AnacostiaBID":
        session_state.login = False
        news_dashboard()
        tweets_dashboard()
