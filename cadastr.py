from bs4 import BeautifulSoup
import requests
import base64
import os
import re
from enum import Enum
from address import get_addresses
from address import grab_addresses

url = 'https://rosegrn.su/api/FormStep2.php'


def fill_files(city, cadastres):
    with open(os.getcwd() + '/out/cadastres/' + city + '.txt', mode='w', encoding='UTF-8') as output_file:
        output_file.writelines("%s\n" % cadastre for cadastre in cadastres)


def address_parse(address):
    street_type = {
        'ул': 'улица',
        'пр-кт': 'проспект',
        'пер': 'переулок',
        'б-р': 'бульвар',
        'тракт': 'тракт',
        'ст': 'станция'
    }
    settlement = {'п': 'поселок', 'мкр': 'мкр', 'снт': 'снт', 'с': 'село'}
    region_dict = {
        'Пермь': 'Пермский',
        'Екатеринбург': 'Свердловская'
    }
    # приоритет: город[->населенный пункт]->улица->дом[->корпус/строение]
    # address_ddt=г+Екатеринбург,+поселок+Садовый,+ул+Верстовая,+д+8
    # address_ddt=г+Екатеринбург,+ул+Чекистов,+д+1+
    # address_ddt=г+Екатеринбург,+ул+Чкалова,+д+121+стр+1
    result = {
        'c_number': 'c_number',
        'address_ddt': None,
        'region_ddt': None,
        'city_ddt': None,
        'settlement_ddt': None,
        'street_type_full_ddt': None,
        'street_ddt': None,
        'house_ddt': None,
        'block_type_full_ddt': None,
        'block_ddt': None
    }
    # address строка типа: ул. Щорса, д. 35, Екатеринбург
    # или: п. Садовый, ул. Сибирка, д. 32, Екатеринбург
    parts = re.split(r"\. |, ", address)

    result['address_ddt'] = 'г+%s,+' % parts[-1]
    result['region_ddt'] = region_dict.get(parts[-1])
    result['city_ddt'] = parts[-1]

    if parts[0] in settlement:

        result['settlement_ddt'] = parts[1]
        result['address_ddt'] = result['address_ddt'] + '%s+%s,+' % (settlement.get(parts[0]), parts[1])
        result['street_type_full_ddt'] = street_type.get(parts[2])
        if ' ' in parts[3]:
            result['street_ddt'] = '+'.join(parts[3].split(' '))
        else:
            result['street_ddt'] = parts[3]
        if parts[2] in ['пер', 'тракт']:
            result['address_ddt'] = result['address_ddt'] + '%s+%s,+' % (result['street_ddt'], parts[2])
        else:
            result['address_ddt'] = result['address_ddt'] + '%s+%s,+' % (parts[2], result['street_ddt'])

        k = [i for i, part in enumerate(parts) if re.search(r'\d+/\w+', part)]
        if len(k) != 0:
            addr_values = parts[k[0]].split('/')
            result['address_ddt'] = result['address_ddt'] + '%s+%s+%s+%s' % ('д', addr_values[0], 'к', addr_values[1])
            result['block_type_full_ddt'] = 'корпус'
            result['block_ddt'] = addr_values[1]
            result['house_ddt'] = addr_values[0]
        else:
            result['address_ddt'] = result['address_ddt'] + '%s+%s' % (parts[4], parts[5])
            result['house_ddt'] = parts[5]

    elif parts[0] in street_type:

        result['street_type_full_ddt'] = street_type.get(parts[0])
        if ' ' in parts[1]:
            result['street_ddt'] = '+'.join(parts[1].split(' '))
        else:
            result['street_ddt'] = parts[1]
        if parts[0] in ['пер', 'тракт']:
            result['address_ddt'] = result['address_ddt'] + '%s+%s,+' % (result['street_ddt'], parts[0])
        else:
            result['address_ddt'] = result['address_ddt'] + '%s+%s,+' % (parts[0], result['street_ddt'])

        k = [i for i, part in enumerate(parts) if re.search(r'\d+/\w+', part)]
        if len(k) != 0:
            addr_values = parts[k[0]].split('/')
            result['address_ddt'] = result['address_ddt'] + '%s+%s+%s+%s' % ('д', addr_values[0], 'к', addr_values[1])
            result['block_type_full_ddt'] = 'корпус'
            result['block_ddt'] = addr_values[1]
            result['house_ddt'] = addr_values[0]
        else:
            result['address_ddt'] = result['address_ddt'] + '%s+%s' % (parts[2], parts[3])
            result['house_ddt'] = parts[3]

    try:
        k = list.index(parts, 'к')
        if parts[k + 1].isdigit():
            result['block_type_full_ddt'] = 'корпус'
            result['block_ddt'] = parts[k + 1]
            result['address_ddt'] = result['address_ddt'] + '+%s+%s' % (parts[k], parts[k + 1])
        else:
            result['house_ddt'] = result['house_ddt'] + parts[k + 1]
            result['address_ddt'] = result['address_ddt'] + '%s' % parts[k + 1]
    except ValueError as e:
        pass

    try:
        k = list.index(parts, 'стр')
        if parts[k + 1].isdigit():
            result['block_type_full_ddt'] = 'строение'
            result['block_ddt'] = parts[k + 1]
            result['address_ddt'] = result['address_ddt'] + '+%s+%s' % (parts[k], parts[k + 1])
        else:
            result['house_ddt'] = result['house_ddt'] + parts[k + 1]
            result['address_ddt'] = result['address_ddt'] + '%s' % parts[k + 1]
    except ValueError as e:
        pass

    return result


def grab_cadastres(cities):
    # grab_addresses(cities)
    for city in cities:
        addresses = get_addresses(city)
        cadastres = []
        try:
            for address in addresses:
                print('считываю кадастровые номера адреса: ' + address)
                data = address_parse(address)
                params = {}
                for key in data.keys():
                    if data.get(key):
                        params[key] = data.get(key)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0'
                }
                r = requests.get(url=url, params=params)
                html = r.text
                unique = set(re.findall(r'\d{2}:\d{2}:\d{6,7}:\d+', html))
                cadastres.extend(list(unique))
        except requests.exceptions or Exception as e:
            print(e)
            pass
        finally:
            fill_files(city, cadastres)
    return None


def get_cadastres(city):
    filename = os.getcwd() + '/out/cadastres/' + city + '.txt'
    with open(filename, mode='r', encoding='UTF-8') as input_file:
        print('oop')
