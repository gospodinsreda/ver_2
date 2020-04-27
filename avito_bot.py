#!/usr/bin/env python3

import os
import sys
import time
import base64
import sqlite3
import datetime
import threading
import subprocess
from sql_driver import *
from yola_module import Yola, monitor_yola
from avito_module import Avito, monitor_avito
from addons import *
import requests
import pytesseract
import telebot
from telebot import types, apihelper
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
import config
try:
	from PIL import Image
except ImportError:
	import Image
import socket


bot = telebot.TeleBot(config.BOT_TOKEN)
if config.DEBUG:
	apihelper.proxy = config.proxy


READY_TO_ADD_LINK = {}
READY_TO_ADD_KEYWORD = {}
READY_TO_ADD_NOTKEYWORD = {}


def restart_func():
	if config.WINDOWS == True:
		os.system('script.bat')
		print('Перезапускаюсь, ёб вашу мать!!!!')
		quit()
	else:
		os.system('bash script.sh')
		print('Перезапускаюсь, ёб вашу мать!!!!')
		quit()


@bot.message_handler(commands=['start'])
def start_message_handler(message):
	cid = message.chat.id
	uid = message.from_user.id
	return bot.send_message(cid, 'В процессе...')


@bot.message_handler(commands=['admin'])
def admin_message_handler(message):
	cid = message.chat.id
	uid = message.from_user.id
	if uid not in config.ADMINS:
		text = 'Доступ запрещен'
		return bot.send_message(cid, text)
	markup = types.ReplyKeyboardMarkup(
		resize_keyboard=True,
		one_time_keyboard=False,
		row_width=1)
	for x in config.admin_markup:
		markup.row(*x)
	text = 'Админ-панель'
	return bot.send_message(cid, text, reply_markup=markup)


@bot.message_handler(commands=['restart'])
def restart_message_handler(message):
	cid = message.chat.id
	uid = message.from_user.id
	if uid not in config.ADMINS:
		text = 'Доступ запрещен'
		return bot.send_message(cid, text)
	text = 'Бот перезапустится в течение нескольких секунд'
	bot.send_message(cid, text)
	restart_func()
	return


