#%%

def input_sensitive_data(data):

    """
    A function that handles user input for sensitive information, such as aws keys 
    and passwords
    """

    entered_data = input(f"Enter the {data}")

    return entered_data

DATABASE_TYPE = 'postgresql' 
DBAPI = 'psycopg2'
ENDPOINT = 'vg-webscraper-database-v2.cywt6wpqordr.eu-west-2.rds.amazonaws.com' # Change it for your AWS endpoint
USER = input_sensitive_data("postgres username")
PASSWORD = input_sensitive_data("postgres password")
PORT = 5432
DATABASE = 'postgres'

'''

AWS SSH command:

ssh -i "keypair1.pem" ubuntu@ec2-13-40-221-22.eu-west-2.compute.amazonaws.com

'''
from importlib_metadata import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver import ChromeOptions
import time
import pandas as pd
import uuid
import json
import os
import urllib.request
import boto3
import sqlalchemy
import psycopg2
from sqlalchemy import create_engine

'''
Below is the credentials for AWS. Look at your security credentials on AWS
to find these credentials.
'''

s3_client = boto3.client('s3', 
                    aws_access_key_id=input_sensitive_data("aws access key id"),
                    aws_secret_access_key=input_sensitive_data("aws secret access key"),
                    region_name=input_sensitive_data('aws region name')
)

def check_if_dir_exists(path, dir_name):

    '''
    Changes the current directory to path and checks if directory
    dir_name exists. If not, create it. Otherwise, do nothing.
    '''

    os.chdir(path)
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)
        print("Directory " , dir_name ,  "has been created ")
        return False
    else:    
        print("Directory " , dir_name ,  " already exists")
        return True


class Game:

    '''
    Class that holds any attributes and methods that relate to a
    scraped game. The attributes form a dict that holds all
    essential information about one game.
    '''

    number_of_games = 0

    def __init__(self, name, price, description, game_images):

        '''
        Initialise a game object.

        - id is incremented for each initialised game object.
        - name, price, description, game_images are all scraped.
        - uuid is randomly generated.
        - all of the above are stored in the game_dict, a
        dictionary that can be used to access any game info.

        '''


        self.name = name
        self.price = price
        self.description = description
        self.uuid = str(uuid.uuid4())
        Game.number_of_games += 1
        self.id = Game.number_of_games
        self.game_images = game_images
        self.game_dict = {"id": self.id, "uuid": self.uuid, "name": self.name, "price": self.price, "description": self.description, "game_images": self.game_images}    

