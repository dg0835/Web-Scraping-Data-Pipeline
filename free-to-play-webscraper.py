#%%

from email.mime import image
from fileinput import filename
from lib2to3.pgen2 import driver
from os import link
from unittest import case
from xml.dom.minidom import Element
from importlib_metadata import os
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import numpy as np
import uuid
import json
import os
import urllib.request

from soupsieve import select

def check_if_dir_exists(path, dir_name):
    os.chdir(path)
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        print("Directory " , dir_name ,  "has been created ")
    else:    
        print("Directory " , dir_name ,  " already exists")

class Game:

    number_of_games = 0

    def __init__(self, name, price, description, game_images):

        self.name = name
        self.price = price
        self.description = description
        self.uuid = str(uuid.uuid4())
        Game.number_of_games += 1
        self.id = Game.number_of_games
        self.game_images = game_images
        self.game_dict = {"id": self.id, "uuid": self.uuid, "name": self.name, "price": self.price, "description": self.description, "game_images": self.game_images}    

class Scraper:
    def __init__(self, url):
        self.driver = webdriver.Chrome() 
        self.url = url

    def driver_gets_url(self):
        self.driver.get(self.url)

    def accept_cookies(self): #Accept Cookies by clicking on 'accept cookies'
        time.sleep(5)
        accept_cookies_button = self.driver.find_element_by_xpath('//*[@id="acceptAllButton"]')
        accept_cookies_button.click()

    def scrape_game_info(self, links):

        game_dict_list = []        

        for link in links:
            time.sleep(1.5)
            self.driver.get(link)

            #Check for age restriction

            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@class="btn_addtocart"]'))
                )
            except:
                print("Age restricted game skipped")
                continue


            #name

            game_name = self.driver.find_element_by_xpath('//*[@id="appHubAppName"]').text

            #price

            try:
                game_price = self.driver.find_element_by_xpath('//*[@class="game_purchase_price price"]').text

            except:
                game_price = self.driver.find_element_by_xpath('//*[@class="discount_final_price"]').text

            
            #desc

            game_desc = self.driver.find_element_by_xpath('//*[@class="game_description_snippet"]').text

            image_link = self.driver.find_element_by_xpath('//*[@class="game_header_image_full"]')

            game_images = []

            game_image = image_link.get_attribute('src')

            game_images.append(game_image)

            game = Game(game_name, game_price, game_desc, game_images)

            game_dict_list.append(game.game_dict)

            print(game.game_dict)

        return game_dict_list

    def get_game_links(self):

        items_to_scrape = 3
        time.sleep(5)

        products1 = self.driver.find_elements_by_xpath('//*[@class="tab_item  "]')
        products2 = self.driver.find_elements_by_xpath('//*[@class="tab_item   app_impression_tracked"]')

        game_links = []


        for product in products1:

            if items_to_scrape == 0:
                break
            items_to_scrape -= 1
            time.sleep(1)
            link = product.get_attribute('href')
            game_links.append(link)
            print(link)

        for product in products2:

            if items_to_scrape == 0:
                break
            time.sleep(1)
            link = product.get_attribute('href')
            game_links.append(link)
            print(link)

        return game_links

    def save_data_locally(self, dict_list): 

        def create_raw_data_folder(): 
            #1. Create a folder called raw_data in the root of the project

            project_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/'

            dir_name = 'raw_data'

            check_if_dir_exists(project_path, dir_name)

            game_name_folder = 'games_stored'

            check_if_dir_exists(project_path, game_name_folder)

        def create_datapoint_folder():
            #2. For each datapoint, create a folder with a name equal to id
            dir_name = 'raw_data'
            raw_data_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data'

            for datapoint in dict_list:
                current_id = datapoint["id"]
                current_id = str(current_id)

                check_if_dir_exists(raw_data_path, current_id)

                datapoint_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data/' + current_id

                image_folder_name = 'images'

                check_if_dir_exists(datapoint_path, image_folder_name)



        def save_datapoint_dicts():
            #3. Within the folder, save the dict in a file called data.json
            for datapoint in dict_list:
                current_id = datapoint["id"]
                current_id = str(current_id)
                datapoint_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data/' + current_id
                os.chdir(datapoint_path)

                with open('JSON_test.json', mode='w') as f:
                    json.dump(datapoint, f) 
            
                os.chdir('..')

        def download_images(): #Download .jpg images 
            for datapoint in dict_list:
                image_links = datapoint["game_images"]
                current_id = datapoint["id"]
                current_id = str(current_id)
                images_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data/' + current_id + '/images'

                for image_index in range(0, len(image_links)):
                    os.chdir(images_path)
                    file_name = current_id + '.jpg'
                    urllib.request.urlretrieve(image_links[image_index], file_name)


        create_raw_data_folder()
        create_datapoint_folder()
        save_datapoint_dicts()
        download_images()

    def run_scraper(self):
        self.driver_gets_url()
        self.accept_cookies()
        game_links = self.get_game_links()
        game_dict_list = self.scrape_game_info(game_links)
        return game_dict_list

    def stop_scraper(self):
        time.sleep(10)
        self.driver.close()


if __name__ == '__main__':

    url = 'https://store.steampowered.com/genre/Free%20to%20Play/'

    scraper = Scraper(url)
    game_dict_list = scraper.run_scraper()
    scraper.save_data_locally(game_dict_list)
    scraper.stop_scraper()

    
# %%

#1. Create a folder called raw_data
#2. Change current directory to the raw_data folder
#3. For each dict in dict list, create a folder equal to the 
#datapoint id and name the folder that.


import json
import os

project_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/'

os.chdir(project_path)

dir_name = 'raw_data'

if not os.path.exists(dir_name):
    os.mkdir(dir_name)
    print("Directory " , dir_name ,  "has been created ")
else:    
    print("Directory " , dir_name ,  " already exists")

os.chdir(dir_name)

test_dict = [{'a': 1, 'b': 2, 'c': 3}, {'d': 4, 'e': 500}]

def create_folder_with_json(my_dict):

    with open('JSON_test.json', mode='w') as f:
        json.dump(my_dict, f) 

create_folder_with_json(test_dict)


# %%
