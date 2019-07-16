import asyncio
import csv
import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests

from utils.file_helper import get_addresses
from utils.file_helper import write_cadastres

cadastres = []
current = 0


def address_parse(address):
    street_type = {
        'ул': 'улица',
        'пр-кт': 'проспект',
        'пер': 'переулок',
        'б-р': 'бульвар',
        'тракт': 'тракт',
        'ст': 'станция',
        'ш': 'шоссе'
    }
    settlement = {'п': 'поселок', 'мкр': 'мкр', 'снт': 'снт', 'с': 'село'}
    region_dict = {
        'Пермь': 'Пермский',
        'Екатеринбург': 'Свердловская',
        'Пенза': 'Пензенская',
        'Томск': 'Томская',
        'Тверь': 'Тверская',
        'Ижевск': 'Удмуртская',
        'Иркутск': 'Иркутская'
    }
    # приоритет: город[->населенный пункт]->улица->дом[->корпус/строение]
    # address_ddt=г+Екатеринбург,+поселок+Садовый,+ул+Верстовая,+д+8
    # address_ddt=г+Екатеринбург,+ул+Чекистов,+д+1+
    # address_ddt=г+Екатеринбург,+ул+Чкалова,+д+121+стр+1
    result = {
        'c_number': 'c_number',
        'address_ddt': '',
        'region_ddt': '',
        'city_ddt': '',
        'settlement_ddt': '',
        'street_type_full_ddt': '',
        'street_ddt': '',
        'house_ddt': '',
        'block_type_full_ddt': '',
        'block_ddt': ''
    }
    # address строка типа: ул. Щорса, д. 35, Екатеринбург
    # или: п. Садовый, ул. Сибирка, д. 32, Екатеринбург
    parts = re.split(r"\. |, ", address)

    result['address_ddt'] = 'г+%s,+' % parts[-1]
    result['region_ddt'] = region_dict.get(parts[-1])
    result['city_ddt'] = parts[-1]

    if parts[0] in settlement:

        if parts[2] not in street_type:
            result['street_type_full_ddt'] = settlement.get(parts[0])
            if ' ' in parts[1]:
                result['street_ddt'] = '+'.join(parts[1].split(' '))
            else:
                result['street_ddt'] = parts[1]
            result['address_ddt'] += '%s+%s,' % (result['street_type_full_ddt'], result['street_ddt'])
            k = [i for i, part in enumerate(parts) if re.search(r'\d+/\w+', part)]
            if len(k) != 0:
                addr_values = parts[k[0]].split('/')
                result['address_ddt'] = result['address_ddt'] + '%s+%s+%s+%s' % (
                    'д', addr_values[0], 'к', addr_values[1])
                result['block_type_full_ddt'] = 'корпус'
                result['block_ddt'] = addr_values[1]
                result['house_ddt'] = addr_values[0]
            else:
                result['address_ddt'] += '%s+%s' % (parts[2], parts[3])
                result['house_ddt'] = parts[3]
        else:
            if ' ' in parts[1]:
                result['settlement_ddt'] = '+'.join(parts[1].split(' '))
            else:
                result['settlement_ddt'] = parts[1]

            result['address_ddt'] += '%s+%s,+' % (settlement.get(parts[0]), result['settlement_ddt'])

            result['street_type_full_ddt'] = street_type.get(parts[2])
            if ' ' in parts[3]:
                result['street_ddt'] = '+'.join(parts[3].split(' '))
            else:
                result['street_ddt'] = parts[3]
            if parts[2] in ['пер', 'тракт']:
                result['address_ddt'] += '%s+%s,+' % (result['street_ddt'], parts[2])
            else:
                result['address_ddt'] += '%s+%s,+' % (parts[2], result['street_ddt'])

            k = [i for i, part in enumerate(parts) if re.search(r'\d+/\w+', part)]
            if len(k) != 0:
                addr_values = parts[k[0]].split('/')
                result['address_ddt'] = result['address_ddt'] + '%s+%s+%s+%s' % (
                    'д', addr_values[0], 'к', addr_values[1])
                result['block_type_full_ddt'] = 'корпус'
                result['block_ddt'] = addr_values[1]
                result['house_ddt'] = addr_values[0]
            else:
                try:
                    result['address_ddt'] += '%s+%s' % (parts[4], parts[5])
                    result['house_ddt'] = parts[5]
                except IndexError as e:
                    print('ошибка при адресе: ' + address)
                    print(result['address_ddt'])

    elif parts[0] in street_type:

        result['street_type_full_ddt'] = street_type.get(parts[0])
        if ' ' in parts[1]:
            result['street_ddt'] = '+'.join(parts[1].split(' '))
        else:
            result['street_ddt'] = parts[1]
        if parts[0] in ['пер', 'тракт']:
            result['address_ddt'] += '%s+%s,+' % (result['street_ddt'], parts[0])
        else:
            result['address_ddt'] += '%s+%s,+' % (parts[0], result['street_ddt'])

        k = [i for i, part in enumerate(parts) if re.search(r'\d+/\w+', part)]
        if len(k) != 0:
            addr_values = parts[k[0]].split('/')
            result['address_ddt'] += '%s+%s+%s+%s' % ('д', addr_values[0], 'к', addr_values[1])
            result['block_type_full_ddt'] = 'корпус'
            result['block_ddt'] = addr_values[1]
            result['house_ddt'] = addr_values[0]
        else:
            result['address_ddt'] += '%s+%s' % (parts[2], parts[3])
            result['house_ddt'] = parts[3]

    try:
        k = list.index(parts, 'к')
        if parts[k + 1].isdigit():
            result['block_type_full_ddt'] = 'корпус'
            result['block_ddt'] = parts[k + 1]
            result['address_ddt'] += '+%s+%s' % (parts[k], parts[k + 1])
        else:
            result['house_ddt'] += '%s' % parts[k + 1]
            result['address_ddt'] += '%s' % parts[k + 1]
    except ValueError as e:
        pass

    try:
        k = list.index(parts, 'стр')
        if parts[k + 1].isdigit():
            result['block_type_full_ddt'] = 'строение'
            result['block_ddt'] = parts[k + 1]
            result['address_ddt'] += '+%s+%s' % (parts[k], parts[k + 1])
        else:
            result['house_ddt'] += parts[k + 1]
            result['address_ddt'] += '%s' % parts[k + 1]
    except ValueError as e:
        pass

    result = {k: v for k, v in result.items() if v != ''}

    return result


