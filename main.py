import os
from time import sleep
from datetime import datetime
from threading import Thread

import httplib2
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials
import requests
from lxml import etree
from sqlalchemy.orm import Session

from model import GoogleSheetsData, engine
from bot_telegram import bot_send_to_chat
from logger import logger
import creds


def get_service_sacc():
    """ Ф-я получает доступ к рессурсу и возвращает объект GooglSheet (тип dict)
    """
    creds_json = os.path.dirname(__file__) + "/creds/testapi-354111-fad13f664c79.json"
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())

    return build('sheets', 'v4', http=creds_service)


def get_data_from_googlesheet():
    """ Ф-я получает данные из таблицы
        Возвращает данные в виде списка списков:
            ([[запись из табл.], [запись из табл.], [запись из табл.], ...])
    """
    try:
        service = get_service_sacc()
        sheet = service.spreadsheets()
        resp_xml = sheet.values().batchGet(spreadsheetId=creds.SHEET_ID, ranges=["Лист1"]).execute()
        response = resp_xml['valueRanges'][0]['values'][1:]
        parsed_data = add_column_rub_valute(response)
        return parsed_data
    except Exception as err:
        logger.error(f"{err}")

    return False


def get_curent_date():
    """ ф-я конвертирует текущую дату в нужный формат для ф-и get_cbr_valute
        пример: 2022-06-23 -> 23/06/2022
    """
    date = str(datetime.now().date()).split('-')[::-1]
    date = "/".join(date)

    return date


def get_cbr_valute(date=None, country=None):
    """ Ф-я принимает два аргумента и возвращает курс валюты по заданным параметрам.
        date: формат должен быть 01/11/2000, если аргумент не задан, то по умолчанию берется текущее время
        country: абривиатура страны, если не задан, то по умолчанию 'USD'
        :return: valute_ (тип float)
    """
    if date is None:
        date = get_curent_date()

    if country is None:
        country = 'USD'

    URL = f'https://www.cbr.ru/scripts/XML_daily.asp?date_req={date}'

    countries = {
        'AUD': 'R01010', 'AZN': 'R01020A', 'GBP': 'R01035',
        'AMD': 'R01060', 'JPY': 'R01820', 'USD': 'R01235'
    }

    xml_data = requests.get(URL)
    xml = xml_data.content
    tree = etree.XML(xml)
    country_name = str(tree.xpath(f'//ValCurs/Valute[@ID="{countries.get(country)}"]/Name/text()')[0])
    valute_ = float(tree.xpath(f'//ValCurs/Valute[@ID="{countries.get(country)}"]/Value')[0].text.replace(',', '.'))

    return country_name, valute_


def add_column_rub_valute(data):
    """ Ф-я производит перерасчет данных из 'price_dollar' по курсу ЦБРФ в рубли и добавлят к полученным
        данным новую колонку 'price_rub'
    """
    name_, current_exchange_rate = get_cbr_valute()
    parsed_data = []

    for row in data:
        row[0] = int(row[0])
        row[1] = int(row[1])
        row[2] = int(row[2])
        row.insert(3, round((lambda x: x * current_exchange_rate)(int(row[2])), 2))
        parsed_data.append(row)

    return parsed_data


def save_data_to_database(data_list):
    """ Ф-я сохраняет данные в БД посредством SQLAlchemy
        data_list: список данных в формате list()
    """
    session = Session(engine)
    list_obj = []

    for row in data_list:

        obj = GoogleSheetsData(
            no=row[0],
            order_no=row[1],
            price_dollar=row[2],
            price_rub=row[3],
            delivery_time=row[4]
        )

        list_obj.append(obj)

    session.add_all(list_obj)
    session.commit()
    logger.info('Сохранение в БД прошло успешно.')

    return True


def check_cell_to_update(query, cell, row):
    """ Ф-я сравнивает ячейки данных лок. БД и новыми данными, если есть различие, то возвращает соотв. объект для
        обновления, если различий нет, то возвращает старый объект.
    """
    if cell != row:
        logger.info(f'Ячейка {cell} в строке с ID {query.no} будет обновлена.')
        return row
    return cell


def check_delivery_time(data):
    """ Ф-я проверяет поле delivery_time (срок поставки) в локальной БД, если срок истёк -
        отрпавляет сообщение в чат-телеграмм
    """
    for row in data_sheet:
        delivery_time = session.query(GoogleSheetsData).get(row[0]).delivery_time
        if datetime.strptime(delivery_time, '%d.%m.%Y').date() < datetime.now().date():
            sleep(5)
            th_ = Thread(target=bot_send_to_chat, args=(f"Срок заказа {row[1]} истёк - {row[4]}",))
            th_.start()


def update_db(data):
    """ Ф-я обновляет записи в БД, зависит от ф-и check_cell_to_update.
        data: данные полученые из таблицы. формат list()
    """
    list_obj_for_update = []
    session = Session(engine)

    for row in data:
        q = session.query(GoogleSheetsData).get(row[0])
        try:
            q.no = check_cell_to_update(query=q, cell=q.no, row=row[0])
            q.order_no = check_cell_to_update(query=q, cell=q.order_no, row=row[1])
            q.price_dollar = check_cell_to_update(query=q, cell=q.price_dollar, row=row[2])
            q.price_rub = check_cell_to_update(query=q, cell=q.price_rub, row=row[3])
            q.delivery_time = check_cell_to_update(query=q, cell=q.delivery_time, row=row[4])

            if any([q.no, q.order_no, q.price_dollar, q.price_rub, q.delivery_time]):
                list_obj_for_update.append(q)

        except Exception as e:
            logger.error(f'Ошибка обновления {e}')

    session.add_all(list_obj_for_update)
    session.commit()
    logger.info('Обновление БД завершено')

    return True


def main_loop(ref_string=None, time_delay=5):
    """ Главный цикл приложения. Ф-я работает в цикле. В режиме онлайн делает запрос к API таблицы и если
        есть изменения, запускает функционал обновления.
        ref_strinf: вх. аргумент в формате str() для стравнения с БД.
        time_delay: определяет в секундах период запросов к API таблицы.
    """

    while True:
        try:
            response = get_data_from_googlesheet()
            logger.debug(f"Ответ получен {response}")

            if not response:
                logger.error("Данные на получены")
                return

            response_string = str(response)

            if ref_string != response_string and ref_string is not None:
                logger.info('В таблице есть изменения. Требуется обновить БД.')
                thread = Thread(target=update_db, args=(response,))
                thread.start()
                thread.join()

            ref_string = response_string
            sleep(time_delay)
            logger.info('Выполняется запрос к таблице...')

        except HttpError as err:
            logger.critical(f"Соединения разорвано. {err}")


if __name__ == '__main__':
    """ Запускает приложение. Проверяет наличие БД. Если БД нет, то делает запрс к API таблицы и сохраняет ее 
        в БД локально. Если БЛ существует, то запускает главный цикл приложения, где в режиме онлайн идет запром к API
    """
    logger.info("Старт приложения")

    session = Session(engine)

    if len(session.query(GoogleSheetsData).all()) == 0:
        data_sheet = get_data_from_googlesheet()
        save_data_to_database(data_sheet)
        th = Thread(target=check_delivery_time, args=(data_sheet,))
        th.start()
        main_loop(ref_string=str(data_sheet))
    else:
        data_sheet = get_data_from_googlesheet()
        th = Thread(target=check_delivery_time, args=(data_sheet,))
        th.start()
        main_loop(ref_string=str(data_sheet))
