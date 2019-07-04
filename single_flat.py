from bs4 import BeautifulSoup, Tag
import requests
import re
from TimeCheck import Profiler


def load_page_content():
    url = 'https://rosreestr.net/kadastr/24-47-0000000-1488'
    response = None
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        print('dns lookup failed')

    if response:
        return response.text
    return None


def get_container(text):
    soup = BeautifulSoup(text, 'html.parser')
    # контейнер с информацией о квартире
    apt_container = soup.find('div', {'class': 'test__data'})
    return apt_container


def get_main_info(keys, values):
    need = ['Тип', 'Кадастровый номер', 'Регион', 'Кадастровый район', 'Почтовый индекс',
            'Адрес полный', 'Адрес по документам', 'Площадь', 'Кадастровая стоимость']
    result = {k: v for k, v in zip(keys, values) if k in need}
    return result


def get_apt_info(page_content):
    apt_container = get_container(page_content)
    items = apt_container.find_all('div', recursive=False)

    keys = []
    values = []
    for item in items:
        title_and_data = item.text.split(': ', 1)
        if len(title_and_data) != 1:
            keys.append(title_and_data[0])
            values.append(title_and_data[1])

    d = get_main_info(keys, values)
    beautify(d)
    return d


def beautify(data):
    cost = data['Кадастровая стоимость']
    offset = len(cost) - cost.find('.') - 1
    data['Кадастровая стоимость'] = cost[:-offset]

    area = data['Площадь']
    offset = len(area) - area.find('(') + 1
    data['Площадь'] = area[:-offset]


def main():
    page_text = load_page_content()
    if not page_text:
        return
    data = get_apt_info(page_text)
    print(data)


if __name__ == '__main__':
    with Profiler() as p:
        main()
