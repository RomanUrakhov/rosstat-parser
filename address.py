import os
import requests
from utils.file_helper import write_addresses


def grab_addresses(cities):
    global response
    url = 'http://dom.mingkh.ru/api/houses'
    for city in cities:
        data = {
            'current': 1,
            'rowCount': -1,
            'searchPhrase': '',
            'region_url': cities[city],
            'city_url': city
        }
        response = requests.post(url, data)
        if response:
            json_obj = response.json()
            houses = json_obj['rows']

            addresses = [house['address'] for house in houses]
            print(f"В городе {city} найдено {len(addresses)} адресов. Записываю в файл...")
            write_addresses(f"{os.getcwd()}/out/addresses", city, addresses)

        else:
            continue
    response.close()
