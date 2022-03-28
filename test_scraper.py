import unittest
import sys
import free_to_play_webscraper
import os

class Test_Scraper(unittest.TestCase):

    def setUp(self):
        url = 'https://store.steampowered.com/genre/Free%20to%20Play/' 
        self.scraper = free_to_play_webscraper.Scraper('https://store.steampowered.com/genre/Free%20to%20Play/')
        self.scraper.driver_gets_url()


    def tearDown(self):
        self.scraper.stop_scraper()

    def test_scrape_game_info(self): 
        result = self.scraper.scrape_game_info(['https://store.steampowered.com/app/1105130/Arcadius/'])
        self.assertEqual(result[0]["name"], "Arcadius")

    def test_get_game_links(self): #check that a link is returned
        result = self.scraper.get_game_links(2)

        print(result)

        self.assertIn('https://store.steampowered.com/', result[0])

    def test_run_scraper(self):
        result = self.scraper.run_scraper()
        itemType = type(result[0])
        self.assertEqual(itemType, dict)


class Test_Directory(unittest.TestCase):

    def test_check_if_dir_exists(self):
        result = free_to_play_webscraper.check_if_dir_exists("/home/dg0834/Desktop/AiCore_Python/projects/webscraper/dummy_folder/", "dummy_file_1.txt")
        self.assertEqual(result, True)


if __name__ == '__main__':
    unittest.main()

