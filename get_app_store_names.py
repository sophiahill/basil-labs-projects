# -*- coding: utf-8 -*-
"""
@author: sophi
"""

#%%
import pandas as pd

from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from time import sleep
import re

#%%
###################################################################
# APP STORE 
###################################################################

## STEPS FOR GETTING APP NAMES ##
    # using https://apps.apple.com/us/genre/ios-books/id6018?letter=A&page=1#page
    
# app_names = set
# 1. get links for categories
# 2. on each category page, get alpha links
        # 3. on each alpha page, get page number links
            # 4. on each page to scrape, add each app name to set
#%%
# lil bot
def initialize_bot():
    chrome_options = Options()
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-backgrounding-occluded-windows')
    chrome_options.add_argument('--disable-background-timer-throttling')
    chrome_options.add_argument('--disable-renderer-backgrounding')
    chrome_options.add_argument('detach:True')

    return webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

# get text from list of web elements
def get_text(elem_list):
    return([x.text for x in elem_list])

#%%

def get_app_names(cat_link):
    ### 2. on each category page ###
    cat_list = []
    bot.get(cat_link)
    sleep(1) 
    
    ### 2b. get alpha links ###
    alpha_container = "//*[@id='selectedgenre']/ul[@class='list alpha']"
    alpha_hrefs_x = ".//a[contains(@href, 'letter')]"
    # alpha container + hrefs
    alphabet = bot.find_element_by_xpath(alpha_container)
    alpha_hrefs = alphabet.find_elements_by_xpath(alpha_hrefs_x)
    # list of links for each letter
    alpha_links = [x.get_attribute("href") for x in alpha_hrefs]   
        
    ### 3a. on each alpha page ###
    for alpha_link in alpha_links:
        bot.get(alpha_link)
        sleep(.5)
        
        ### 3b. get page number links ###
        num_container = "//*[@id='selectedgenre']/ul[@class='list paginate']"
        num_hrefs_x = ".//a[contains(@href, 'page')]"
        # num container + hrefs
        numbers = bot.find_element_by_xpath(num_container)
        num_hrefs = numbers.find_elements_by_xpath(num_hrefs_x)
        # list of links for each letter
        num_links = [x.get_attribute("href") for x in num_hrefs] 
        
        for num_link in num_links:
            bot.get(num_link)
            sleep(.5)
            
            ### 4. add each app name to set ###
            names_container = "//*[@id='selectedgenre']/div[@id='selectedcontent']"
            paths = [".//div[@class='column first']/ul/li/a", 
                            ".//div[@class='column']/ul/li/a",
                            ".//div[@class='column last']/ul/li/a"]
    
            # names container + text
            all_cols = bot.find_element_by_xpath(names_container)
            elems = [all_cols.find_elements_by_xpath(p) for p in paths]
            listed_names = list(map(get_text, elems))
            names = [name for col in listed_names for name in col]
            
            cat_list += names
            print(cat_list[:-10])
        
        print(alpha_link)

    return(cat_list)
    
    
#%%

if __name__ == "__main__":
    # start up the bot
    bot = initialize_bot()
    bot.get("https://apps.apple.com/us/genre/ios-books/id6018")
    
    ### 1. get names, links for categories ### 
    cats_container = "//*[@id='genre-nav']/div/ul"
    cat_hrefs_x = ".//a[contains(@href, 'apps.apple.com/us/genre')]"
    # categories container + hrefs
    container = bot.find_element_by_xpath(cats_container)
    cat_hrefs = container.find_elements_by_xpath(cat_hrefs_x)
    # list of links for each category
    cat_links = [x.get_attribute("href") for x in cat_hrefs]
    
    # get names of categories for dict keys
    cat_names = [re.search("ios-(.+?)/", x).group(1) for x in cat_links]
    empties = [[] for n in range(len(cat_names))]
    # assign
    cat_dict = {k:v for (k,v) in zip(cat_names, empties)}
    
    # cat name to its link
    cat_stuff = list(zip(cat_names, cat_links))
    
    # do the thing :o
        # get a dict of {category name: all app names in that category}
    for (cn, cl) in cat_stuff:
        cat_dict[cn] = get_app_names(cl)
    
    # put together
    as_names_df = pd.DataFrame(cat_dict.items(),
                               columns = cat_dict.keys())
    as_names_df.rename(columns = {as_names_df.columns[0]:"App Name"}, inplace = True)
    
    save_path = r"C:\Users\sophi\Documents\basil_labs\as_names.csv.gz"
    as_names_df.to_csv(save_path, index = False, compression = "gzip")
    
    