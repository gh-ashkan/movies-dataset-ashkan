import sys
from multiprocessing import Pool
from threading import Thread

from config import OBJECT_CLASS
from crawl import LinkCrawler, DataCrawler


def my_pool(link):
    url, page_number = link
    crawler = LinkCrawler(url=url, number_page=page_number)
    crawler.start(store=True)


def start_find_links():
    url = "https://www.f2m.top/category/{}/page/"
    links = []
    number_pages = None

    while True:
        try:
            number_pages = int(input(f"enter number of page (1-10): "))
        except ValueError as ex:
            print(f"ERROR!!!\n{ex}\n\t-> please enter integer.\n{'--'*20}")
            continue

        if number_pages in range(1, 11):
            break
        else:
            print(f"enter number page in range (1 to 10).\n{'--'*20}")

    for genre in OBJECT_CLASS.values():
        links.append([url.format(genre), number_pages])

    pool = Pool(4)
    with pool:
        pool.map(my_pool, links)


if __name__ == "__main__":
    switch = sys.argv[1]
    if switch == "find_links":
        start_find_links()
    elif switch == "extract_page":
        data = DataCrawler()
        data.start(store=True)