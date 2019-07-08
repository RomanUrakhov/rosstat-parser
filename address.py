import os
import requests


def fill_files(city, houses):
    addresses = []
    for house in houses:
        addresses.append(house['address'])

    with open(os.getcwd() + '/out/addresses/' + city + '.txt', mode='w', encoding='UTF-8') as output_file:
        output_file.writelines("%s\n" % address for address in addresses)


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
            fill_files(city, houses)
        else:
            continue
    response.close()


def get_addresses(city):
    filename = os.getcwd() + '/out/addresses/' + city + '.txt'
    with open(filename, mode='r', encoding='UTF-8') as input_file:
        addresses = [address.rstrip() for address in input_file.readlines()]
    return addresses
