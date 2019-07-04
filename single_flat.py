from bs4 import BeautifulSoup, Tag
import requests
import re
from TimeCheck import Profiler


def load_page_content():
    url = 'https://rosreestr.net/kadastr/24-47-0000000-1488'
    response = requests.get(url)
    return response.text


def get_container(text):
    soup = BeautifulSoup(text, 'html.parser')
    # контейнер с информацией о квартире
    flat_container = soup.find('div', {'class': 'test__data'})
    return flat_container


def get_flat_info(items):
    keys = []
    values = []
    for item in items:
        title_and_data = item.text.split(':', 1)
        if len(title_and_data) != 1:
            keys.append(title_and_data[0])
            values.append(title_and_data[1].strip())

    # d = dict(zip(keys, values))
    # d = {k: v for k, v in zip(keys, values)}
    d = get_main_info(keys, values)
    print(d)

    return d


def get_main_info(keys, values):
    need = ['Тип', 'Кадастровый номер', 'Регион', 'Кадастровый район', 'Почтовый индекс',
            'Адрес полный', 'Адрес по документам', 'Площадь', 'Кадастровая стоимость']
    result = {k: v for k, v in zip(keys, values) if k in need}
    # result = list(filter(lambda x: x in need, values))
    return result


# def get_main_info(data):
#     result = {}
#     need = ['Тип', 'Кадастровый номер', 'Регион', 'Кадастровый район', 'Почтовый индекс',
#             'Адрес полный', 'Адрес по документам', 'Площадь', 'Кадастровая стоимость']
#     for key in data.keys():
#         if key in need:
#             result[key] = data.get(key)
#
#     return result


def beautify(data):
    cost = data['Кадастровая стоимость']
    offset = len(cost) - cost.find('.') - 1
    data['Кадастровая стоимость'] = cost[:-offset]

    area = data['Площадь']
    offset = len(area) - area.find('(') + 1
    data['Площадь'] = area[:-offset]


def main():
    page_text = load_page_content()
    flat_container = get_container(page_text)
    items = flat_container.find_all('div', recursive=False)
    data = get_flat_info(items)
    # data = get_main_info(data)
    # beautify(data)
    # print(data)


if __name__ == '__main__':
    with Profiler() as p:
        main()
