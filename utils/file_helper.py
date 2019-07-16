import os
import csv


def write_apartments(dirname, city, data):
    try:
        os.makedirs(dirname)
    except OSError as e:
        pass
    filename = f"{dirname}/{city}.tsv"
    try:
        with open(filename, mode='a', encoding='UTF-8', newline='') as output_file:
            writer = csv.DictWriter(output_file, delimiter='\t', fieldnames=data[0].keys())
            if os.stat(filename).st_size == 0:
                writer.writeheader()
            for item in data:
                writer.writerow(item)
    except IOError:
        print('I/O Error')


def write_cadastres(dirname, city, data):
    try:
        os.makedirs(dirname)
    except OSError as e:
        pass
    filename = f"{dirname}/{city}.csv"
    try:
        with open(filename, mode='a', encoding='UTF-8', newline='') as output_file:
            writer = csv.writer(output_file, lineterminator='\n')
            for item in data:
                writer.writerow([item, ])
    except IOError:
        print("I/O Error")


def write_addresses(dirname, city, data):
    try:
        os.makedirs(dirname)
    except OSError as e:
        pass
    filename = f"{dirname}/{city}.txt"
    try:
        with open(filename, mode='w', encoding='UTF-8') as output_file:
            output_file.writelines("%s\n" % item for item in data)
    except IOError as e:
        print(e)


def get_cadastres(dirname, city):
    filename = f"{dirname}/{city}.csv"
    data = []
    try:
        with open(filename, mode='r', encoding='UTF-8', newline='') as input_file:
            reader = csv.reader(input_file, lineterminator='\n')
            for cadastre in reader:
                data.append(cadastre[0])
    except IOError:
        print("I/O Error")
    return data


def get_addresses(dirname, city):
    filename = f"{dirname}/{city}.txt"
    data = []
    try:
        with open(filename, mode='r', encoding='UTF-8') as input_file:
            data = [item.rstrip() for item in input_file.readlines()]
    except IOError:
        print("I/O Error")
    return data