def fetch(session, url, city, total):
    with session.get(url=url) as response:
        if response.status_code != 200:
            print("FAILURE::{0}".format(url))
        else:
            global current
            current += 1
            print('считано %d/%d адресов' % (current, total))
            if not response.text == '':
                data = response.text
                unique = set(re.findall(r'\d{2}:\d{2}:\d{6,7}:\d+', data))
                cadastres.extend(list(unique))


async def worker_function(urls, city):
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, url, city, len(urls))
                ) for url in urls
            ]
            for response in await asyncio.gather(*tasks):
                pass


def grab_cadastres(cities):
    for city in cities:
        global current
        current = 0
        addresses = get_addresses(f"{os.getcwd()}/out/addresses", city)
        print('Обработка города %s, всего адресов: %d' % (city, len(addresses)))
        try:
            # получаем список url каждого дома в городе city
            urls = []
            for address in addresses:
                data = address_parse(address)
                url = 'https://rosegrn.su/api/FormStep2.php?'
                for key in data:
                    url += '%s=%s&' % (key, data.get(key))
                url = url[:-1]
                urls.append(url)
            # Инициализируем асинхронную функцию worker_function
            loop = asyncio.get_event_loop()
            future = asyncio.ensure_future(worker_function(urls=urls, city=city))
            loop.run_until_complete(future)

        except requests.exceptions as e:
            pass
        finally:
            write_cadastres(f"{os.getcwd()}/out/cadastres", city, cadastres)
