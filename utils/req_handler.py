import requests


def get_execute(url, headers=None):
    response = None
    try:
        response = requests.get(url, headers)
    except requests.exceptions.ConnectionError:
        print('dns lookup failed')
    if response:
        return response.json()
    return None


def post_execute(url, data=None):
    response = None
    try:
        response = requests.post(url,data)
    except requests.exceptions:
        return 'Oops'
    if response:
        return response.json()
    return None
