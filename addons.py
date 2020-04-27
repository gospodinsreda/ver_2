import requests
import config


def wa_send_message(params):
	"""
	Выполнить запрос к WhatsApp API
	"""
	url = '{!s}/sendMessage'.format(config.WA_REQUEST_URL)
	params['token'] = config.WA_BOT_TOKEN
	res = requests.post(url, params=params)
	return res.json()


def wa_create_group(params):
	"""
	Выполнить запрос к WhatsApp API
	"""
	url = '{!s}/group'.format(config.WA_REQUEST_URL)
	params['token'] = config.WA_BOT_TOKEN
	res = requests.post(url, params=params)
	return res.json()


def wa_add_group(params):
	"""
	Выполнить запрос к WhatsApp API
	"""
	url = '{!s}/addGroupParticipant'.format(config.WA_REQUEST_URL)
	params['token'] = config.WA_BOT_TOKEN
	res = requests.post(url, params=params)
	return res.json()
