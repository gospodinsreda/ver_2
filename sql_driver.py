import sqlite3
import config


with sqlite3.connect(config.DB_NAME) as connection:
	cursor = connection.cursor()
	sql = '''
	CREATE TABLE IF NOT EXISTS avito (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		product_link INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	sql = '''
	CREATE TABLE IF NOT EXISTS yola (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		product_link INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	sql = '''
	CREATE TABLE IF NOT EXISTS avito_links (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		search_link INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	sql = '''
	CREATE TABLE IF NOT EXISTS yola_links (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		search_link INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	sql = '''
	CREATE TABLE IF NOT EXISTS keywords (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		keyword INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	sql = '''
	CREATE TABLE IF NOT EXISTS notkeywords (
		id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
		notkeyword INTEGER NOT NULL
	)'''
	cursor.execute(sql)
	connection.commit()


class DataBase:
	"""
	Класс Базы Данных
	"""

	@staticmethod
	def add_keyword(text):
		"""
		Добавить ключевое слово
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'INSERT INTO keywords (keyword) VALUES (?)'
			cursor.execute(sql, (text,))
		connection.commit()

	@staticmethod
	def get_keywords():
		"""
		Получить ключевые слова
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'SELECT * FROM keywords'
			return cursor.execute(sql).fetchall()

	@staticmethod
	def delete_keyword(id):
		"""
		Удалить ключевое слово
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'DELETE FROM keywords WHERE id=?'
			cursor.execute(sql, (id,))
		connection.commit()

	@staticmethod
	def add_notkeyword(text):
		"""
		Добавить исключающее слово
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'INSERT INTO notkeywords (notkeyword) VALUES (?)'
			cursor.execute(sql, (text,))
		connection.commit()

	@staticmethod
	def get_notkeywords():
		"""
		Получить исключающие слова
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'SELECT * FROM notkeywords'
			return cursor.execute(sql).fetchall()

	@staticmethod
	def delete_notkeyword(id):
		"""
		Удалить исключающее слово
		"""
		with sqlite3.connect(config.DB_NAME) as connection:
			cursor = connection.cursor()
			sql = 'DELETE FROM notkeywords WHERE id=?'
			cursor.execute(sql, (id,))
		connection.commit()

if __name__ == "__main__":
	DataBase.delete_notkeyword(input("Введите id: "))
