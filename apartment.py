import asyncio
import csv
import json
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import requests

from utils.time_check import Profiler
from cadastr import grab_cadastres

# cities = {
#     'perm': 'permskiy-kray',
#     'ekaterinburg': 'sverdlovskaya-oblast',
#     'penza': 'penzenskaya-oblast',
#     'tver': 'tverskaya-oblast',
#     'tomsk': 'tomskaya-oblast'
# }

cities = {
    'perm': 'permskiy-kray'
}

apartments = []
retry_cadastres = []
not_found = 0
current = 0


def fill_file(city):
    dirname = os.getcwd() + '/out/apartments'
    try:
        os.mkdir(dirname)
    except OSError as e:
        pass
    filename = dirname + '/' + city + '.tsv'
    try:
        with open(filename, mode='a', encoding='UTF-8', newline='') as output_file:
            writer = csv.DictWriter(output_file, delimiter='\t', fieldnames=apartments[0].keys())
            if os.stat(filename).st_size == 0:
                writer.writeheader()
            for apartment in apartments:
                writer.writerow(apartment)
    except IOError:
        print('I/O Error')


def read_file(city):
    dirname = os.getcwd() + '/out/cadastres'
    filename = dirname + '/' + city + '.csv'
    cadastres = []
    try:
        with open(filename, mode='r', encoding='UTF-8', newline='') as input_file:
            reader = csv.reader(input_file, lineterminator='\n')
            for cadastre in reader:
                cadastres.append(cadastre[0])
    except IOError:
        print("I/O Error")
    return cadastres


def fetch(session, cadastre, city, total):
    url = 'https://kadastrmap.ru/new_api.php?q=' + cadastre + '&f238774bdb830a42bff5ef2d34c0126=771'
    headers = {
        'Host': 'kadastrmap.ru',
        'User-Agent': 'User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://kadastrmap.ru/?kad_no=' + cadastre,
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'TE': 'Trailers'
    }
    sleep(0.4)
    with session.get(url, headers=headers) as response:
        try:
            if response.status_code != 200:
                print('не считано по коду: %d' % response.status_code)
                retry_cadastres.append(cadastre)
            else:
                global current
                current += 1
                print('считано %d/%d' % (current, total))
                data = response.json()['info']
                if 'дом' not in data['objectName']:
                    a_type = data['objectName']
                    a_type = str.strip(a_type)
                    a_type = str.lower(a_type)
                    a_type = str.replace(a_type, ' №', '')
                    a_type = str.replace(a_type, '-комнатная ', '')
                    apt_info = {
                        'Тип': a_type,
                        'Кадастровый номер': data['objectCn'],
                        'Адрес': data['mergedAddress'],
                        'Площадь': data['areaValue'],
                        'Кадастровая стоимость': data['cadCost']
                    }
                    apartments.append(apt_info)

        except json.JSONDecodeError:
            print('Упал на url::' + url)
        except KeyError:
            global not_found
            not_found += 1
            print('Вот тут есть JSON, но нет info::' + url)


async def worker_function(cadastres, city):
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, cadastre, city, len(cadastres))
                ) for cadastre in cadastres
            ]
            for response in await asyncio.gather(*tasks):
                pass


def main():
    grab_cadastres(cities)
    for city in cities:
        try:
            cadastres = read_file(city=city)
            print('Всего квартир найдено: %d' % len(cadastres))
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(worker_function(cadastres=cadastres, city=city))
            loop.run_until_complete(future)

            # Нужно добавить постобработку запросов, которые улетели по 503 коду (рогонять через retry_cadastres)
            # if len(retry_cadastres) > 0:
            #     loop = asyncio.get_event_loop()
            #     future = asyncio.ensure_future(worker_function(cadastres=retry_cadastres, city=city))
            #     loop.run_until_complete(future)

        except requests.exceptions as e:
            pass
        finally:
            print('Выгружаю в файл')
            fill_file(city)
            print('По кадастровым номера не найдено %d квартир' % not_found)


if __name__ == '__main__':
    with Profiler() as p:
        main()