class Scraper:

    '''
    Scraper class holds methods that are involved in web scraping.
    It also holds methods that are involved in taking info from
    the web and storing that info locally.
    '''

    def __init__(self, url):

        #Headless mode options below

        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'

        options = webdriver.ChromeOptions()
        options.headless = True
        options.add_argument(f'user-agent={user_agent}')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--disable-extensions")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        options.add_argument("--start-maximized")
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        #Headless mode options above

        time.sleep(5)

        '''
        Initialise the scraper. Chromedriver is used and url
        is the url that will be scraped.
        '''

        self.driver = webdriver.Chrome(executable_path="chromedriver", options=options) 
        self.url = url
        self.scrape_quantity = self.quantity_to_scrape()

    def quantity_to_scrape(self):

        while True:
            scrape_quantity = input("How many games do you want to scrape?")
            if scrape_quantity.isnumeric():
                return int(scrape_quantity)
            else:
                print("Invalid input")

    def driver_gets_url(self):
        self.driver.get(self.url)

    def accept_cookies(self): #Accept Cookies by clicking on 'accept cookies'
        
        '''
        Looks for the accept cookies button and clicks it.
        '''
        
        time.sleep(5)
        accept_cookies_button = self.driver.find_element_by_xpath('//*[@id="acceptAllButton"]')
        accept_cookies_button.click()

    def scroll_to_bottom(self):
        pass


    def scrape_game_info(self, links):

        '''
        Accesses each link. Checks for age restriction page. If
        it appears, the scraper moves on to the next game. If not,
        the scraper gathers the game info (name, price, description,
        images.) Using this information, a game object is created. As
        a result, the dict that holds the game info is created on
        object initialisation and these are stored in a list.
        '''

        game_dict_list = []        
        game_name_list = []

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

            '''
            check for a game description (no description is an indicator that
            the sample is not a game itself)
            '''
            
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@class="game_description_snippet"]'))
                )
                game_desc = self.driver.find_element_by_xpath('//*[@class="game_description_snippet"]').text

            except:
                print("No game description found. Game skipped")
                continue



            #name

            game_name = self.driver.find_element_by_xpath('//*[@id="appHubAppName"]').text

            #check for duplicate

            if game_name in game_name_list:
                print('Duplicate found - game skipped')
                continue
            else:
                game_name_list.append(game_name)

            #price

            try:
                game_price = self.driver.find_element_by_xpath('//*[@class="game_purchase_price price"]').text

            except:
                game_price = self.driver.find_element_by_xpath('//*[@class="discount_final_price"]').text

            
            #images

            image_link = self.driver.find_element_by_xpath('//*[@class="game_header_image_full"]')

            slideshow_image_class = self.driver.find_elements_by_xpath('//*[@class="highlight_strip_item highlight_strip_screenshot"]/img')

            game_images = []

            game_image = image_link.get_attribute('src')
            game_images.append(game_image)

            for image in slideshow_image_class:
                time.sleep(1)
                slideshow_image_link = image.get_attribute('src')
                game_images.append(slideshow_image_link)

            game = Game(game_name, game_price, game_desc, game_images)

            game_dict_list.append(game.game_dict)

            print(game.game_dict)

            self.scrape_quantity -= 1

            if self.scrape_quantity == 0:
                return game_dict_list

        return game_dict_list

    def get_game_links(self):

        '''
        The link to each game on the web page is added to a list. Done
        by finding the xpath of the game and getting the href. Also
        possible to declare a limit of number of items to scrape.
        '''

        items_to_scrape = self.scrape_quantity
        time.sleep(5)

        products1 = self.driver.find_elements_by_xpath('//*[@class="search_result_row ds_collapse_flag "]')
        products2 = self.driver.find_elements_by_xpath('//*[@class="search_result_row ds_collapse_flag  app_impression_tracked"]')

        products = products1 + products2

        print(products)

        game_links = []
        
        for product in products:
            time.sleep(1)
            link = product.get_attribute('href')
            game_links.append(link)
            print(link)


        return game_links

    def save_data_locally(self, dict_list): 

        '''
        Function made up of inner functions that work together to 
        store all of the game info locally.
        '''

        def create_folder(folder_name): 

            '''
            Creates a folder to store datapoint folders in (each
            game that has been scraped)
            '''
            #1. Create a folder called raw_data in the root of the project

            raw_data_dir = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/'

            dir_name = folder_name

            check_if_dir_exists(raw_data_dir, dir_name)

            game_name_folder = 'games_stored'

            check_if_dir_exists(raw_data_dir, game_name_folder)

        def create_datapoint_folder():

            '''
            Within the raw data folder, a datapoint folder is
            created. Here, the game info for each game is stored.
            Images are stored in an images folder. 
            '''

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

            '''
            Dump the dict for each game into a json file.
            '''

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

            '''
            Access the images for each game using the list of links
            stored in the game dict and download these images.
            '''

            for datapoint in dict_list:
                image_links = datapoint["game_images"]
                current_id = datapoint["id"]
                current_id = str(current_id)
                images_path = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data/' + current_id + '/images'

                for image_index in range(0, len(image_links)):
                    os.chdir(images_path)
                    file_name = str(image_index) + '.jpg'
                    urllib.request.urlretrieve(image_links[image_index], file_name)


        create_folder('raw_data')
        create_datapoint_folder()
        save_datapoint_dicts()
        download_images()

    def upload_to_aws(self):

        """
        Upload each json file and image to AWS, retaining the file
        structure. 
        """

        raw_data_dir = '/home/dg0834/Desktop/AiCore_Python/projects/webscraper/raw_data'

        os.chdir(raw_data_dir)

        for dirpath, dirname, filename in os.walk(raw_data_dir):
            print(f'Current Path: {dirpath}')
            print(f'Directories: {dirname}')
            print(f'Files: {filename} \n')


            for file in filename:
                os.chdir(dirpath)
                response = s3_client.upload_file(file, 'vg-webscraper', str(dirpath) + '/' + file)

    def store_data_in_dataframe(self, game_dict_list):

        """
        For each game, store the game info in a pandas dataframe.
        """

        df = pd.DataFrame(game_dict_list)

        return df

    def dataframe_to_sql():

        """
        Converts the pandas dataframe containing the game info into an sql
        database.
        """

        #1. 
        pass

    def run_scraper(self):

        '''
        Calls a number of methods, with the overall goal to scrape
        the necessary game info and store this info locally.
        '''

        self.driver_gets_url()
        self.accept_cookies()
        game_links = self.get_game_links()
        game_dict_list = self.scrape_game_info(game_links)
        return game_dict_list

    def stop_scraper(self):

        '''
        Once scraping and storing is finished, stop the driver.
        '''

        time.sleep(10)
        self.driver.close()


if __name__ == '__main__':

    url = 'https://store.steampowered.com/search/?sort_by=Released_DESC&filter=topsellers'

    scraper = Scraper(url)
    game_dict_list = scraper.run_scraper()
    scraper.save_data_locally(game_dict_list)
    df = scraper.store_data_in_dataframe(game_dict_list)
    scraper.stop_scraper()

    scraper.upload_to_aws()

    engine = create_engine(f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{ENDPOINT}:{PORT}/{DATABASE}")

    engine.connect()

    df.to_sql('game_dataset', engine, if_exists='replace')

# %%
