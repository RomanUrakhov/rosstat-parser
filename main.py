import address
import cadastr
import apartment
from utils import time_check

# cities = {
#     'perm': 'permskiy-kray',
#     'ekaterinburg': 'sverdlovskaya-oblast',
#     'penza': 'penzenskaya-oblast',
#     'tver': 'tverskaya-oblast',
#     'tomsk': 'tomskaya-oblast',
#     'izhevsk': 'udmurtskaya-respublika',
#     'irkutsk': 'irkutskaya-oblast'
# }

cities = {
    'ekaterinburg': 'sverdlovskaya-oblast'
}


def main():
    # address.grab_addresses(cities)
    # cadastr.grab_cadastres(cities)
    apartment.grab_apartments(cities)


if __name__ == '__main__':
    with time_check.Profiler() as p:
        main()
