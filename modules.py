from avito_module import *
from yola_module import *
import config
import time


while True:
	try:
		monitor_avito()
		monitor_yola()
		if config.WINDOWS == False:
			os.system('sudo cp -rf database.db /var/www/html/files/')
		time.sleep(config.SLEEP_TIME)
	except Exception as e:
		print(e)
		pass
	
