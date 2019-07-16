import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import requests

from utils.file_helper import get_cadastres
from utils.file_helper import write_apartments

apartments = []
retry_cadastres = []
error = 0
not_found = 0
current = 0
retry = False


def fetch(session, cadastre, city, total):
    url = f"https://kadastrmap.ru/new_api.php?q={cadastre}&f238774bdb830a42bff5ef2d34c0126=771"
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
    sleep(0.3)
    with session.get(url, headers=headers) as response:
        try:
            if response.status_code != 200:
                print('не считано по коду: %d' % response.status_code)
                if not retry:
                    global error
                    error += 1
                    retry_cadastres.append(cadastre)
            else:
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
                    global current
                    current += 1
                    print('считано %d/%d' % (current, total))
                if retry:
                    k = retry_cadastres.index(cadastre)
                    retry_cadastres.pop(k)

        except json.JSONDecodeError:
            print('Упал на url::' + url)
        except KeyError:
            global not_found
            not_found += 1
            print('Вот тут есть JSON, но нет info::' + url)


async def worker_function(cadastres, city):
    with ThreadPoolExecutor(max_workers=6) as executor:
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


def grab_apartments(cities):
    for city in cities:
        global current
        current = 0
        try:
            cadastres = get_cadastres(f"{os.getcwd()}/out/cadastres", city)
            print('Всего квартир найдено: %d' % len(cadastres))

            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(worker_function(cadastres=cadastres, city=city))
            loop.run_until_complete(future)

            print('Выгружаю в файл %d записей' % current)

            write_apartments(f"{os.getcwd()}/out/apartments", city, apartments)
            apartments.clear()

            print('По кадастровым номерм не найдено %d квартир' % not_found)
            print('По кадастровым номерам не обработано %d квартир' % error)

        except Exception as e:
            print(f"Какая-то ошибка: {e}")
        finally:
            if len(apartments) != 0:
                print('Выгружаю в файл %d записей' % len(apartments))
                write_apartments(f"{os.getcwd()}/out/apartments", city, apartments)
                apartments.clear()
                print('По кадастровым номерм не найдено %d квартир' % not_found)
                print('По кадастровым номерам не обработано %d квартир' % error)
