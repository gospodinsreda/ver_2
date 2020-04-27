import requests
import config
import sqlite3
from sql_driver import *
from selenium import webdriver
from bs4 import BeautifulSoup
import pytesseract
import base64
try:
    from PIL import Image
except ImportError:
    import Image
import os
from telebot import types, apihelper
import time
import telebot
from telebot import types, apihelper

bot = telebot.TeleBot(config.BOT_TOKEN)
if config.DEBUG:
	apihelper.proxy = config.proxy


class Avito:
    """
    Класс Avito
    """

    @staticmethod
    def in_database(product_link):
        """
        Проверить, что данная ссылка уже есть в базе данных
        """
        with sqlite3.connect(config.DB_NAME) as connection:
            cursor = connection.cursor()
            sql = 'SELECT * FROM avito WHERE product_link=?'
            res = cursor.execute(sql, (product_link,)).fetchone()
        return bool(res)

    @staticmethod
    def add_database(product_link):
        """
        Добавить ссылку в базу данных
        """
        with sqlite3.connect(config.DB_NAME) as connection:
            cursor = connection.cursor()
            sql = 'INSERT INTO avito (product_link) VALUES (?)'
            cursor.execute(sql, (product_link,))
            connection.commit()

    @staticmethod
    def get_search_links():
        """
        Получить ссылки для поиска
        """
        with sqlite3.connect(config.DB_NAME) as connection:
            cursor = connection.cursor()
            sql = 'SELECT * FROM avito_links'
            return cursor.execute(sql).fetchall()

    @staticmethod
    def add_search_link(link):
        """
        Добавить ссылку для поиска
        """
        with sqlite3.connect(config.DB_NAME) as connection:
            cursor = connection.cursor()
            sql = 'INSERT INTO avito_links (search_link) VALUES (?)'
            cursor.execute(sql, (link,))
        connection.commit()

    @staticmethod
    def delete_search_link(id):
        """
        Удалить ссылку для поиска
        """
        with sqlite3.connect(config.DB_NAME) as connection:
            cursor = connection.cursor()
            sql = 'DELETE FROM avito_links WHERE id=?'
            cursor.execute(sql, (id,))
        connection.commit()

    @staticmethod
    def get_advertisement_phone(url):
        """
        Получить телефон объявления на Авито
        """
        try:
                if config.WINDOWS == True:
                    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                else:
                    from pyvirtualdisplay import Display
                    display = Display(visible=0, size=(800, 600))
                    display.start()
                driver = webdriver.Firefox()
                driver.get(url)
                driver.find_element_by_xpath("/html/body/div[3]/div[1]/div[3]/div[3]/div[2]/div[1]/div/div[2]/div/div[2]/div/div/span/span/button").click()
                time.sleep(2)
                phone_img = driver.find_element_by_xpath(
                    "/html/body/div[3]/div[1]/div[3]/div[3]/div[2]/div[1]/div/div[2]/div/div[2]/div/div/span/span/button/span/img").get_attribute('src')
                driver.close()
                print(phone_img)
                base64photo = phone_img.split(',')[1]
                fname = 'foo.png'
                print("Создали файл foo")
                with open(fname, 'wb') as f:
                    f.write(base64.decodestring(bytes(base64photo, 'utf8')))
                phone = pytesseract.image_to_string(Image.open(fname))
                # print(len(phone))
                # time.sleep(10)
                #while len(phone) != 15:
                #    phone = pytesseract.image_to_string(Image.open(fname))
                os.remove(fname)
                return '+' + phone.replace('-', '').replace(' ', '')

        except Exception as e:
                print(e)
                driver.close()
                return None


def monitor_avito():
    """
    Мониторинг Авито по ссылкам
    """
    search_links = Avito.get_search_links()
    for lnk in search_links:
        url = lnk[1]
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        session.proxies = {
            'http': 'http://r5rpwY:cd999t@45.10.82.26:8000',
        }
        res = session.get(url)
        print(res.text)
        html_doc = res.text
        soup = BeautifulSoup(html_doc, 'lxml')
        collect = soup.find('div', {'data-marker': 'items/list'})
        links = collect.findAll('a')
        links_array = []
        for i, link in enumerate(links):
            for x in links_array:
                if x == 'https://avito.ru{!s}'.format(link.get('href')):
                    continue
            if (('https://avito.ru{!s}'.format(link.get('href')))
                    not in links_array) & (link.get('href').find('favorites') == -1):
                link_ = 'https://avito.ru{!s}'.format(link.get('href'))
                price = soup.findAll(
                    'div', {'data-marker': 'item/price'})[i].text
                title = link.text
                # Проверка по ключевым и исключающим словам
                keywords_arr = [str(x[1]).lower()
                                for x in DataBase.get_keywords()]
                notkeywords_arr = [str(x[1]).lower()
                                   for x in DataBase.get_notkeywords()]
                print(keywords_arr)
                confirm = False
                if len(keywords_arr) == 0:
                    confirm = True
                for kw in keywords_arr:
                    if kw in title.lower() or kw in link_.lower():
                        confirm = True
                for kw in notkeywords_arr:
                    if kw in title.lower() or kw in link_.lower():
                        confirm = False
                if confirm:
                    links_array.append({
                        'link': link_,
                        'price': price,
                        'title': title
                    })

        print(links_array)
        print(len(links_array))
        for x in links_array:
            print(x)
            if not Avito.in_database(x['link']):
                sended_msg_ids = []
                text = 'Найдено новое объявление\n\n<b>{!s}</b>\n\n{!s}\n\nЦена: <b>{!s}</b>'.format(
                    x['title'], x['link'], x['price'])
                # Отправка объявления всем админам бота
                for adm_id in config.ADMINS:
                    try:
                        res = bot.send_message(adm_id, text, parse_mode='HTML')
                        sended_msg_ids.append(
                            {'chat_id': adm_id, 'message_id': res.message_id})
                    except Exception as e:
                        print(e)
                # Попытка получения номера объявления и обновления сообщения у админов
                print('Starting find phone...')
                # TODO
                phone = None
                phone = Avito.get_advertisement_phone(x['link'])
                print(phone)
                if phone:
                    for msg in sended_msg_ids:
                        phone = phone.replace('+8', '+7')
                        new_text = '{!s}\n\nТелефон: {!s}'.format(text, phone)
                        keyboard = types.InlineKeyboardMarkup()
                        keyboard.add(types.InlineKeyboardButton(
                            text='Отправить СМС', callback_data='sendsms_{!s}'.format(phone)))
                        bot.edit_message_text(
                            new_text, chat_id=msg['chat_id'], message_id=msg['message_id'], reply_markup=keyboard, parse_mode='HTML')
                Avito.add_database(x['link'])
