import logging

import requests
from bs4 import BeautifulSoup

import templates


def logger_formatter(logger):
    """ Apply custom settings to the logger """
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_map_thumbnails():
    """ Make a dict[map_name] = img_url for the map thumbnails. Scrap it from a source that's somewhat complete.

    Only at startup.

    """
    map_thumbnails = {}
    base_url = 'https://wiki.unknownworlds.com'
    map_list_url = base_url + '/ns2/Map_Index'

    logger.info(templates.LOG_GET.format(map_list_url))
    map_index = requests.get(map_list_url).text

    soup = BeautifulSoup(map_index, 'html.parser')
    tables = soup.find_all('table', {'class': 'wikitable'})
    for table in tables:
        map_rows = table.find_all('tr')
        for map_row in map_rows:
            tds = map_row.find_all('td')
            try:
                map_name = tds[1].find('a').text
                map_url = base_url + tds[-1].find('img').get('src')
            except:
                pass
            else:
                map_thumbnails[map_name] = map_url
    return map_thumbnails

def steam64_ns2id(steam64):
    i_server = 0 if steam64 % 2 == 0 else 1
    steam64 -= i_server
    if steam64 > 76561197960265728:
        steam64 -= 76561197960265728
    steam64 /= 2

    return int(steam64*2 + i_server)

logger = logging.getLogger(__name__)
logger_formatter(logger)

map_thumbnails = load_map_thumbnails()
