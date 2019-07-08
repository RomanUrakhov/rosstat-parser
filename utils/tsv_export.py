import csv
import os


def is_file_empty(filename):
    return os.path.isfile(filename) and os.path.getsize(filename) == 0


def write_file(filename, data):
    with open(filename, mode='a', encoding='UTF-8') as out_file:
        tsw_writer = csv.writer(out_file, delimiter='\t')
        if is_file_empty(filename):
            tsw_writer.writerow(
                ['Тип', 'Кадастровый номер', 'Регион', 'Кадастровый район', 'Почтовый индекс',
                 'Адрес полный', 'Адрес по документам', 'Площадь', 'Кадастровая стоимость']
            )
        tsw_writer.writerow(data.values())
