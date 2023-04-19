import json
import pprint
import requests
from pymongo import MongoClient
from config import STORAGE
from mongo import MongoDatabase
from storage import FileStore, MongoStore
from multiprocessing import Pool
from threading import Thread
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from parser import AdvertisementPageParser


class CrawlBase(ABC):
    def __init__(self):
        self.storage = self.__set_storage()

    @staticmethod
    def __set_storage():
        if STORAGE == "mongo":
            return MongoStore()
        return FileStore()

    @abstractmethod
    def start(self, store=False):
        pass

    @abstractmethod
    def store(self, datas, filename):
        pass

    @staticmethod
    def get(link):
        try:
            response = requests.get(link)
        except requests.HTTPError:
            return None
        if response.status_code == 200:
            return response
        return None


class LinkCrawler(CrawlBase):
    def __init__(self, url, number_page=1):
        self.url = url
        self.number_page = number_page
        self.__links_movie = list()
        super().__init__()

    def my_thread(self, link):
        response = self.get(link)
        self.__links_movie.extend(self.find_links(response.text))

    def start(self, store=False):
        start_page = 1
        urls = list()
        for i in range(self.number_page):
            urls.append(self.url + str(start_page))
            start_page += 1

        threads = []
        for link in urls:
            tr = Thread(target=self.my_thread, args=(link,))
            threads.append(tr)
            tr.start()

        for i in threads:
            i.join()

        if store:
            self.store(self.__links_movie, 'movies_url')

        print(f"find_links executed successfully -> url: {self.url}.")

    def store(self, datas, filename, *args):
        self.storage.store(datas, filename)

    @staticmethod
    def find_links(html_doc):
        soup = BeautifulSoup(html_doc, 'html.parser')
        articles = soup.find_all(
            'div', attrs={'class': 'col mb-3 mb-sm-0 col-sm-auto m-link px-0'}
        )

        links_move = [
            {'link': article.find('a').get('href'), "flag": False} for article in articles
        ]

        return links_move


class DataCrawler(CrawlBase):
    def __init__(self, search_collection="movies_url", store=False):
        self.__links = self.__load_links(search_collection)
        self.parse = AdvertisementPageParser()
        self.store_bool = store
        self.datas = list()
        super().__init__()

    def my_multi_processing(self, link):
        response = self.get(link[0])
        if response is not None:
            self.datas.append(self.parse.parse(response.text, link))

    def start(self, store=False):
        self.store_bool = store

        # for link in self.__links:
        #     response = self.get(link)
        #     print(response)
        #     if response is not None:
        #         my_data = self.parse.parse(response.text)
        #         if self.store_bool:
        #             print(f"name: {my_data.get('name')}")
        #             self.store(
        #                 datas=my_data,
        #             )

        # pool = Pool(4)
        # with pool:
        #     pool.map(self.my_multi_processing, self.__links)

        if self.__links:
            threads = []
            for link in self.__links:
                tr = Thread(target=self.my_multi_processing, args=(link,))
                threads.append(tr)
                tr.start()

            for thread in threads:
                thread.join()

            if self.store_bool and self.datas:
                response = self.store(datas=self.datas)
                print(response)
        else:
            print("There are no links to search")

    def store(self, datas, *args):
        return self.storage.store(datas, 'movies_information')

    @staticmethod
    def __load_links(search_collection="movies_url"):
        links = []

        if STORAGE == "mongo":
            mongodb = MongoDatabase()
            collection = getattr(mongodb.database, search_collection)
            for link in collection.find():
                if not link["flag"]:
                    collection.update_one({"link": link["link"]},
                                          {"$set": {"flag": True}})
                    links.append((link["link"], link["_id"]))
        elif STORAGE == 'file':
            with open("fixtures/movies_link.json", "r") as f:
                links = json.loads(f.read())
        if links:
            return links
        return None
