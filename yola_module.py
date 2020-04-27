from bs4 import BeautifulSoup
import sqlite3
import requests
import config
import pytesseract
from sql_driver import DataBase
import telebot
from telebot import types, apihelper

bot = telebot.TeleBot(config.BOT_TOKEN)
if config.DEBUG:
	apihelper.proxy = config.proxy



class Yola:
	"""
	Класс Yola
	"""

	@staticmethod
	def in_database(product_link):
		"""
		Проверить, что данная ссылка уже есть в базе данных
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'SELECT * FROM yola WHERE product_link=?'
			res = cursor.execute(sql, (product_link,)).fetchone()
		return bool(res)

	@staticmethod
	def add_database(product_link):
		"""
		Добавить ссылку в базу данных
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'INSERT INTO yola (product_link) VALUES (?)'
			cursor.execute(sql, (product_link,))
			connection.commit()

	@staticmethod
	def get_search_links():
		"""
		Получить ссылки для поиска
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'SELECT * FROM yola_links'
			return cursor.execute(sql).fetchall()

	@staticmethod
	def add_search_link(link):
		"""
		Добавить ссылку для поиска
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'INSERT INTO yola_links (search_link) VALUES (?)'
			cursor.execute(sql, (link,))
		connection.commit()

	@staticmethod
	def delete_search_link(id):
		"""
		Удалить ссылку для поиска
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'DELETE FROM yola_links WHERE id=?'
			cursor.execute(sql, (id,))
		connection.commit()


def monitor_yola():
	"""
	Мониторинг Юлы по ссылкам
	"""
	search_links = Yola.get_search_links()
	for lnk in search_links:
		url = lnk[1]
		location = lnk[1].replace('https://youla.ru/', '').split('/')
		location = location[0]
		session = requests.Session()
		session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4086.0 Safari/537.36'})
		session.proxies = {
            'http': 'http://r5rpwY:cd999t@45.10.82.26:8000',
        }
		html_doc = session.get(url).text
		soup = BeautifulSoup(html_doc, 'lxml')
		collect = soup.find('section', 'product_section')
		links = collect.findAll('a')
		links_array = []
		for link in links:
			if location in link.get('href'):
				for x in links_array:
					if x == 'https://youla.ru{!s}'.format(link.get('href')):
						continue
				if (('https://youla.ru{!s}'.format(link.get('href')))
						not in links_array) & (link.get('href').find('favorites') == -1):
					try:
						link_ = 'https://youla.ru{!s}'.format(link.get('href'))
						price = link.parent.find(
							'div', 'product_item__description').text.strip()
						title = link.parent.find(
							'div', 'product_item__title').text.strip()
						if len(price.split('\n')) > 1:
							price = price.split('\n')[0]
					except Exception as e:
						print(e)
						continue

					# Проверка по ключевым и исключающим словам
					keywords_arr = [str(x[1]).lower() for x in DataBase.get_keywords()]
					notkeywords_arr = [str(x[1]).lower() for x in DataBase.get_notkeywords()]
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
							'title': title,
						})

			print(links_array)
			print(len(links_array))
			for x in links_array:
				print(x)
				if not Yola.in_database(x['link']):
					for adm_id in config.ADMINS:
						text = 'Найдено новое объявление\n\n<b>{!s}</b>\n\n{!s}\n\nЦена: <b>{!s}</b>\n'.format(
							x['title'], x['link'], x['price'])
						try:
							bot.send_message(adm_id, text, parse_mode='HTML')
						except Exception as e:
							print(e)
					Yola.add_database(x['link'])