@bot.message_handler(content_types=['text'])
def text_handler(message):
	cid = message.chat.id
	uid = message.from_user.id

	# Обработать отмену операции
	if message.text == '❌ Отмена':
		if uid in READY_TO_ADD_LINK:
			del READY_TO_ADD_LINK[uid]
		if uid in READY_TO_ADD_KEYWORD:
			del READY_TO_ADD_KEYWORD[uid]
		if uid in READY_TO_ADD_NOTKEYWORD:
			del READY_TO_ADD_NOTKEYWORD[uid]
		text = 'Действие отменено'
		bot.send_message(cid, text)
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, one_time_keyboard=False, row_width=1)
		for x in config.admin_markup:
			markup.row(*x)
		text = 'Админ-панель'
		return bot.send_message(cid, text, reply_markup=markup)

	# Обработать добавление новой ссылки
	if uid in READY_TO_ADD_LINK:
		if 'place' not in READY_TO_ADD_LINK[uid]:
			if message.text not in ['Авито', 'Юла']:
				text = 'Выберите одну из площадок на клавиатуре'
				return bot.send_message(cid, text)
			READY_TO_ADD_LINK[uid]['place'] = message.text
			text = 'Вставьте ссылку на мобильную версию приложения для Авито'
			text += ' (https://m.avito.ru) и на версия для ПК для Юлы (https://yola.ru)'
			text += '\n\nПример ссылка для Авито: {!s}'.format(
				config.AVITO_EXAMPLE_LINK)
			text += '\n\nПример ссылка для Юлы: {!s}'.format(
				config.YOLA_EXAMPLE_LINK)
			markup = types.ReplyKeyboardMarkup(
				resize_keyboard=True, one_time_keyboard=False, row_width=1)
			markup.row('❌ Отмена')
			return bot.send_message(cid, text, reply_markup=markup)
		if 'link' not in READY_TO_ADD_LINK[uid]:
			# Проверить ссылку на валидость
			if READY_TO_ADD_LINK[uid]['place'] == 'Авито':
				try:
					html_doc = requests.get(message.text).text
					soup = BeautifulSoup(html_doc, 'lxml')
					collect = soup.find('div', {'data-marker': 'items/list'})
					links = collect.findAll('a')
					links[0]
				except Exception as e:
					print(e)
					text = 'Неверная ссылка. Попробуйте ещё раз'
					return bot.send_message(cid, text)
			elif READY_TO_ADD_LINK[uid]['place'] == 'Юла':
				try:
					html_doc = requests.get(message.text).text
					soup = BeautifulSoup(html_doc, 'lxml')
					collect = soup.find('section', 'product_section')
					links = collect.findAll('a')
					links[0]
				except Exception as e:
					print(e)
					text = 'Неверная ссылка. Попробуйте ещё раз'
					return bot.send_message(cid, text)
			READY_TO_ADD_LINK[uid]['link'] = message.text
			if READY_TO_ADD_LINK[uid]['place'] == 'Авито':
				Avito.add_search_link(READY_TO_ADD_LINK[uid]['link'])
			elif READY_TO_ADD_LINK[uid]['place'] == 'Юла':
				Yola.add_search_link(READY_TO_ADD_LINK[uid]['link'])
			del READY_TO_ADD_LINK[uid]
			text = 'Ссылка успешно добавлена!'
			bot.send_message(cid, text)
			markup = types.ReplyKeyboardMarkup(
				resize_keyboard=True, one_time_keyboard=False, row_width=1)
			for x in config.admin_markup:
				markup.row(*x)
			text = 'Админ-панель'
			return bot.send_message(cid, text, reply_markup=markup)

	# Обработать добавление ключевого слова
	if uid in READY_TO_ADD_KEYWORD:
		if 'keyword' not in READY_TO_ADD_KEYWORD[uid]:
			words = message.text.split('\n')
			words_normal = []
			for x in words:
				if len(x) > 0: words_normal.append(x)
			READY_TO_ADD_KEYWORD[uid]['keyword'] = message.text
			for x in words_normal:
				DataBase.add_keyword(x)
			del READY_TO_ADD_KEYWORD[uid]
			text = 'Ключевое слово успешно добавлено'
			bot.send_message(cid, text)
			markup = types.ReplyKeyboardMarkup(
				resize_keyboard=True, one_time_keyboard=False, row_width=1)
			for x in config.admin_markup:
				markup.row(*x)
			text = 'Админ-панель'
			return bot.send_message(cid, text, reply_markup=markup)

	# Обработать добавление исключающего слова
	if uid in READY_TO_ADD_NOTKEYWORD:
		if 'keyword' not in READY_TO_ADD_NOTKEYWORD[uid]:
			words = message.text.split('\n')
			words_normal = []
			for x in words:
				if len(x) > 0: words_normal.append(x)
			READY_TO_ADD_NOTKEYWORD[uid]['keyword'] = message.text
			for x in words_normal:
				DataBase.add_notkeyword(x)
			del READY_TO_ADD_NOTKEYWORD[uid]
			text = 'Исключающее слово успешно добавлено'
			bot.send_message(cid, text)
			markup = types.ReplyKeyboardMarkup(
				resize_keyboard=True, one_time_keyboard=False, row_width=1)
			for x in config.admin_markup:
				markup.row(*x)
			text = 'Админ-панель'
			return bot.send_message(cid, text, reply_markup=markup)

	# Обработать кнопки главного меню
	if message.text == '➕ Добавить ссылку':
		READY_TO_ADD_LINK[uid] = {}
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, one_time_keyboard=False, row_width=1)
		markup.row('Авито', 'Юла')
		markup.row('❌ Отмена')
		text = 'Выберите площадку на клавиатуре'
		return bot.send_message(cid, text, reply_markup=markup)
	elif message.text == '👀 Посмотреть ссылки':
		a_links = Avito.get_search_links()
		y_links = Yola.get_search_links()
		links = a_links + y_links
		if len(links) == 0:
			text = 'Пока нет ни одной активной ссылки для поиска объявлений'
			return bot.send_message(cid, text)
		for x in a_links:
			print(x)
			text = 'Авито\n\n{!s}'.format(x[1])
			markup = types.InlineKeyboardMarkup()
			markup.add(
				types.InlineKeyboardButton(
					callback_data='delavito_{!s}'.format(
						x[0]), text='❌ Удалить ссылку'))
			bot.send_message(cid, text, reply_markup=markup)
		for x in y_links:
			text = 'Юла\n\n{!s}'.format(x[1])
			markup = types.InlineKeyboardMarkup()
			markup.add(
				types.InlineKeyboardButton(
					callback_data='delyola_{!s}'.format(
						x[0]), text='❌ Удалить ссылку'))
			bot.send_message(cid, text, reply_markup=markup)
		text = 'Всего ссылок для поиска объявлений: <b>{!s}</b>'.format(
			len(links))
		return bot.send_message(cid, text, parse_mode='HTML')
	elif message.text == '➕ Добавить ключевое слово':
		READY_TO_ADD_KEYWORD[uid] = {}
		text = 'Введите ключевое слово'
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, one_time_keyboard=False, row_width=1)
		markup.row('❌ Отмена')
		return bot.send_message(cid, text, reply_markup=markup)
	elif message.text == '👀 Посмотреть ключевые слова':
		keywords = DataBase.get_keywords()
		if len(keywords) == 0:
			text = 'Нет ни одного ключевого слова'
			return bot.send_message(cid, text)
		for x in keywords:
			text = 'Ключевое слово: {!s}'.format(x[1])
			markup = types.InlineKeyboardMarkup()
			markup.add(
				types.InlineKeyboardButton(
					callback_data='delkeyword_{!s}'.format(
						x[0]), text='❌ Удалить'))
			bot.send_message(cid, text, reply_markup=markup)
		text = 'Всего исключающих слов: <b>{!s}</b>'.format(len(keywords))
		return bot.send_message(cid, text, parse_mode='HTML')
	elif message.text == '➕ Добавить исключающее слово':
		READY_TO_ADD_NOTKEYWORD[uid] = {}
		text = 'Введите исключаюшее слово'
		markup = types.ReplyKeyboardMarkup(
			resize_keyboard=True, one_time_keyboard=False, row_width=1)
		markup.row('❌ Отмена')
		return bot.send_message(cid, text, reply_markup=markup)
	elif message.text == '👀 Посмотреть исключающие слова':
		keywords = DataBase.get_notkeywords()
		if len(keywords) == 0:
			text = 'Нет ни одного исключающего слова'
			return bot.send_message(cid, text)
		for x in keywords:
			text = 'Исключающее слово: {!s}'.format(x[1])
			markup = types.InlineKeyboardMarkup()
			markup.add(
				types.InlineKeyboardButton(
					callback_data='delnotkeyword_{!s}'.format(
						x[0]), text='❌ Удалить'))
			bot.send_message(cid, text, reply_markup=markup)
		text = 'Всего исключающих слов: <b>{!s}</b>'.format(len(keywords))
		return bot.send_message(cid, text, parse_mode='HTML')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	uid = call.from_user.id
	cid = call.message.chat.id

	print(call.data)

	try:
		bot.answer_callback_query(call.id, 'Выполнено')
	except Exception as e:
		print(e)

	# Обработать удаление ссылок
	if call.data.startswith('delavito'):
		link_id = int(call.data.split('_')[1])
		Avito.delete_search_link(link_id)
		return bot.edit_message_text(
			'Ссылка удалена', cid, call.message.message_id)
	elif call.data.startswith('delyola'):
		link_id = int(call.data.split('_')[1])
		Yola.delete_search_link(link_id)
		return bot.edit_message_text(
			'Ссылка удалена', cid, call.message.message_id)
	elif call.data.startswith('delkeyword'):
		word_id = int(call.data.split('_')[1])
		DataBase.delete_keyword(word_id)
		return bot.edit_message_text(
			'Ключевое слово удалено', cid, call.message.message_id)
	elif call.data.startswith('delnotkeyword'):
		word_id = int(call.data.split('_')[1])
		DataBase.delete_notkeyword(word_id)
		return bot.edit_message_text(
			'Исключающее слово удалено',
			cid,
			call.message.message_id)

	# Обработать отправку СМС
	if call.data.startswith('sendsms'):
		phone = call.data.split('_')[1]

		wa_number = '7{!s}@c.us'.format(phone[1:])
		sms_text = 'Здравствуйте! Готовы забрать Вашу технику сегодня в любое время.'
		dt = datetime.datetime.now()
		date_ = '{!s}.{!s}.{!s}'.format(dt.day, dt.month, dt.year)
		# Создать групповой чат WhatsApp
		res = wa_create_group({
			'groupName': 'Забрать технику {!s}'.format(date_),
			'chatIds': [config.ADMIN_WA_CHAT_ID],
		})
		print(res)
		group_id = res['chatId']

		# Добавить в чат админа
		res1 = wa_add_group({
			'groupId': group_id,
			'participantChatId': config.ADMIN_WA_CHAT_ID
		})
		print(res1)
		# Добавить в чат клиента
		res2 = wa_add_group({
			'groupId': group_id,
			'participantChatId': wa_number,
		})
		print(res2)
		# Отправить сообщение в группу
		res3 = wa_send_message({'chatId': group_id, 'body': sms_text})
		print(res3)
		new_text = '{!s}\n\nСМС отправлено'.format(call.message.text)
		return bot.edit_message_text(new_text, chat_id=cid, message_id=call.message.message_id, reply_markup=None)


def run_monitoring():
	"""
	Запустить мониторинг объявлений
	"""
	while True:
		try:
			monitor_avito(bot)
			monitor_yola(bot)
			if config.WINDOWS == False:
				os.system('sudo cp -rf database.db /var/www/html/files/')
		except Exception as e:
			print(e)
			raise e
			continue
			pass
		finally:
			time.sleep(config.SLEEP_TIME)


def run_bot():
	"""
	Запустить бота
	"""
	while True:
		try:
			bot.polling(none_stop=True, interval=0)
		except Exception as e:
			print(e)
			time.sleep(30)
			continue


def main():
	#th1 = threading.Thread(target=run_monitoring)
	th2 = threading.Thread(target=run_bot)
	#th1.start()
	th2.start()
	#th1.join()
	th2.join()
	#while True:
	#	try:
	#		if th1.isAlive() == False:
	#			th1 = threading.Thread(target=run_monitoring)
	#			th1.start()
	#			th1.join()
	#		time.sleep(3)
	#	except Exception as e:
	#		print(e)
	#		continue


if __name__ == '__main__':
	#main()
	run_bot()
